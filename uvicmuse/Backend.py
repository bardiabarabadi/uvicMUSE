from uvicmuse.constants import *
from uvicmuse.helper import *
from functools import partial
from uvicmuse.muse import Muse
import socket
import struct
import pygatt
from pylsl import StreamInfo, StreamOutlet


class Backend:

    def __init__(self, muse_backend='bgapi'):
        self.muses = []
        self.muse = None
        self.is_muse_connected = False
        self.muse_backend = muse_backend

        self.use_lsl = False

        self.udp_port = 0
        self.udp_address = ''
        self.is_udp_streaming = False
        self.socket = False

        self.use_low_pass = False
        self.use_high_pass = False
        self.low_pass_cutoff = 0.1
        self.high_pass_cutoff = 30.0

    # + MUSE interface functions
    def refresh_btn_callback(self):
        succeed = False
        try:
            self.muses = list_muses()
        except pygatt.exceptions.BLEError:
            return ["No BLE Module Found."], succeed

        succeed = True
        to_return = []
        for i in range(len(self.muses)):
            to_return.append('[' + str(i) + ']: Name=' + self.muses[i]['name'] + ', Address=' +
                             self.muses[i]['address'])
        return to_return, succeed

    def connect_btn_callback(self, current_muse_id, use_EEG,
                             use_PPG, use_ACC, use_gyro):

        self.muse = self.muses[current_muse_id]

        eeg_outlet = self._get_eeg_outlet()
        ppg_outlet = self._get_ppg_outlet()
        acc_outlet = self._get_acc_outlet()
        gyro_outlet = self._get_gyro_outlet()

        push_eeg = partial(self._push, outlet=eeg_outlet) if use_EEG else None
        push_ppg = partial(self._push, outlet=ppg_outlet) if use_PPG else None
        push_acc = partial(self._push, outlet=acc_outlet) if use_ACC else None
        push_gyro = partial(self._push, outlet=gyro_outlet) if use_gyro else None

        self.muse = Muse(address=self.get_muse_address(), callback_eeg=push_eeg,
                         callback_ppg=push_ppg, callback_acc=push_acc,
                         callback_gyro=push_gyro, backend=self.muse_backend,
                         interface="/dev/ttyACM0", name=self.get_muse_name())

        self.is_muse_connected = self.muse.connect()

        return self.is_muse_connected

    def disconnect_btn_callback(self):
        if not self.is_muse_connected:
            return False
        else:
            self.muse.stop()
            self.muse.disconnect()
            self.is_muse_connected = False
            self.muse = None
            return True

    # - MUSE interface functions

    # + UDP interface functions
    def udp_stream_btn_callback(self, udp_port, udp_address):
        self.udp_port = udp_port
        self.udp_address = udp_address
        self.is_udp_streaming = True
        return

    def udp_stop_btn_callback(self):
        self.udp_port = 0
        self.udp_address = ''
        self.is_udp_streaming = False
        return

    # - UDP interface functions

    # + Status functions
    def is_connected(self):
        return self.is_muse_connected

    def is_udp_streaming(self):
        return self.is_udp_streaming

    # - Status functions

    def get_muse_name(self):
        return self.muse['name']

    def get_muse_address(self):
        return self.muse['address']

    def _get_eeg_outlet(self):
        # Connecting to MUSE
        eeg_info = StreamInfo('Muse', 'EEG', MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, 'float32',
                              'Muse%s' % self.get_muse_address())
        eeg_info.desc().append_child_value("manufacturer", "Muse")

        eeg_outlet = StreamOutlet(eeg_info, LSL_EEG_CHUNK)

        return eeg_outlet

    def _get_ppg_outlet(self):
        # Connecting to MUSE
        ppg_info = StreamInfo('Muse', 'PPG', MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE,
                              'float32', 'Muse%s' % self.get_muse_address())
        ppg_info.desc().append_child_value("manufacturer", "Muse")

        ppg_outlet = StreamOutlet(ppg_info, LSL_PPG_CHUNK)

        return ppg_outlet

    def _get_acc_outlet(self):
        acc_info = StreamInfo('Muse', 'ACC', MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE,
                              'float32', 'Muse%s' % self.get_muse_address())
        acc_info.desc().append_child_value("manufacturer", "Muse")

        acc_outlet = StreamOutlet(acc_info, LSL_ACC_CHUNK)

        return acc_outlet

    def _get_gyro_outlet(self):
        gyro_info = StreamInfo('Muse', 'GYRO', MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE,
                               'float32', 'Muse%s' % self.get_muse_address())
        gyro_info.desc().append_child_value("manufacturer", "Muse")

        gyro_outlet = StreamOutlet(gyro_info, LSL_GYRO_CHUNK)

        return gyro_outlet

    def _push(self, data, timestamps, outlet):
        for ii in range(data.shape[1]):
            if self.use_lsl:
                outlet.push_sample(data[:, ii], timestamps[ii])

            if self.is_udp_streaming:

                udp_msg = struct.pack('ffffff', data[0, ii],
                                      data[1, ii], data[2, ii], data[3, ii], data[4, ii],
                                      100 * (timestamps[ii] - self.prv_ts))

                self.prv_ts = timestamps[ii]
                if not is_data_valid(data[:, ii], timestamps[ii]):
                    continue

                self.socket.sendto(udp_msg, self.udp_address)
