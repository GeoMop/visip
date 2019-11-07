import visip as wf

# Class decorator creates the data class
# and the constructor action.
@wf.Class
class Point:
    x: float
    y: float


@wf.Class
class Quadrature:
    points: wf.List[Point]
    weights: float

# Workflow decorator creates the 'mid_rule' workflow action.
# Auxiliary variable 'self' is used to keep variable names
@wf.workflow
def mid_rule(self) -> Quadrature:
    points = [Point(0.5, 0.5)]
    self.weights = [1]
    return Quadrature(points, self.weights)
