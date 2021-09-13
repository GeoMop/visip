from visip.eval.cache import ResultCacheMongo


def test_mongo():
    cache = ResultCacheMongo()

    cache.clear()
    cache.insert(1, "hello")
    assert cache.value(1) == "hello"
