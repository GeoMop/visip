import visip as wf


@wf.Class
class Point:
    x:float
    y:float


@wf.Class
class Quadrature:
    points:wf.List[Point]
    weights:float


@wf.workflow
def mid_rule(self):
    self.weights = [1]
    Quadrature_1 = Quadrature(points=[Point(x=0.5, y=0.5)], weights=self.weights)
    return Quadrature_1