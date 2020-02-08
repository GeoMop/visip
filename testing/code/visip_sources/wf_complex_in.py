import visip as wf

@wf.action_def
def read_file(input: wf.FileIn) -> int:
    with open(input.path, "r") as f:
        content = f.readlines()
    return len(content)



@wf.workflow
def gmsh_run(self, geometry: wf.FileIn, mesh_step: float = 1.0) -> wf.FileIn:
    self.mesh_file_out = wf.derived_file(geometry, ".msh")
    self.flow_input = wf.file_from_template(wf.file_in('darcy_flow.yaml.tmpl'), dict(mesh=self.mesh_file_out))
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




