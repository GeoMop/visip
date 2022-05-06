import os
import pytest
import subprocess
script_dir = os.path.dirname(os.path.realpath(__file__))

@pytest.mark.parametrize("env", [
    "local.yaml",
    "multiprocess.yaml"])
@pytest.mark.parametrize("case", [
    "simple.py"])
def test_visip_command(env, case):
    visip_cmd = os.path.join(script_dir, "../../bin/visip")
    env_path = os.path.join(script_dir, "env", env)
    case_path = os.path.join(script_dir, "sources", case)
    result = subprocess.run(["python3", visip_cmd, env_path, case_path])
    assert result.returncode == 0