from uvicmuse.constants import *
from uvicmuse.helper import *
from uvicmuse.MuseBLE import MuseBLE as muse
from uvicmuse.MuseFinder import MuseFinder
# from .constants import *
# from .helper import *
# from .MuseBLE import MuseBLE as muse
# from .MuseFinder import MuseFinder

from functools import partial
import socket
import struct
import os
from pylsl import StreamInfo, StreamOutlet
import platform
import asyncio
from scipy import signal


class Backend:

    def __init__(self):  # TODO: Different protocols need different port sfor udp
        # Solution: Get a 'base' udp port and build all on top of that
        # Reflect on the matlab function
        self.notch_a = None
        self.notch_b = None
        self.notch_z = None
        self.notch_fs = 60
        self.fs = 256
        self.muses = []
        self.muse = None
        self.muse_obj = None
        self.is_muse_connected = False

        self.use_lsl = True

        self.udp_port = 0
        self.udp_address = '127.0.0.1'
        self.is_udp_streaming = False
        self.socket = None

        self.use_low_pass = False
        self.use_high_pass = False
        self.use_notch = False
        self.low_pass_cutoff = 0.1
        self.high_pass_cutoff = 30.0
        self.filter_a = None
        self.filter_b = None
        self.filter_z = None

        if platform.system() != 'Linux':
            self.interface = None
        else:
            if os.path.exists("/dev/ttyACM0"):
                self.interface = "/dev/ttyACM0"
            else:
                self.interface = "/dev/ttyACM1"

    # + MUSE interface functions

    def refresh_btn_callback(self, event):
        succeed = False
        mf = MuseFinder(add_muse_to_list_callback=self.muses.append)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(mf.search_for_muses(timeout=10))

        self.muses = mf.get_muses()
        return self.muses, True

    def connect_btn_callback(self, current_muse_id):
        error_msg = ''
        self.muse = self.muses[current_muse_id]

        eeg_outlet = self._get_eeg_outlet()
        ppg_outlet = self._get_ppg_outlet()
        acc_outlet = self._get_acc_outlet()
        gyro_outlet = self._get_gyro_outlet()

        push_eeg = partial(self._push, outlet=eeg_outlet, offset=EEG_PORT_OFFSET)
        push_ppg = partial(self._push, outlet=ppg_outlet, offset=PPG_PORT_OFFSET)
        push_acc = partial(self._push, outlet=acc_outlet, offset=ACC_PORT_OFFSET)
        push_gyro = partial(self._push, outlet=gyro_outlet, offset=GYRO_PORT_OFFSET)

        self.muse_obj = muse(client=self.muse, callback_eeg=push_eeg,
                             callback_ppg=push_ppg, callback_acc=push_acc,
                             callback_gyro=push_gyro, callback_control=self.command_callback)

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.muse_obj.connect())
            self.is_muse_connected = True
        except muse.PPG_error:
            error_msg = 'MSUE2 is needed for PPG'

        return self.is_muse_connected, error_msg

    def disconnect_btn_callback(self):
        if not self.is_muse_connected:
            return False
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.muse_obj.disconnect())
            self.is_muse_connected = False
            self.muse_obj = None
            return True

    # - MUSE interface functions

    # + UDP interface functions
    def udp_stream_btn_callback(self, use_low_pass, use_high_pass, low_pass_cutoff,
                                high_pass_cutoff, use_notch):
        self.udp_port = 1963
        self.udp_address = '127.0.0.1'
        self.is_udp_streaming = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.use_low_pass = use_low_pass
        self.use_high_pass = use_high_pass
        self.use_notch = use_notch

        self.low_pass_cutoff = low_pass_cutoff / (0.5 * self.fs)
        self.high_pass_cutoff = high_pass_cutoff / (0.5 * self.fs)

        if self.use_low_pass and self.use_high_pass:
            cutoffs = [self.high_pass_cutoff, self.low_pass_cutoff]
            btype = 'band'
        elif self.use_low_pass:
            cutoffs = self.low_pass_cutoff
            btype = 'lowpass'
        elif self.use_high_pass:
            cutoffs = self.high_pass_cutoff
            btype = 'highpass'
        else:
            cutoffs = 0.5
            btype = 'low'

        self.filter_b, self.filter_a = signal.butter(N=3, Wn=cutoffs, btype=btype, output='ba')
        self.filter_z = signal.lfilter_zi(self.filter_b, self.filter_a)

        self.notch_b, self.notch_a = signal.iirnotch(w0=self.notch_fs * 2 / self.fs, Q=20, fs=self.fs)
        self.notch_z = signal.lfilter_zi(self.notch_b, self.notch_a)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.muse_obj.start())

        return

    def udp_stop_btn_callback(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.muse_obj.stop())
        self.udp_port = 0
        self.udp_address = '127.0.0.1'
        self.is_udp_streaming = False
        self.socket = None
        return

    # - UDP interface functions

    # + Status functions
    def is_connected(self):
        return self.is_muse_connected

    def is_udp_streaming(self):
        return self.is_udp_streaming

    # - Status functions

    def get_muse_name(self):
        return self.muse.name

    def get_muse_address(self):
        return self.muse.address

    def get_muse(self):
        return self.muse

    def _get_eeg_outlet(self):
        # Connecting to MUSE
        eeg_info = StreamInfo('Muse', 'EEG', MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, 'float32',
                              'Muse%s' % self.get_muse_address())
        eeg_info.desc().append_child_value("manufacturer", "Muse")
        eeg_channels = eeg_info.desc().append_child("channels")

        for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
            eeg_channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "EEG")

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

    def _push(self, data, timestamps, outlet, offset=0):
        for ii in range(data.shape[1]):
            if self.use_lsl:
                outlet.push_sample(data[:, ii], timestamps[ii])

            if self.use_low_pass or self.use_high_pass and offset == EEG_PORT_OFFSET:
                for i in range(data.shape[0]):
                    data[i, ii], self.filter_z = signal.lfilter(self.filter_b, self.filter_a, [data[i, ii]],
                                                                zi=self.filter_z)

            if self.use_notch and offset == EEG_PORT_OFFSET:
                for i in range(data.shape[0]):
                    data[i, ii], self.notch_z = signal.lfilter(self.notch_b, self.notch_a, [data[i, ii]],
                                                               zi=self.notch_z)

            if self.is_udp_streaming:

                if offset == EEG_PORT_OFFSET:
                    udp_msg = struct.pack('ffffff', data[0, ii],
                                          data[1, ii], data[2, ii], data[3, ii], data[4, ii],
                                          (timestamps[ii]))
                    if not is_data_valid(data[:, ii], timestamps[ii]):
                        continue
                    self.socket.sendto(udp_msg, (self.udp_address, self.udp_port + offset))

                else:  # ppg or acc or gyro
                    udp_msg = struct.pack('ffff', data[0, ii],
                                          data[1, ii], data[2, ii],
                                          (timestamps[ii]))
                    if not is_data_valid(data[:, ii], timestamps[ii]):
                        continue
                    self.socket.sendto(udp_msg, (self.udp_address, self.udp_port + offset))

    def command_callback(self, a):
        print("Received command callback completely: ")
        print(a)
