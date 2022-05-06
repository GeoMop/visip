import visip as wf
import toolbox  # visip module
"""
Simple analysis:
+ several interconnected workflows 
+ module dependency
+ time_scale parameter 
- no meta actions
- no file and system interaction
"""

@wf.workflow
def make_mesh(mesh_step: float):
    mesh_size = 1000 / mesh_step
    toolbox.sleep(1e-6 * mesh_size)
    return mesh_size

@wf.workflow
def compute(mesh: float, data: float):
    return



@wf.analysis
def mock_workflow():
    data = [3, 1, 2, 5]
    mesh = make_mesh(0.1)
    a = compute(mesh, data[0])
    b = compute(mesh, data[3])
    return [a, b]