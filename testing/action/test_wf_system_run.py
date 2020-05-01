import os
import pytest
import visip as wf
from visip.dev import evaluation

script_dir = os.path.dirname(os.path.realpath(__file__))


@wf.workflow
def simple_wf(self) -> wf.ExecResult:
    self.res = wf.system(['dir'], stdout=wf.SysFile.PIPE,
                         stderr=wf.SysFile.STDOUT)
    return self.res


def test_simple_wf():
    print('Root workspace: ', os.getcwd())
    result = evaluation.run(simple_wf, workspace=os.path.join(script_dir, "inputs"))
    print(result.stdout.decode())




