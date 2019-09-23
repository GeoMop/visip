import attr

import load_yaml


class Flow_input(object):
    flow123d_version: str
    problem: load_yaml.Coupling_Sequential

    def __init__(self, data):
        self.flow123d_version = data["flow123d_version"]
        self.problem = data['problem']

    def __repr__(self):
        return 'flow123d_version: {} {}'.format(self.flow123d_version, self.problem)


data = load_yaml.load_file()
# print(data)
# print(data['flow123d_version'])
FF = Flow_input(data)
print(FF.problem.mesh)
