import visip as wf
import visip_gui.test_files.home as home


@wf.workflow
def test_clas(self, a, b):
    self.c = [a]
    self.e = [self.c, [a, b]]
    list_3 = [[1, 4, 3, 3, 'str'], self.e[1][0]]
    return list_3


@wf.workflow
def test_class(self, a, b):
    self.a_x = a.x
    self.b_y = b.y
    Point_1 = home.Point(x=self.a_x, y=self.b_y)
    return Point_1


@wf.analysis
def test_analysis(self):
    self.tuple = test_clas(a=10, b='hallo')
    self.point = test_clas(a=home.Point(x=20, y=30), b=home.Point(x=40, y=50))
    self.list = test_clas(a=1, b=2)
    self.extract = self.list[1]
    list_0 = [self.tuple, self.point, self.extract]
    return list_0


@wf.workflow
def system_test_wf(self, script_name):
    Value_1 = 'python'
    file_r_1 = wf.file_in(path=script_name, workspace='')
    Value_3 = '-m'
    Value_8 = 'msg_file.txt'
    Value_9 = ''
    self.res = wf.system(arguments=['echo', 'Hallo world'], stdout=wf.file_out(path=Value_8, workspace=Value_9), stderr=None)
    self.msg_file = wf.file_in(path='msg_file.txt', workspace=self.res.workdir)
    Value_11 = 123
    self.res_0 = wf.system(arguments=[Value_1, file_r_1, Value_3, self.msg_file, Value_11], stdout=wf.SysFile.PIPE, stderr=wf.SysFile.STDOUT)
    return self.res_0