import common as wf
import frontend.test_files.home as home


@wf.workflow
def test_list(self, a, b):
    self.c = [a]
    self.e = [self.c, [a, b]]
    List_3 = [self.e[1][0], 10, [1, 3, 3, 4, 'str']]
    return List_3


@wf.workflow
def test_class(self, a, b):
    self.a_x = a.x
    self.b_y = b.y
    Point_1 = home.Point(x=self.a_x, y=self.b_y)
    return Point_1


@wf.analysis
def test_analysis(self):
    self.tuple = test_list(a=10, b='hallo')
    self.point = test_list(a=home.Point(x=20, y=30), b=home.Point(x=40, y=50))
    self.list = test_list(a=1, b=2)
    self.extract = self.list[1]
    List_1 = [self.tuple, self.point, self.extract]
    return List_1