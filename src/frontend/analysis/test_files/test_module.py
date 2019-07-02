import common.analysis as wf
import frontend.analysis.test_files.test_module1 as test_module1


@wf.workflow
def test_list(self, a, b):
    self.point = test_module1.Point(a,b)
    self.c = [a]
    List_1 = [a, b]
    List_2 = [self.c, List_1, self.point]
    return List_2

@wf.workflow
def test_list1(self, a, b):
    self.c = [a]
    List_1 = [a, b]
    return List_1

