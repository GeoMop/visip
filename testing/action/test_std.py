import os
import visip as wf
from visip.dev import evaluation
script_dir = os.path.dirname(os.path.realpath(__file__))

@wf.action_def
def read_file(input: wf.File) -> int:
    with open(input.path, "r") as f:
        content = f.readlines()
    return len(content)


MY_FILE = "my_file.txt"
WORKSPACE = "_workspace"
@wf.analysis
def my_file_count() -> None:
    return read_file(wf.file_r(MY_FILE, workspace=WORKSPACE))

def test_file():
    print("Root workspace: ", os.getcwd())
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(os.path.join(WORKSPACE, MY_FILE), "w") as f:
        f.write("one\ntwo\nthree")
    result = evaluation.run(my_file_count)
    print(result)
    assert result == 3



@wf.workflow
def system_test_wf(self, script_name: str)  -> wf.ExecResult:
    script = wf.file_r(script_name)
    self.res = wf.system(
        ['echo', "Hallo world"],
        stdout=wf.file_w('msg_file.txt'))
    self.msg_file = wf.file_r('msg_file.txt', self.res.workdir)
    self.res = wf.system(['python', script, "-m", self.msg_file, 123], stdout=wf.SysFile.PIPE, stderr=wf.SysFile.STDOUT)
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
    result = evaluation.run(system_test_wf, [script_name], workspace=script_dir)
    assert result.stdout == b"I'm here.\n"




def test_file_action_skipping():
    # Test that external operations are skipped once files are the same
    pass
