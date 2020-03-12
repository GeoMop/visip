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
        self.cache: Dict[int, Any] = {}

    def value(self, hash_int:int) -> Any:
        return self.cache.get(hash_int, ResultCache.NoValue)

    def insert(self, hash_int, value):
        self.cache[hash_int] = value