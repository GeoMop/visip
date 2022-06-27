import visip as wf
from modules import toolbox  # visip module
"""
Simple analysis:
+ several interconnected workflows 
+ module dependency
+ time_scale parameter 
- no meta actions
- no file and system interaction
"""

@wf.Class
class Mesh:
    mesh_step: float
    n_elements: int

@wf.workflow
def make_mesh(mesh_step: float):
    toolbox.print("make_mesh:", mesh_step)
    mesh_size = wf.round(1000 / mesh_step)
    toolbox.sleep(1e-6 * mesh_size)
    return Mesh(mesh_step, mesh_size)

@wf.workflow
def compute(mesh: Mesh, data: float):
    toolbox.print("compute:", mesh.n_elements, data)
    return mesh.n_elements + data

@wf.action_def
def postprocess(mesh: Mesh):
    return mesh.n_elements / 2

@wf.analysis
def mock_workflow():
    data = [3, 1, 2, 5]
    mesh = make_mesh(0.1)
    a = compute(mesh, data[0])
    b = compute(mesh, data[3])
    c = postprocess(mesh)
    return [a, b, c]