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
def test_class(self, a, b):
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