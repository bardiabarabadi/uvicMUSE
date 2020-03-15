from constants import *
from helper import *

# from .constants import *
# from .helper import *


import pygatt


class Backend:

    def __init__(self, muse_backend='bgapi'):
        self.muses = []
        self.muse = None
        self.is_muse_connected = False

        self.use_lsl = False

        self.udp_port = 0
        self.udp_address = ''
        self.is_udp_streaming = False

        self.current_muse_id = None
        self.use_EEG = False
        self.use_PPG = False
        self.use_ACC = False
        self.use_gyro = False

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
            return ["No BLE Module Found..."], succeed

        succeed = True
        to_return = []
        for i in range(len(self.muses)):
            to_return.append('[' + str(i) + ']: Name=' + self.muses[i]['name'] + ', Address=' +
                             self.muses[i]['address'])
        return to_return, succeed

    def connect_btn_callback(self, current_muse_id):
        self.current_muse_id = current_muse_id
        # TODO: Not Implemented
        return

    def disconnect_btn_callback(self):  # TODO: Not Implemented
        return  # No return

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
