import os
import shutil
import visip.dev.tools as tools
import visip as wf
from visip.dev import evaluation
script_dir = os.path.dirname(os.path.realpath(__file__))



def eval():
    return evaluation.Evaluation(workspace=script_dir)


def test_Len():
    result = eval().run(wf.Len, [1,2,3])
    assert result.result == 3
    result = eval().run(wf.Len, [])
    assert result.result == 0
    result = eval().run(wf.Len, {1:1,2:1})
    assert result.result == 2

def test_Append():
    x = [1,2,3]
    result = eval().run(wf.Append, x, 4)
    assert result.result == [1,2,3,4]
    result = eval().run(wf.Append, [], 4)
    assert result.result == [4]


@wf.action_def
def read_file(input: wf.FileIn) -> int:
    with open(input.path, "r") as f:
        content = f.readlines()
    return len(content)


MY_FILE = "my_file.txt"
WORKSPACE = "_workspace"
@wf.analysis
def my_file_count() -> int:
    return read_file(wf.file_in(MY_FILE, workspace=WORKSPACE))

def test_file():
    print("Root workspace: ", os.getcwd())
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(os.path.join(WORKSPACE, MY_FILE), "w") as f:
        f.write("one\ntwo\nthree")
    result = evaluation.run(my_file_count)
    # print(result)
    assert result == 3



@wf.workflow
def system_test_wf(self, script_name: str)  -> wf.ExecResult:
    script = wf.file_in(script_name)
    self.msg = wf.system(
        ['echo', "Hallo world"],
        stdout=wf.file_out('msg_file.txt'))
    self.msg_file = wf.file_in('msg_file.txt', self.msg.workdir)
    self.res = wf.system(['python', script, "-m", self.msg_file, "123"], stdout=wf.SysFile.PIPE, stderr=wf.SysFile.STDOUT)
    return self.res

def test_system():
    """
    Test system action with mock command.
    :return:
    """
    try:
        os.remove(os.path.join(script_dir, "msg_file.txt"))
    except FileNotFoundError:
        pass

    print("Root workspace: ", os.getcwd())
    script_name = "_mock_script_test_system.py"
    result = eval().run(system_test_wf, script_name).result
    assert result.stdout == b"I'm here.\n"


def prepare_workspace_template():
    with tools.change_cwd(script_dir):
        shutil.rmtree("_workspace", ignore_errors=True)
        os.makedirs("_workspace")
        shutil.copyfile(os.path.join("inputs", "darcy_flow.yaml.tmpl"),
                        os.path.join("_workspace", "darcy_flow.yaml.tmpl"))

    print("Root workspace: ", os.getcwd())


def test_file_from_template():
    prepare_workspace_template()
    result = eval().run(wf.file_from_template,
                            wf.file_in('_workspace/darcy_flow.yaml.tmpl'),
                            dict(MESH='my_mesh.msh')).result

    with open(os.path.join(script_dir, "_workspace", "darcy_flow.yaml"), "r") as f:
        content = f.read()
    assert content.find('my_mesh.msh')

@wf.analysis
def my_mesh_yaml():
    return wf.file_from_template(wf.file_in('_workspace/darcy_flow.yaml.tmpl'), dict(MESH='my_mesh.msh'))


def test_file_from_template_wf():
    prepare_workspace_template()
    result = eval().run(my_mesh_yaml).result
    with open(os.path.join(script_dir, "_workspace", "darcy_flow.yaml"), "r") as f:
        content = f.read()
    assert content.find('my_mesh.msh')


def test_file_action_skipping():
    # Test that external operations are skipped once files are the same
    pass
