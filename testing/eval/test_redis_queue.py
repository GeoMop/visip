from visip.eval.redis_queue import RedisQueue


def test_redis_queue():
    # initialize and clear queue
    q = RedisQueue()
    q.clear()

    q.put("a")
    d = q.get()
    assert d == "a"
