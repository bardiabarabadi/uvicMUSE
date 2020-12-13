from uvicmuse.constants import *
from uvicmuse.MuseBLE import *
from uvicmuse.MuseFinder import *
from uvicmuse.helper import *

import asyncio
from functools import partial


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

    def disconnect(self):
        self.loop.run_until_complete(self.muse.disconnect())

    def search_and_connect(self):
        mf = MuseFinder(add_muse_to_list_callback=None)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(mf.search_for_muses(timeout=self.timeout))
        self.all_muses = mf.get_muses()

        success = False

        if len(self.all_muses) < 1:
            print("No MUSEs found, please try again or increase the timeout")
            return success

        if self.target_name is None:
            if len(self.all_muses) == 1:
                print("No target MUSE specified, one device found. Connecting to " + str(self.all_muses[0].name))
                self.target_muse = self.all_muses[0]
            else:
                print("No target MUSE specified, more than one MUSE is in range. Please specify the target.")
                return success

        else:
            found = False
            for d in self.all_muses:
                if self.target_name in d.name:
                    print("Target MUSE-" + self.target_name + " found. Attempting to connect...")
                    self.target_muse = d
                    found = True
            if found is False:
                print("Couldn't find target, + " + str(self.target_name) + ". Please specify the target.")
                return False

        # Connecting
        push_eeg = partial(self._push, offset=EEG_PORT_OFFSET)
        push_ppg = partial(self._push, offset=PPG_PORT_OFFSET)
        push_acc = partial(self._push, offset=ACC_PORT_OFFSET)
        push_gyro = partial(self._push, offset=GYRO_PORT_OFFSET)
        self.muse = MuseBLE(client=self.target_muse, callback_control=self._command_callback,
                            callback_acc=push_acc, callback_eeg=push_eeg, callback_gyro=push_gyro,
                            callback_ppg=push_ppg)

        loop.run_until_complete(self.muse.connect(timeout=30))

        print("connection was successful")
        asyncio.run(asyncio.sleep(2))
        success = True
        return success

    def pull_eeg(self):
        self.loop.run_until_complete(self.muse.start())
        to_return = self.eeg_buff
        self.eeg_buff = []
        return to_return

    def pull_ppg(self):
        self.loop.run_until_complete(self.muse.start())
        to_return = self.ppg_buff
        self.ppg_buff = []
        return to_return

    def pull_acc(self):
        self.loop.run_until_complete(self.muse.start())
        to_return = self.acc_buff
        self.acc_buff = []
        return to_return

    def pull_gyro(self):
        self.loop.run_until_complete(self.muse.start())
        to_return = self.gyro_buff
        self.gyro_buff = []
        return to_return

    def reset_buffers(self):
        self.eeg_buff = []
        self.ppg_buff = []
        self.acc_buff = []
        self.gyro_buff = []

    def _push(self, data, timestamps, offset=0):
        for ii in range(data.shape[1]):
            if not is_data_valid(data[:, ii], timestamps[ii]):
                continue
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
