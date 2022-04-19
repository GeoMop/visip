import visip as wf


@wf.Class
class Point:
    x:wf.Float
    y:wf.Float


@wf.Class
class Quadrature:
    points:wf.List(Point)
    weights:wf.List(wf.Float)


@wf.workflow
def mid_rule(self) -> Quadrature:
    self.weights = [1.0]
    Quadrature_1 = Quadrature(points=[Point(x=0.5, y=0.5)], weights=self.weights)
    return Quadrature_1
