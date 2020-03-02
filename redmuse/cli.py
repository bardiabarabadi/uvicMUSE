#!/usr/bin/python
import sys
import argparse
from .udp_stream import *


class CLI:
    def __init__(self, command):
        # use dispatch pattern to invoke method with same name
        getattr(self, command)()

    @staticmethod
    def list():
        parser = argparse.ArgumentParser(
            description='List available Muse devices.')
        parser.add_argument("-b", "--backend",
                            dest="backend", type=str, default="bgapi",
                            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.")
        parser.add_argument("-i", "--interface",
                            dest="interface", type=str, default=None,
                            help="The interface to use, 'hci0' for gatt or a com port for bgapi. WIll auto-detect if not specified")
        args = parser.parse_args(sys.argv[2:])
        from . import list_muses
        list_muses(args.backend, args.interface)

    @staticmethod
    def stream():
        parser = argparse.ArgumentParser(
            description='Start an LSL stream from Muse headset.')
        parser.add_argument("-a", "--address",
                            dest="address", type=str, default=None,
                            help="Device MAC address.")
        parser.add_argument("-n", "--name",
                            dest="name", type=str, default=None,
                            help="Name of the device.")
        parser.add_argument("-b", "--backend",
                            dest="backend", type=str, default="bgapi",
                            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.")
        parser.add_argument("-i", "--interface",
                            dest="interface", type=str, default=None,
                            help="The interface to use, 'hci0' for gatt or a com port for bgapi.")
        parser.add_argument("-p", "--ppg",
                            default=False, action="store_true", help="Include PPG data")
        parser.add_argument("-c", "--acc",
                            default=False, action="store_true", help="Include accelerometer data")
        parser.add_argument("-g", "--gyro",
                            default=False, action="store_true", help="Include gyroscope data")
        parser.add_argument('-d', '--disable-eeg', dest='disable_eeg',
                            action='store_true', help="Disable EEG data")
        args = parser.parse_args(sys.argv[2:])
        from . import stream

        stream(args.address, args.backend,
               args.interface, args.name, args.ppg, args.acc, args.gyro, args.disable_eeg)

    @staticmethod
    def udp_stream():
        parser = argparse.ArgumentParser(
            description='Start a stream from Muse headset and send to UDP socket.')
        parser.add_argument("-a", "--address",
                            dest="address", type=str, default=None,
                            help="Device MAC address.")
        parser.add_argument("-n", "--name",
                            dest="name", type=str, default=None,
                            help="Name of the device.")
        parser.add_argument("-b", "--backend",
                            dest="backend", type=str, default="bgapi",
                            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.")
        parser.add_argument("-i", "--interface_port",
                            dest="interface", type=str, default='localhost',
                            help="The port for UDP socket. Default is localhost")
        parser.add_argument("-p", "--ppg",
                            default=False, action="store_true", help="Include PPG data")
        parser.add_argument("-c", "--acc",
                            default=False, action="store_true", help="Include accelerometer data")
        parser.add_argument("-g", "--gyro",
                            default=False, action="store_true", help="Include gyroscope data")
        parser.add_argument('-d', '--disable-eeg', dest='disable_eeg', default=False,
                            action='store_true', help="Disable EEG data")

        parser.add_argument("-t", "--port",
                            dest="udp_port", type=int, default=10000,
                            help="UDP port")

        args = parser.parse_args(sys.argv[2:])

        udp_stream(args.address, args.backend,
                   args.interface, args.name, args.ppg, args.acc, args.gyro, args.disable_eeg, args.udp_port)

    @staticmethod
    def record():
        parser = argparse.ArgumentParser(
            description='Record data from an LSL stream.')
        parser.add_argument("-d", "--duration",
                            dest="duration", type=int, default=60,
                            help="Duration of the recording in seconds.")
        parser.add_argument("-f", "--filename",
                            dest="filename", type=str, default=None,
                            help="Name of the recording file.")
        parser.add_argument("-dj", "--dejitter",
                            dest="dejitter", type=bool, default=True,
                            help="Whether to apply dejitter correction to timestamps.")
        parser.add_argument("-t", "--type", type=str, default="EEG",
                            help="Data type to record from. Either EEG, PPG, ACC, or GYRO.")

        args = parser.parse_args(sys.argv[2:])
        from . import record
        record(args.duration, args.filename, args.dejitter, args.type)

    @staticmethod
    def record_direct():
        parser = argparse.ArgumentParser(
            description='Record directly from Muse without LSL.')
        parser.add_argument("-a", "--address",
                            dest="address", type=str, default=None,
                            help="Device MAC address.")
        parser.add_argument("-n", "--name",
                            dest="name", type=str, default=None,
                            help="Name of the device.")
        parser.add_argument("-b", "--backend",
                            dest="backend", type=str, default="auto",
                            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.")
        parser.add_argument("-i", "--interface",
                            dest="interface", type=str, default=None,
                            help="The interface to use, 'hci0' for gatt or a com port for bgapi.")
        parser.add_argument("-d", "--duration",
                            dest="duration", type=int, default=60,
                            help="Duration of the recording in seconds.")
        parser.add_argument("-f", "--filename",
                            dest="filename", type=str, default=None,
                            help="Name of the recording file.")
        args = parser.parse_args(sys.argv[2:])
        from . import record_direct
        record_direct(args.address, args.backend,
                      args.interface, args.name, args.duration, args.filename)

