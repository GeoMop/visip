import visip as wf


@wf.workflow
def test_list(self, a, b):
    self.c = [a]
    self.e = [self.c, [a, b]]
    A_list_2 = [self.e[1][0], self.e[0]]
    return A_list_2


@wf.Class
class Point:
    x:wf.Float
    y:wf.Float


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
    A_list_1 = [self.tuple, self.point, self.extract]
    return A_list_1


@wf.workflow
def test_dict(self, a, b, c):
    self.direct_dict = wf.dict((2, a), (3, b), (5, c))
    self.brace_dict = wf.dict((2, a), (3, b), (5, c))
    A_tuple_7 = (self.direct_dict[5], self.brace_dict[3])
    return A_tuple_7


@wf.action_def
def add(a: wf.Float, b: wf.Float) -> wf.Float:
    # User defined action cen not been represented.
    pass