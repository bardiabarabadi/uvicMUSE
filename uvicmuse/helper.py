import platform
import pygatt
import os
import sys


def resource_path(rel_path):
    if hasattr(sys, '_MEIPASS'):
        print("Has attr MEIPASS")
        return os.path.join(sys._MEIPASS, rel_path)

    return os.path.join(os.path.abspath("."), rel_path)


def resolve_backend(backend):
    if backend in ['auto', 'gatt', 'bgapi']:
        platformName = platform.system().lower()
        if backend == 'auto':
            if platformName == 'linux' or platformName == 'linux2':
                backend = 'gatt'
            elif platformName == 'windows' and int(platform.version().replace('.', '')) >= 10015063:
                backend = 'bgapi'
            else:
                backend = 'bgapi'
        return backend
    else:
        raise (ValueError('Backend must be one of: auto, gatt, bgapi'))


def find_muse(name=None):
    muses = list_muses()
    if name:
        for muse in muses:
            if muse['name'] == name:
                return muse
    elif muses:
        return muses[0]


def list_muses(backend='bgapi', interface=None):
    backend = resolve_backend(backend)

    if backend == 'gatt':
        interface = interface or 'hci0'
        adapter = pygatt.GATTToolBackend(interface)
    else:
        adapter = pygatt.BGAPIBackend(serial_port=interface)

    adapter.start()
    # print('Searching for Muses, this may take up to 10 seconds...                                 ')
    devices = adapter.scan(timeout=10.5)
    adapter.stop()
    muses = []

    for device in devices:
        if device['name'] and 'Muse' in device['name']:
            muses = muses + [device]

    if muses:
        for muse in muses:
            pass
            # print('Found device %s, MAC Address %s' %
            #       (muse['name'], muse['address']))
    else:
        pass
        # print('No Muses found.')

    return muses


def is_data_valid(data, timestamps):
    if timestamps == 0.0:
        return False
    if all(data == 0.0):
        return False
    return True


def PPG_error(Exceptions):
    pass
