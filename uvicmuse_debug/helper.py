import platform
import pygatt
import logging
import serial.tools.list_ports

logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
logging.getLogger('pygatt').setLevel(logging.DEBUG)


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
    print('Interface is seleceted as ' + str(interface))
    if backend == 'gatt':
        interface = interface or 'hci0'
        adapter = pygatt.GATTToolBackend(interface)
    else:

        if platform.system() == 'Windows':
            port_list = serial.tools.list_ports.comports()
            if len(port_list) == 0:
                print('No dongle found')
                return []

            for com in port_list:
                print('found ' + com.description + ', manufactured: ' + com.manufacturer)
                if com.manufacturer == 'Bluegiga':
                    interface = com.device

        adapter = pygatt.BGAPIBackend(serial_port=interface)

    adapter.start()
    print('Searching for Muses, this may take up to 10 seconds...                                 ')
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
