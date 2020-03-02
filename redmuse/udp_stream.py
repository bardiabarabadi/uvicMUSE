from functools import partial
from time import time, sleep
import socket
from pylsl import StreamInfo, StreamOutlet
import struct
# from constants import AUTO_DISCONNECT_DELAY, \
#     MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, LSL_EEG_CHUNK, \
#     MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE, LSL_PPG_CHUNK, \
#     MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE, LSL_ACC_CHUNK, \
#     MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE, LSL_GYRO_CHUNK
# from muse import Muse
# from stream import find_muse
from .constants import AUTO_DISCONNECT_DELAY, \
    MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, LSL_EEG_CHUNK, \
    MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE, LSL_PPG_CHUNK, \
    MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE, LSL_ACC_CHUNK, \
    MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE, LSL_GYRO_CHUNK
from .muse import Muse
from .stream import find_muse

prv_ts = 0


def isDataValid(data, timestamps):
    if timestamps == 0.0:
        return False

    for i in range(data.shape[0]-1):
        if data[i] == 0.0:
            return False
    return True


# Begins UPD stream(s) from a Muse with a given address with data sources determined by arguments
def udp_stream(address, backend='bgapi', udp_ip='localhost', name=None, ppg_enabled=False, acc_enabled=False,
               gyro_enabled=False, eeg_disabled=False, udp_port=102, ):
    if not address:
        found_muse = find_muse(name)
        if not found_muse:
            return
        else:
            address = found_muse['address']
            name = found_muse['name']

    if not eeg_disabled:
        eeg_info = StreamInfo('Muse', 'EEG', MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, 'float32',
                              'Muse%s' % address)
        eeg_info.desc().append_child_value("manufacturer", "Muse")
        eeg_channels = eeg_info.desc().append_child("channels")

        for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
            eeg_channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "EEG")

        eeg_outlet = StreamOutlet(eeg_info, 1)

    if ppg_enabled:
        ppg_info = StreamInfo('Muse', 'PPG', MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE,
                              'float32', 'Muse%s' % address)
        ppg_info.desc().append_child_value("manufacturer", "Muse")
        ppg_channels = ppg_info.desc().append_child("channels")

        for c in ['PPG1', 'PPG2', 'PPG3']:
            ppg_channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "mmHg") \
                .append_child_value("type", "PPG")

        ppg_outlet = StreamOutlet(ppg_info, LSL_PPG_CHUNK)

    if acc_enabled:
        acc_info = StreamInfo('Muse', 'ACC', MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE,
                              'float32', 'Muse%s' % address)
        acc_info.desc().append_child_value("manufacturer", "Muse")
        acc_channels = acc_info.desc().append_child("channels")

        for c in ['X', 'Y', 'Z']:
            acc_channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "g") \
                .append_child_value("type", "accelerometer")

        acc_outlet = StreamOutlet(acc_info, LSL_ACC_CHUNK)

    if gyro_enabled:
        gyro_info = StreamInfo('Muse', 'GYRO', MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE,
                               'float32', 'Muse%s' % address)
        gyro_info.desc().append_child_value("manufacturer", "Muse")
        gyro_channels = gyro_info.desc().append_child("channels")

        for c in ['X', 'Y', 'Z']:
            gyro_channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "dps") \
                .append_child_value("type", "gyroscope")

        gyro_outlet = StreamOutlet(gyro_info, LSL_GYRO_CHUNK)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def push(data, timestamps, outlet, address=('localhost',101)):

        global prv_ts
        for ii in range(data.shape[1]):
            
            MSG = struct.pack('ffffff', data[0, ii],
                              data[1, ii], data[2, ii], data[3, ii], data[4, ii], 100 * (timestamps[ii] - prv_ts))

            prv_ts = timestamps[ii]

            #print(data[0, ii],
            #                  data[1, ii], data[2, ii], data[3, ii], data[4, ii], timestamps[ii])
            #print(data.shape)
            if not isDataValid(data[:, ii], timestamps[ii]):
                continue
            outlet.sendto(MSG, address)  # TODO: Replace with TCP/UDP send
            # outlet.push_sample(data[:, ii], timestamps[ii])

    push_eeg = partial(push, outlet=sock, address=(udp_ip, udp_port)) if not eeg_disabled else None
    push_ppg = partial(push, outlet=sock, address=(udp_ip, udp_port)) if ppg_enabled else None
    push_acc = partial(push, outlet=sock, address=(udp_ip, udp_port)) if acc_enabled else None
    push_gyro = partial(push, outlet=sock, address=(udp_ip, udp_port)) if gyro_enabled else None

    if all(f is None for f in [push_eeg, push_ppg, push_acc, push_gyro]):
        print('Stream initiation failed: At least one data source must be enabled.')
        return

    muse = Muse(address=address, callback_eeg=push_eeg, callback_ppg=push_ppg, callback_acc=push_acc,
                callback_gyro=push_gyro,
                backend=backend, interface=None, name=name)

    did_connect = muse.connect()

    if did_connect:
        print('Connected.')
        muse.start()

        eeg_string = " EEG" if not eeg_disabled else ""
        ppg_string = " PPG" if ppg_enabled else ""
        acc_string = " ACC" if acc_enabled else ""
        gyro_string = " GYRO" if gyro_enabled else ""

        print("Streaming%s%s%s%s..." %
              (eeg_string, ppg_string, acc_string, gyro_string))

        while time() - muse.last_timestamp < AUTO_DISCONNECT_DELAY:
            try:
                sleep(1)
            except KeyboardInterrupt:
                muse.stop()
                muse.disconnect()
                sock.close()
                break

        print('Disconnected.')
