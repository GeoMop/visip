from visip.eval.cache import ResultCacheMongo
from json_data import jsondata

import json


def test_mongo():
    @jsondata
    class A:
        a: int = 1
        b: str = "test"
        c: float = 2.0

    # initialize and clear cache
    cache = ResultCacheMongo()
    cache.clear()

    # create object and save to cache
    a = A(a=2, b="hello", c=3.0)
    bin_data = json.dumps(a.serialize(), sort_keys=True).encode('utf-8')
    cache.insert(1, bin_data)

    # read data from cache
    bin_data_saved = cache.value(1)
    a_saved = A.deserialize(json.loads(bin_data_saved.decode('utf-8')))
    assert a_saved == a
