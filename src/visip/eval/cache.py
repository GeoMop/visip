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
        self.cache: Dict[bytes, Any] = {}

    def value(self, hash: bytes) -> Any:
        return self.cache.get(hash, ResultCache.NoValue)

    def insert(self, hash, value):
        self.cache[hash] = value

    def is_finished(self, hash_int:int) -> bool:
        return self.value(hash_int) is not ResultCache.NoValue