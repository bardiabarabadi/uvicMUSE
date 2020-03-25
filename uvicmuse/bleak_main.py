import numpy
import os
import asyncio
from bleak import BleakScanner, BleakClient
from constants import *

global a

UUID_ = '0000fe8d-0000-1000-8000-00805f9b34fb'


async def write_cmd(cmd, muse, handle):
    """Wrapper to write a command to the Muse device.
    cmd -- list of bytes"""
    await muse.write_gatt_descriptor(handle=handle, data=cmd)


def eeg_callback(sender, data):
    print(f"{sender}: {data}")

async def run(loop):
    scanner = BleakScanner()
    await scanner.start()
    await asyncio.sleep(10.0)
    await scanner.stop()
    devices = await scanner.get_discovered_devices()
    muses = []
    for d in devices:
        print(d)
        if 'Muse' in str(d):
            muses.append(d)
    if len(muses) == 0:
        print("Couldn't find any MUSE...\nRetry.")
        return
    else:
        muse = BleakClient(muses[0].address, loop=loop)
        try:
            await muse.connect(timeout=20)
            await muse.start_notify(MUSE_GATT_ATTR_AF8, eeg_callback)
            await muse.connect(timeout=20)
            print("Connected to " + str(muses[0]))
            # muse.get_appropriate_uuid()
            for i in range(64):
                try:
                    await write_cmd([0x04, 0x70, 0x32, 0x31, 0x0a], muse, i)
                except Exception as e:
                    print (str(i) + ' : ' +str(e))

            services = await muse.get_services()

            print ("Started notify. Waiting for 10 seconds...")
            await asyncio.sleep(10.0)
            await muse.stop_notify(MUSE_GATT_ATTR_AF8)
            print("Stopped notify.")

        except Exception as e:
            print(e)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()
    print('Done')
