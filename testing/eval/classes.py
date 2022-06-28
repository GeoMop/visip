import visip as wf


@wf.Class
class Point:
    x: float
    y: float


@wf.Class
class Line:
    p1: Point
    p2: Point
