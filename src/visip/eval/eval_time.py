import time
"""
Synchronised time for processes.
"""

class Time:
    """
    See: https://peps.python.org/pep-0418
    Starting with use of monotonic, try high resolution timers if neccessry.
    """

    def __init__(self, sync_time: float = 0):
        """
        :param sync_time: reference time of construction
        """
        self._own_sync_time = self.time()
        self._global_sync_time = sync_time
        self._time_correction = self._global_sync_time - self._own_sync_time
        self.clock_res = time.get_clock_info("monotonic").resolution

    def time(self):
        return time.monotonic()

    def sync_time(self):
        return self._time_correction + self.time()
