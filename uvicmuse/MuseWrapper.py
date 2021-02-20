from uvicmuse.constants import *
from uvicmuse.muse import *
from uvicmuse.helper import *
import pygatt
import asyncio
from functools import partial
from pylsl import StreamInfo, StreamOutlet


class MuseWrapper:

    def __init__(self,
                 loop,
                 target_name=None,  # Should be a string containing four digits/letters
                 timeout=10,
                 max_buff_len=2 * 256  # Set this to be the maximum number of samples to keep
                 ):
        self.all_muses = []
        self.target_name = target_name
        self.timeout = timeout
        self.muse = None
        self.target_muse = None

        self.eeg_buff = []
        self.ppg_buff = []
        self.acc_buff = []
        self.gyro_buff = []
        self.max_buff_len = max_buff_len
        self.loop = loop

        if platform.system() != 'Linux':
            self.interface = None
        else:
            if os.path.exists("/dev/ttyACM0"):
                self.interface = "/dev/ttyACM0"
            else:
                self.interface = "/dev/ttyACM1"

    def disconnect(self):
        self.muse.stop()
        self.muse.disconnect()

    def search_and_connect(self):
        self.all_muses = list_muses(interface=self.interface)
        success = False

        if len(self.all_muses) < 1:
            print("No MUSEs found, please try again or increase the timeout")
            return success

        if self.target_name is None:
            if len(self.all_muses) == 1:
                self.target_muse = self.all_muses[0]
                print("No target MUSE specified, one device found. Connecting to " + str(self.get_muse_name()))
            else:
                print("No target MUSE specified, more than one MUSE is in range. Please specify the target.")
                return success

        else:
            found = False
            for d in self.all_muses:
                if self.target_name in d['name']:
                    print("Target MUSE-" + self.target_name + " found. Attempting to connect...")
                    self.target_muse = d
                    found = True
            if found is False:
                print("Target MUSE NOT found, please try again or increase the timeout")
                return False

        # Connecting

        eeg_outlet = self._get_eeg_outlet()
        ppg_outlet = self._get_ppg_outlet()
        acc_outlet = self._get_acc_outlet()
        gyro_outlet = self._get_gyro_outlet()

        push_eeg = partial(self._push, outlet=eeg_outlet, offset=EEG_PORT_OFFSET)
        push_ppg = partial(self._push, outlet=ppg_outlet, offset=PPG_PORT_OFFSET)
        push_acc = partial(self._push, outlet=acc_outlet, offset=ACC_PORT_OFFSET)
        push_gyro = partial(self._push, outlet=gyro_outlet, offset=GYRO_PORT_OFFSET)
        self.muse = Muse(address=self.get_muse_address(), callback_control=self._command_callback,
                         callback_acc=push_acc, callback_eeg=push_eeg, callback_gyro=push_gyro,
                         callback_ppg=push_ppg)

        try:
            success = self.muse.connect()
        except pygatt.exceptions.BLEError:
            self.muse = Muse(address=self.get_muse_address(), callback_control=self._command_callback,
                             callback_acc=push_acc, callback_eeg=push_eeg, callback_gyro=push_gyro,
                             callback_ppg=None)
            success = self.muse.connect()

        self.muse.start()
        return success

    def pull_eeg(self):
        # self.loop.run_until_complete(self.muse.start())
        to_return = self.eeg_buff
        self.eeg_buff = []
        return to_return

    def pull_ppg(self):
        # self.loop.run_until_complete(self.muse.start())
        to_return = self.ppg_buff
        self.ppg_buff = []
        return to_return

    def pull_acc(self):
        # self.loop.run_until_complete(self.muse.start())
        to_return = self.acc_buff
        self.acc_buff = []
        return to_return

    def pull_gyro(self):
        # self.loop.run_until_complete(self.muse.start())
        to_return = self.gyro_buff
        self.gyro_buff = []
        return to_return

    def reset_buffers(self):
        self.eeg_buff = []
        self.ppg_buff = []
        self.acc_buff = []
        self.gyro_buff = []

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
            if not is_data_valid(data[:, ii], timestamps[ii]):
                continue
            outlet.push_sample(data[:, ii], timestamps[ii])
            if offset == EEG_PORT_OFFSET:
                to_append_eeg_data = [data[0, ii], data[1, ii], data[2, ii], data[3, ii], data[4, ii],
                                      (timestamps[ii])]
                if len(self.eeg_buff) >= self.max_buff_len:
                    self.eeg_buff.pop(0)
                self.eeg_buff.append(to_append_eeg_data)

            elif offset == PPG_PORT_OFFSET:
                to_append_ppg_data = [data[0, ii], data[1, ii], data[2, ii],
                                      (timestamps[ii])]
                if len(self.ppg_buff) >= self.max_buff_len:
                    self.ppg_buff.pop(0)
                self.ppg_buff.append(to_append_ppg_data)

            elif offset == ACC_PORT_OFFSET:
                to_append_acc_data = [data[0, ii], data[1, ii], data[2, ii],
                                      (timestamps[ii])]
                if len(self.acc_buff) >= self.max_buff_len:
                    self.acc_buff.pop(0)
                self.acc_buff.append(to_append_acc_data)

            elif offset == GYRO_PORT_OFFSET:
                to_append_gyro_data = [data[0, ii], data[1, ii], data[2, ii],
                                       (timestamps[ii])]
                if len(self.gyro_buff) >= self.max_buff_len:
                    self.gyro_buff.pop(0)
                self.gyro_buff.append(to_append_gyro_data)

    @staticmethod
    def _command_callback(a):
        pass
        # print("Received command callback: ")
        # print(a)

    def get_muse_name(self):
        return self.target_muse['name']

    def get_muse_address(self):
        return self.target_muse['address']
