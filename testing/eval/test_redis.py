import visip as wf
from visip.dev import evaluation
from visip.eval.cache import ResultCacheRedis
from visip.eval.redis_server import RedisServer
from visip.dev.module import Module
from visip.dev.dtype import List, Tuple, Dict, Str

from classes import Point, Line

import os
import time


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
def to_point(a: float, b: float) -> Point:
    return Point(a, b)


@wf.workflow
def to_line(a: float, b: float, c: float, d: float) -> Line:
    return Line(Point(a, b), Point(c, d))


@wf.workflow
def to_list(a: float, b: float, c: float, d: float) -> List(Point):
    return [Point(a, b), Point(c, d)]


@wf.workflow
def to_tuple(a: float, b: float, c: float, d: float) -> Tuple(Point, Point):
    return (Point(a, b), Point(c, d))


@wf.workflow
def to_dict(a: float, b: float, c: float, d: float) -> Dict(Str, Point):
    return {"a": Point(a, b), "b": Point(c, d)}


@wf.workflow
def to_struct(a: float, b: float, c: float, d: float) -> Tuple(Line, List(Dict(Str, Point))):
    return (Line(Point(a, b), Point(c, d)), [{"a": Point(a, b), "b": Point(c, d)}])


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
    Module.load_module(os.path.join(os.path.dirname(__file__), "classes.py"))

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

    # point
    result = evaluation.Evaluation(cache=cache).run(to_point, 1.0, 2.0).result
    assert result.x == 1.0
    assert result.y == 2.0
    result = evaluation.Evaluation(cache=cache).run(to_point, 1.0, 2.0).result
    assert result.x == 1.0
    assert result.y == 2.0

    # line
    result = evaluation.Evaluation(cache=cache).run(to_line, 1.0, 2.0, 3.0, 4.0).result
    assert result.p1.x == 1.0
    assert result.p2.x == 3.0
    result = evaluation.Evaluation(cache=cache).run(to_line, 1.0, 2.0, 3.0, 4.0).result
    assert result.p1.x == 1.0
    assert result.p2.x == 3.0

    # list
    result = evaluation.Evaluation(cache=cache).run(to_list, 1.0, 2.0, 3.0, 4.0).result
    assert result[0].x == 1.0
    assert result[1].x == 3.0
    result = evaluation.Evaluation(cache=cache).run(to_list, 1.0, 2.0, 3.0, 4.0).result
    assert result[0].x == 1.0
    assert result[1].x == 3.0

    # tuple
    result = evaluation.Evaluation(cache=cache).run(to_tuple, 1.0, 2.0, 3.0, 4.0).result
    assert result[0].x == 1.0
    assert result[1].x == 3.0
    result = evaluation.Evaluation(cache=cache).run(to_tuple, 1.0, 2.0, 3.0, 4.0).result
    assert result[0].x == 1.0
    assert result[1].x == 3.0

    # dict
    result = evaluation.Evaluation(cache=cache).run(to_dict, 1.0, 2.0, 3.0, 4.0).result
    assert result["a"].x == 1.0
    assert result["b"].x == 3.0
    result = evaluation.Evaluation(cache=cache).run(to_dict, 1.0, 2.0, 3.0, 4.0).result
    assert result["a"].x == 1.0
    assert result["b"].x == 3.0

    # struct
    result = evaluation.Evaluation(cache=cache).run(to_struct, 1.0, 2.0, 3.0, 4.0).result
    assert result[0].p1.x == 1.0
    assert result[0].p2.x == 3.0
    assert result[1][0]["a"].x == 1.0
    assert result[1][0]["b"].x == 3.0
    result = evaluation.Evaluation(cache=cache).run(to_struct, 1.0, 2.0, 3.0, 4.0).result
    assert result[0].p1.x == 1.0
    assert result[0].p2.x == 3.0
    assert result[1][0]["a"].x == 1.0
    assert result[1][0]["b"].x == 3.0

    # stop server
    server.stop()
    time.sleep(2)
