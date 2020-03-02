import argparse
import sys
from .cli import CLI


def main():
    parser = argparse.ArgumentParser(
        description='Python package for streaming and recording EEG data from the Muse 1&2 headset.',
        usage='''redmuse <command> [<args>]
    Available commands:
    list        List available Muse devices.
                -b --backend    BLE backend to use. can be auto, bluemuse, gatt or bgapi.
                -i --interface  The interface to use, 'hci0' for gatt or a com port for bgapi.

    stream      Start an LSL stream from Muse headset.
                -a --address    Device MAC address.
                -n --name       Device name (e.g. Muse-41D2).
                -b --backend    BLE backend to use. can be auto, bluemuse, gatt or bgapi.
                -i --interface  The interface to use, 'hci0' for gatt or a com port for bgapi.
                -p --ppg        Include PPG data
                -c --acc        Include accelerometer data
                -g --gyro       Include gyroscope data
                --disable-eeg   Disable EEG data

    stream      Start an LSL stream from Muse headset.
                -a --address    Device MAC address.
                -n --name       Device name (e.g. Muse-41D2).
                -b --backend    BLE backend to use. can be auto, bluemuse, gatt or bgapi (Default).
                -i --interface_port  The port for UDP socket. Default is localhost
                -t --port       UDP port
                -p --ppg        Include PPG data
                -c --acc        Include accelerometer data
                -g --gyro       Include gyroscope data
                --disable-eeg   Disable EEG data

    record   Record EEG data from an LSL stream.
                -d --duration   Duration of the recording in seconds.
                -f --filename   Name of the recording file.
                -dj --dejitter  Whether to apply dejitter correction to timestamps.
                -t --type       Data type to record from. Either EEG, PPG, ACC, or GYRO 

    record_direct      Record data directly from Muse headset (no LSL).
                -a --address    Device MAC address.
                -n --name       Device name (e.g. Muse-41D2).
                -b --backend    BLE backend to use. can be auto, bluemuse, gatt or bgapi.
                -i --interface  The interface to use, 'hci0' for gatt or a com port for bgapi.
        ''')

    parser.add_argument('command', help='Command to run.')

    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])

    if not hasattr(CLI, args.command):
        print('Incorrect usage. See help below.')
        parser.print_help()
        exit(1)

    cli = CLI(args.command)


if __name__ == '__main__':
    main()
