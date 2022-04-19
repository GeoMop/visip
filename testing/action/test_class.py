import pytest

import visip as wf
from visip.dev import evaluation, task, module

@wf.Class
class Point:
    x: float
    y: float

@wf.workflow
def to_point(a: float, b: float) -> float:
    return Point(a, b)


def test_class():
    result = evaluation.run(to_point, 1, 2)
    print(result)
