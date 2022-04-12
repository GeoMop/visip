import os
import pytest
import visip as wf
from visip.dev import evaluation
script_dir = os.path.dirname(os.path.realpath(__file__))

@wf.workflow
def gmsh_run(self, geometry: wf.FileIn, mesh_step: float = 1.0) -> wf.FileIn:
    self.mesh_file_out = wf.derived_file(geometry, ".msh")
    log_file = wf.derived_file(geometry, ".msh_log")
    self.mesh_res = wf.system(['../gmsh.sh', geometry, "-2", "-clscale",
                               wf.format("{:8.2g}", mesh_step), "-format", "msh2", "-o", self.mesh_file_out],
                                stdout=log_file, stderr=wf.SysFile.STDOUT)
    self.joined = (self.mesh_file_out, self.mesh_res)
    self.mesh_file = wf.file_in(self.joined[0])
    return self.mesh_file


FLOW_PATH = "flow.sh"
GMSH_PATH = "gmsh.sh"
@wf.workflow
def simple_wf(self, mesh_step) -> wf.ExecResult:
    self.geometry = wf.file_in('square.geo')
    self.mesh = gmsh_run(self.geometry, mesh_step)
    self.flow_input = wf.file_from_template(wf.file_in('darcy_flow.yaml.tmpl'), dict(MESH=self.mesh))
    self.res = wf.system(['../flow.sh', self.flow_input, "-o", "."], stdout=wf.SysFile.PIPE, stderr=wf.SysFile.STDOUT)
    return self.res


def remove_files(files, prefix=""):
    for f in files:
        try:
            os.remove(os.path.join(script_dir, prefix, f))
        except FileNotFoundError:
            pass

# TODO:
# This can not be a unit test as it depends on flow and gmsh, should move these to 'integration_tests'
@pytest.mark.skip
def test_simple_wf():
    """
    Test system action with mock command.
    :return:
    """
    remove_files(["darcy_flow.yaml", "square.msh_log", "square.msh"], prefix="flow_case")

    print("Root workspace: ", os.getcwd())
    eval = evaluation.Evaluation(workspace=os.path.join(script_dir, "flow_case"))
    result = eval.run(simple_wf, 0.1).result
    print(result.stdout.decode())


