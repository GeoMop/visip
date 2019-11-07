import visip as wf


@wf.workflow
def test_list(self, a, b):
    self.c = [a]
    d = [a, b]
    self.e = [self.c, d]
    return [self.e[1][0], self.e[0]]


@wf.Class
class Point:
    x:float
    y:float


@wf.workflow
def test_class(self, a: Point, b: Point):
    self.a_x = a.x
    self.b_y = b.y
    return Point(self.a_x, self.b_y)


@wf.analysis
def test_analysis(self):
    self.tuple = test_list(10, "hallo")
    self.point = test_list(Point(20, 30), Point(40, 50))
    self.list = test_list(1, 2)
    self.extract = self.list[1]
    return [self.tuple, self.point, self.extract]

@wf.workflow
def test_dict(self, a: float, b:float, c:float):
    self.direct_dict = wf.dict((2, a), (3, b), (5, c))
    self.brace_dict = {2:a, 3:b, 5:c}
    return (self.direct_dict[5], self.brace_dict[3])
    #return (self.brace_dict[3], )


"""
TODO:
- missing type hints in fn declaration
- results should be substituted
"""
