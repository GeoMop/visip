from typing import *


class ResultCache:
    """
    Trivial implementation of the task hash database.
    Possible improvements:
    - pemanent storage, store values in file, have only hashes in the memory
    - precise hash type
    - safe also date of values, remove expired values
    """
    class NoValue:
        pass

    def __init__(self):
        self.cache: Dict[bytes, Tuple[Any, Tuple[float, float]]] = {}



    def value(self, hash: bytes) -> Any:
        item = self.cache.get(hash, (self.NoValue, self.NoValue))
        return item[0]

    def time_interval(self, hash: bytes) -> Any:
        item = self.cache.get(hash, (self.NoValue, self.NoValue))
        return item[1]

    def insert(self, hash:bytes, value, time_interval):
        self.cache[hash] = value, time_interval

    def is_finished(self, hash_int:int) -> bool:
        return self.value(hash_int) is not ResultCache.NoValue