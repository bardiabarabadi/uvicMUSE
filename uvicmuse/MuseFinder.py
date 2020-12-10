from bleak import discover

# from .constants import *
from uvicmuse.constants import *

class MuseFinder(object):

    def __init__(self,
                 add_muse_to_list_callback=None,  # Used to call a UI function when a new muse is found
                 ):
        self.muses = []
        self.add_muse_to_list_callback = add_muse_to_list_callback

    async def search_for_muses(self, timeout=1):
        self.muses = []
        for i in range(int(timeout / 2) + 1):
            # search for muses timeout/2 times, 2 seconds each time
            devices = await discover(timeout=2)
            for d in devices:
                if MUSE_NAME in d.name and not self._is_already_found(newly_found_muse=d):
                    self.muses.append(d)
                    if self.add_muse_to_list_callback is not None:
                        self.add_muse_to_list_callback(d)

    def _is_already_found(self, newly_found_muse):
        for old_muse in self.muses:
            if newly_found_muse.name == old_muse.name:
                return True
        return False

    def get_muses(self):
        return self.muses
