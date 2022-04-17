import visip as wf
from visip.dev import evaluation


@wf.Class
class Point:
    x: float
    y: float


@wf.action_def
def to_point(a: float, b: float) -> float:
    return Point(a, b)


@wf.workflow
def point_wf(self, a, b):
    return to_point(a, b)


@wf.analysis
def point_an(self):
    return point_wf(1.0, 2.0)


def test_dummy():
    result = evaluation.run(point_an)
