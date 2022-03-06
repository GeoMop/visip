import visip as wf


@wf.workflow
def test_list(self, a, b):
    self.c = [a]
    self.e = [self.c, [a, b]]
    list_2 = [self.e[1][0], self.e[0]]
    return list_2


@wf.Class
class Point:
    x:float
    y:float


@wf.workflow
def test_class(self, a: Point, b: Point):
    self.a_x = a.x
    self.b_y = b.y
    Point_1 = Point(x=self.a_x, y=self.b_y)
    return Point_1


@wf.analysis
def test_analysis(self):
    self.tuple = test_list(a=10, b='hallo')
    self.point = test_list(a=Point(x=20, y=30), b=Point(x=40, y=50))
    self.list = test_list(a=1, b=2)
    self.extract = self.list[1]
    list_0 = [self.tuple, self.point, self.extract]
    return list_0


@wf.workflow
def test_dict(self, a, b, c):
    self.direct_dict = wf.dict((2, a), (3, b), (5, c))
    self.brace_dict = wf.dict((2, a), (3, b), (5, c))
    tuple_7 = (self.direct_dict[5], self.brace_dict[3])
    return tuple_7


@wf.action_def
def add(a:float, b:float) -> float:
    # User defined action cen not been represented.
    pass