import visip as wf

import pickle


@wf.Class
class Point:
    x: float
    y: float


def test_pickle():
    p = Point()
    t = p._value.output_type
    pickle.dumps(t)
