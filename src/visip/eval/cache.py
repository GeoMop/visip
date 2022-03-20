from typing import *

from ..dev import data

import redis


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

    def is_finished(self, hash_int: int) -> bool:
        return self.value(hash_int) is not ResultCache.NoValue


class ResultCacheRedis(ResultCache):
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, db=0)

    def value(self, hash_int: int) -> Any:
        value = self.client.get(str(hash_int))
        if value is not None:
            return value
        else:
            return ResultCache.NoValue

    def insert(self, hash_int, bin_data):
        self.client.set(str(hash_int), bin_data)

    def clear(self):
        self.client.flushdb()
