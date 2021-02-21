# from .constants import *
from uvicmuse.constants import *

import bitstring
from bleak import BleakClient
import json
from bleak.exc import BleakError
import numpy as np
from time import time
import asyncio
from kivy.logger import Logger


def ppg_error():
    print("PPG is only available on MUSE v2")
    # T0D0: a proper error routine


class MuseBLE(object):

    def __init__(self, client,
                 callback_control=None,  # Will be called with a dictionary containing control info
                 callback_eeg=None,
                 callback_ppg=None,
                 callback_acc=None,
                 callback_gyro=None,
                 callback_tele=None
                 ):

        self.loop = asyncio.new_event_loop()
        self.client = BleakClient(client.address, loop=self.loop)

        self.last_tm_ppg = 0
        self.last_tm_eeg = 0
        self.callback_control = callback_control
        self.callback_eeg = callback_eeg
        self.callback_ppg = callback_ppg
        self.callback_acc = callback_acc
        self.callback_gyro = callback_gyro
        self.callback_tele = callback_tele

        self._current_control_seq = ""

    async def connect(self, timeout=20):
        # Tries to connect to the given MUSE (given the address in the constructor), Returns success

        success = False
        for retry in range(int(timeout / 4) + 1):
            try:
                await self.client.connect(timeout=timeout)
                success = True
            except BleakError:
                success = False
            if success:
                break
        if not success:
            return False
        if self.callback_control is not None:
            await self._subscribe_control()
        if self.callback_eeg is not None:
            await self._subscribe_eeg()
        if self.callback_ppg is not None and len(self.client.services.characteristics) > 12:
            await self._subscribe_ppg()
        if self.callback_acc is not None:
            await self._subscribe_acc()
        if self.callback_tele is not None:
            await self._subscribe_telemetry()
        if self.callback_gyro is not None:
            await self._subscribe_gyro()

        return True

    def disconnect_(self):
        self.loop.run_until_complete(self.disconnect())

    async def disconnect(self):
        # Disconnects from the MUSE, returns success
        try:
            await self.client.disconnect()
            success = True
        except BleakError:
            success = False
        return success

    async def ask_control(self):
        """Send a message to Muse to ask for the control status.
                The message received is a dict with the following keys:
                "hn": device name
                "sn": serial number
                "ma": MAC address
                "id":
                "bp": battery percentage
                "ts":
                "ps": preset selected
                "rc": return status, if 0 is OK
        """
        await self._write_command([0x02, 0x73, 0x0a])

    async def ask_device_info(self):
        """Send a message to Muse to ask for the device info.
                The message received is a dict with the following keys:
                "ap":
                "sp":
                "tp": firmware type, e.g: "consumer"
                "hw": hardware version?
                "bn": build number?
                "fw": firmware version?
                "bl":
                "pv": protocol version?
                "rc": return status, if 0 is OK
        """
        await self._write_command([0x03, 0x76, 0x31, 0x0a])

    async def ask_reset(self):
        # The message received would be {"rc": return status}, 0 is OK
        await self._write_command([0x03, 0x2a, 0x31, 0x0a])

    async def start(self):
        self._init_timestamp_correction()
        self._init_sample_eeg()
        self._init_sample_ppg()
        self._init_sample_control()
        self.last_tm_eeg = 0
        self.last_tm_ppg = 0
        await self.resume()

    async def resume(self):
        await self._write_command([0x02, 0x64, 0x0a])

    async def stop(self):
        await self._write_command([0x02, 0x68, 0x0a])

    async def keep_alive(self):
        await self._write_command([0x02, 0x6b, 0x0a])

    async def select_preset(self, preset):
        # Setting preset for headband configuration
        if preset == 20:
            await self._write_command([0x04, 0x70, 0x32, 0x30, 0x0a])
        elif preset == 22:
            await self._write_command([0x04, 0x70, 0x32, 0x32, 0x0a])
        elif preset == 23:
            await self._write_command([0x04, 0x70, 0x32, 0x33, 0x0a])
        else:
            await self._write_command([0x04, 0x70, 0x32, 0x31, 0x0a])

    async def _subscribe_to_uuid(self, uuid, callback):
        await self.client.start_notify(uuid, callback)

    async def _write_command(self, command):
        await self.client.write_gatt_char(MUSE_CONTROL_HANDLE, bytearray(command), False)

    # _subscribe functions

    async def _subscribe_control(self):
        await self._subscribe_to_uuid(MUSE_CONTROL_HANDLE, self._handle_control)

    async def _subscribe_eeg(self):
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_TP9, callback=self._handle_eeg)
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_AF7, callback=self._handle_eeg)
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_AF8, callback=self._handle_eeg)
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_TP10, callback=self._handle_eeg)
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_RIGHTAUX, callback=self._handle_eeg)

    async def _subscribe_ppg(self):
        try:
            await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_PPG1, callback=self._handle_ppg)
            await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_PPG2, callback=self._handle_ppg)
            await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_PPG3, callback=self._handle_ppg)
        except BleakError:
            raise ppg_error

    async def _subscribe_gyro(self):
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_GYRO, callback=self._handle_gyro)

    async def _subscribe_acc(self):
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_ACCELEROMETER, callback=self._handle_acc)

    async def _subscribe_telemetry(self):
        # Handles telemetry (Battery, temp, ...) incoming data
        await self._subscribe_to_uuid(uuid=MUSE_GATT_ATTR_TELEMETRY, callback=self._handle_tele)

    # Unpack functions
    @staticmethod
    def _unpack_eeg_channel(packet):
        # Each packet is encoded with a 16bit timestamp followed by 12 time samples with a 12 bit resolution.
        aa = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:12,uint:12,uint:12,uint:12,uint:12,uint:12, \
                          uint:12,uint:12,uint:12,uint:12,uint:12,uint:12"
        res = aa.unpack(pattern)
        packet_index = res[0]
        data = res[1:]
        # 12 bits on a 2 mVpp range
        data = 0.48828125 * (np.array(data) - 2048)
        return packet_index, data

    @staticmethod
    def _unpack_ppg_channel(packet):
        """Decode data packet of one PPG channel.
        Each packet is encoded with a 16bit timestamp followed by 3
        samples with an x bit resolution.
        """

        aa = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:24,uint:24,uint:24,uint:24,uint:24,uint:24"
        res = aa.unpack(pattern)
        packet_index = res[0]
        data = res[1:]

        return packet_index, data

    @staticmethod
    def _unpack_imu_channel(packet, scale=1):
        """Decode data packet of the accelerometer and gyro (imu) channels.
                Each packet is encoded with a 16bit timestamp followed by 9 samples
                with a 16 bit resolution.
                """
        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:16,int:16,int:16,int:16,int:16, \
                           int:16,int:16,int:16,int:16,int:16"
        data = bit_decoder.unpack(pattern)

        packet_index = data[0]

        samples = np.array(data[1:]).reshape((3, 3), order='F') * scale

        return packet_index, samples

    # Initialize samples

    def _init_sample_control(self):
        self._current_control_seq = ""

    def _init_sample_eeg(self):
        self.timestamps_eeg = np.zeros(5)
        self.data_eeg = np.ones((5, 12))

    def _init_sample_ppg(self):
        self.timestamps_ppg = np.zeros(3)
        self.data_ppg = np.zeros((3, 6))

    # Timestamp Correction
    def _init_timestamp_correction(self):
        """Init IRLS params"""
        # initial params for the timestamp correction
        # the time it started + the inverse of sampling rate
        self.sample_index_eeg = 0
        self.sample_index_ppg = 0
        self.reg_params = np.array(
            [time(), 1. / MUSE_SAMPLING_EEG_RATE])
        self.reg_ppg_sample_rate = np.array(
            [time(), 1. / MUSE_SAMPLING_PPG_RATE])

    # Handlers
    def _handle_control(self, sender, packet):
        # Handles the message coming from the control sequence
        assert sender == 13, "_handle_control is receiving a message " \
                             "with a different UUID " + str(sender)

        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8, \
                                uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8"
        chars = bit_decoder.unpack(pattern)

        # Length of the string
        n_incoming = chars[0]

        # Parse as chars, only useful bytes
        incoming_message = "".join(map(chr, chars[1:]))[:n_incoming]

        self._current_control_seq += incoming_message

        if incoming_message[-1] == '}':  # end of the current message
            self.callback_control(json.loads(self._current_control_seq))  # Call the callback
            self._init_sample_control()

    def _handle_eeg(self, sender, packet):
        index = int((sender - 31) / 3)
        timestamp = time()
        tm, d = self._unpack_eeg_channel(packet)
        # Logger.info('this is what eeg received: ' + str(sender) + 'data: ' + str(d))
        if self.last_tm_eeg == 0:
            self.last_tm_eeg = tm - 1

        self.data_eeg[index] = d
        self.timestamps_eeg[index] = timestamp

        # Check if this is the last data in the sequence
        if sender == 34:
            if tm != self.last_tm_eeg + 1:
                pass
                # print("Missing sample %d : %d" % (tm, self.last_tm_eeg))
            self.last_tm_eeg = tm

            idxs = np.arange(0, 12) + self.sample_index_eeg
            self.sample_index_eeg += 12

            # timestamps are extrapolated backwards based on sampling rate and current time
            timestamps = self.reg_params[1] * idxs + self.reg_params[0]

            # push data
            self.callback_eeg(self.data_eeg, timestamps)

            # save last timestamp for disconnection timer
            self.last_timestamp = timestamps[-1]

            # reset sample
            self._init_sample_eeg()

    def _handle_ppg(self, sender, data):
        """Callback for receiving a sample.
        samples are received in this order : 56, 59, 62
        wait until we get x and call the data callback
        """

        handle = sender - 1
        timestamp = time()
        index = int((handle - 56) / 3)
        tm, d = self._unpack_ppg_channel(data)

        if self.last_tm_ppg == 0:
            self.last_tm_ppg = tm - 1

        self.data_ppg[index] = d
        self.timestamps_ppg[index] = timestamp
        # last data received
        if handle == 62:
            if tm != self.last_tm_ppg + 1:
                pass
                # print("missing sample %d : %d" % (tm, self.last_tm_ppg))
            self.last_tm_ppg = tm

            # calculate index of time samples
            indices = np.arange(0, LSL_PPG_CHUNK) + self.sample_index_ppg
            self.sample_index_ppg += LSL_PPG_CHUNK

            # timestamps are extrapolated backwards based on sampling rate and current time
            timestamps = self.reg_ppg_sample_rate[1] * indices + self.reg_ppg_sample_rate[0]

            # save last timestamp for disconnection timer
            self.last_timestamp = timestamps[-1]

            # push data
            if self.callback_ppg:
                self.callback_ppg(self.data_ppg, timestamps)

            # reset sample
            self._init_sample_ppg()

    def _handle_acc(self, sender, packet):
        """Handle incoming accelerometer data.
        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        if sender != 22:  # handle 0x17
            print("ERROR ACC" + str(sender))
            return

        timestamps = [time()] * 3

        # save last timestamp for disconnection timer
        self.last_timestamp = timestamps[-1]

        packet_index, samples = self._unpack_imu_channel(
            packet, scale=MUSE_ACCELEROMETER_SCALE_FACTOR)

        self.callback_acc(samples, timestamps)

    def _handle_gyro(self, sender, packet):
        """Handle incoming gyroscope data.
        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        if sender != 19:  # handle 0x14
            print("ERROR GYRO" + str(sender))
            return
        timestamps = [time()] * 3

        # save last timestamp for disconnection timer
        self.last_timestamp = timestamps[-1]

        packet_index, samples = self._unpack_imu_channel(
            packet, scale=MUSE_GYRO_SCALE_FACTOR)

        self.callback_gyro(samples, timestamps)

    def _handle_tele(self, sender, packet):
        """Handle the telemetry (battery, temperature and stuff) incoming data
        """
        if sender != 26:  # handle 0x1a
            print("ERROR TELE" + str(sender))
            return
        timestamp = time()

        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:16,uint:16,uint:16,uint:16"  # The rest is 0 padding
        data = bit_decoder.unpack(pattern)

        battery = data[1] / 512
        fuel_gauge = data[2] * 2.2
        adc_volt = data[3]
        temperature = data[4]

        self.callback_tele(
            timestamp, battery, fuel_gauge, adc_volt, temperature)

    def command_callback(dc):
        print("Received command callback completely: ")
        print(dc)
