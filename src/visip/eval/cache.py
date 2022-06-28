from typing import *

from ..dev import data
#from json_data import jsondata, serialize, deserialize
from visip.dev.data import serialize, deserialize

import redis
import json
import pickle


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



        self.types_map = {}

    def value(self, hash: bytes) -> Any:
        item = self.cache.get(hash, (self.NoValue, self.NoValue))
        return item[0]

    def time_interval(self, hash: bytes) -> Any:
        item = self.cache.get(hash, (self.NoValue, self.NoValue))
        return item[1]

    def insert(self, hash:bytes, value, time_interval):
        self.cache[hash] = value, time_interval

    def is_finished(self, hash_int: int) -> bool:
        return self.value(hash_int) is not ResultCache.NoValue

    def update_types_map(self, map):
        self.types_map.update(map)


class ResultCacheRedis(ResultCache):
    def __init__(self, host='localhost', port=6379):
        super().__init__()

        self.client = redis.Redis(host=host, port=port, db=0)

    def value(self, hash_int: int) -> Any:
        bin_data = self.client.get(str(hash_int))
        if bin_data is not None:
            #value = deserialize(json.loads(bin_data.decode('utf-8')), cls_dict=self.types_map)
            value = deserialize(bin_data)
            return value
        else:
            return ResultCache.NoValue

    def insert(self, hash_int, value, time_interval):
        #bin_data = json.dumps(serialize(value, module=True), sort_keys=True).encode('utf-8')
        bin_data = serialize(value)
        self.client.set(str(hash_int), bin_data)

    def clear(self):
        self.client.flushdb()
