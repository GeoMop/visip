from typing import *

from ..dev import data

import pymongo
import bson


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


class ResultCacheMongo(ResultCache):
    _INDEX_NAME = 'hash_int_1'

    def __init__(self):
        client = pymongo.MongoClient('127.0.0.1', 27017)
        db = client.visip_database
        self.mongo_collection = db.visip_collection

        index_inf = self.mongo_collection.index_information()
        if ResultCacheMongo._INDEX_NAME not in index_inf:
            hash_int1 = pymongo.IndexModel(
                keys=[('hash_int', pymongo.ASCENDING)],
                name=ResultCacheMongo._INDEX_NAME)
            self.mongo_collection.create_indexes([hash_int1])

    def value(self, hash_int: int) -> Any:
        res = self.mongo_collection.find_one({
            'hash_int': hash_int
        })
        if res:
            try:
                value = data.deserialize(res['value'])
                return value
            except KeyError:
                pass
        return ResultCache.NoValue

    def insert(self, hash_int, value):
        thebytes = data.serialize(value)
        self.mongo_collection.update_one(
            filter={
                'hash_int': hash_int
            },
            update={
                '$set': {
                    'hash_int': hash_int,
                    'value': bson.binary.Binary(thebytes)
                }
            },
            upsert=True
        )

    def clear(self):
        self.mongo_collection.delete_many(
            filter={}
        )
