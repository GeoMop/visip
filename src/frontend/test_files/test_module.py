import common as wf
from src.frontend.test_files import home


@wf.workflow
def test_list(self, a, b):
    self.c = [a]
    d = [a, b]
    self.e = [self.c, d]
    return [self.e[1][0], self.e[0]]


@wf.workflow
def test_class(self, a: home.Point, b: home.Point):
    self.a_x = a.x
    self.b_y = b.y
    return home.Point(self.a_x, self.b_y)


@wf.analysis
def test_analysis(self):
    self.tuple = test_list(10, "hallo")
    self.point = test_list(home.Point(20, 30), home.Point(40, 50))
    self.list = test_list(1, 2)
    self.extract = self.list[1]
    return [self.tuple, self.point, self.extract]