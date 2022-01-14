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
        self.cache: Dict[int, Any] = {}

    def value(self, hash_int:int) -> Any:
        return self.cache.get(hash_int, ResultCache.NoValue)

    def insert(self, hash_int, value):
        self.cache[hash_int] = value


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
