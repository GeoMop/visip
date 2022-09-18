from visip.eval.cache import ResultCacheRedis
from visip.eval.redis_queue import RedisQueue
from json_data import jsondata
import multiprocessing as mp

import json


def test_redis():
    @jsondata
    class A:
        a: int = 1
        b: str = "test"
        c: float = 2.0

    # initialize and clear cache
    cache = ResultCacheRedis()
    cache.clear()

    # create object and save to cache
    a = A(a=2, b="hello", c=3.0)
    bin_data = json.dumps(a.serialize(), sort_keys=True).encode('utf-8')
    cache.insert(1, bin_data, (0, 0))

    # read data from cache
    bin_data_saved = cache.value(1)
    a_saved = A.deserialize(json.loads(bin_data_saved.decode('utf-8')))
    assert a_saved == a


def test_more_clients():
    @jsondata
    class A:
        a: int = 1
        b: str = "test"
        c: float = 2.0

    # initialize and clear cache
    cache1 = ResultCacheRedis()
    cache1.clear()

    cache2 = ResultCacheRedis()
    cache2.clear()

    # create object and save to cache
    a = A(a=2, b="hello", c=3.0)
    bin_data = json.dumps(a.serialize(), sort_keys=True).encode('utf-8')
    cache1.insert(1, bin_data, (0, 0))

    # read data from cache
    bin_data_saved = cache2.value(1)
    a_saved = A.deserialize(json.loads(bin_data_saved.decode('utf-8')))
    assert a_saved == a


def run(id):
    cache = ResultCacheRedis()
    queue = RedisQueue(id)

    bin_data = b"hello"
    cache.insert(1, bin_data, (0, 0))

    queue.put(1)


def test_multiprocess():
    # initialize and clear cache
    cache = ResultCacheRedis()
    cache.clear()

    ctx = mp.get_context('spawn')
    queue = RedisQueue()
    proc = ctx.Process(target=run, args=(queue.id, ))
    proc.start()

    queue.get()

    # read data from cache
    bin_data_saved = cache.value(1)
    assert bin_data_saved == b"hello"

    proc.join()
