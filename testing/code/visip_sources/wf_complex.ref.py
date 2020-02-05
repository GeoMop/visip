import visip as wf


@wf.action_def
def read_file(input:wf.FileIn) -> int:
    # User defined action cen not been represented.
    pass


@wf.workflow
def gmsh_run(self, geometry, mesh_step):
    self.mesh_file_out = wf.derived_file(f=geometry, ext='.msh')
    Value_5 = '{:8.2g}'
    list_1 = ['../gmsh.sh', geometry, '-2', '-clscale', wf.format(Value_5, mesh_step), '-format', 'msh2', '-o', self.mesh_file_out]
    Value_9 = '.msh_log'
    self.mesh_res = wf.system(arguments=list_1, stdout=wf.derived_file(f=geometry, ext=Value_9), stderr=wf.SysFile.STDOUT, workdir='')
    self.joined = (self.mesh_file_out, self.mesh_res)
    self.mesh_file = wf.file_in(path=self.joined[0], workspace='')
    return self.mesh_file


@wf.workflow
def simple_wf(self, mesh_step):
    file_in_1 = wf.file_in(path='darcy_flow.yaml.tmpl', workspace='')
    self.geometry = wf.file_in(path='square.geo', workspace='')
    self.mesh = gmsh_run(geometry=self.geometry, mesh_step=mesh_step)
    self.flow_input = wf.file_from_template(template=file_in_1, parameters=wf.dict(('MESH', self.mesh)), delimiters='<>')
    list_1 = ['../flow.sh', self.flow_input, '-o', '.']
    self.res = wf.system(arguments=list_1, stdout=wf.SysFile.PIPE, stderr=wf.SysFile.STDOUT, workdir='')
    return self.res