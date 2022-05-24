import visip as wf
from visip.dev import evaluation
from visip.eval.cache import ResultCacheRedis
from visip.eval.redis_server import RedisServer

import os
import time


@wf.Class
class Point:
    x: float
    y: float


@wf.action_def
def add(a: int, b: int) -> int:
    return a + b


@wf.workflow
def sum_wf(self, a, b):
    return add(a, b)


@wf.analysis
def sum_an(self):
    return sum_wf(1, 2)


@wf.workflow
def to_point(a: float, b: float) -> float:
    return Point(a, b)


def test_redis():
    # start server
    server = RedisServer(os.path.join(os.path.dirname(__file__), "redis_data"), 10001)
    server.start()
    time.sleep(2)

    # initialize and clear cache
    cache = ResultCacheRedis(port=10001)
    cache.clear()

    cache.insert(1, 3)
    assert cache.value(1) == 3

    # stop server
    server.stop()
    time.sleep(2)

    # start server again
    server = RedisServer(os.path.join(os.path.dirname(__file__), "redis_data"), 10001)
    server.start()
    time.sleep(2)

    # initialize again
    cache = ResultCacheRedis(port=10001)

    assert cache.value(1) == 3

    # stop server
    server.stop()
    time.sleep(2)


def test_wf():
    # start server
    server = RedisServer(os.path.join(os.path.dirname(__file__), "redis_data"), 10001)
    server.start()
    time.sleep(2)

    # initialize and clear cache
    cache = ResultCacheRedis(port=10001)
    cache.clear()

    result = evaluation.Evaluation(cache=cache).run(sum_an).result
    assert result == 3
    result = evaluation.Evaluation(cache=cache).run(sum_an).result
    assert result == 3

    # not working
    # result = evaluation.Evaluation(cache=cache).run(to_point, 1.0, 2.0).result
    # print(result)

    # stop server
    server.stop()
    time.sleep(2)
