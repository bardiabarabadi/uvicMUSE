import platform

def resolve_backend(backend):
    if backend in ['auto', 'gatt', 'bgapi', 'bluemuse']:
        platformName = platform.system().lower()
        if backend == 'auto':
            if platformName == 'linux' or platformName == 'linux2':
                backend = 'gatt'
            elif platformName == 'windows' and int(platform.version().replace('.', '')) >= 10015063:
                backend = 'bluemuse'
            else:
                backend = 'bgapi'
        return backend
    else:
        raise(ValueError('Backend must be one of: auto, gatt, bgapi, bluemuse.'))
