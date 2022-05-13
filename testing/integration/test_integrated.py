import os
import pytest
import subprocess
from multiprocessing import Pool

script_dir = os.path.dirname(os.path.realpath(__file__))

#@pytest.mark.skip
@pytest.mark.parametrize("env", [
    "local.yaml",
    "multiprocess.yaml"])
#@pytest.mark.parametrize("env", [
#    "multiprocess.yaml"])
@pytest.mark.parametrize("case", [
    "simple.py"])
def test_visip_command(env, case):
    visip_cmd = os.path.join(script_dir, "../../bin/visip")
    env_path = os.path.join(script_dir, "env", env)
    case_path = os.path.join(script_dir, "sources", case)
    result = subprocess.run(["python3", visip_cmd, env_path, case_path])
    assert result.returncode == 0

class Base:
    @classmethod
    def inc_c(cls, a):
        return a + 1

class Wrapper(Base):

    @staticmethod
    def inc(a):
        return a + 1

    def inc1(self, a):
        return a + 1

    @classmethod
    def inc_c(cls, a):
        return a + 1

class Resource:
    def __init__(self):
        self.finished=[]
    def add_finished(self, res, task):
        self.finished.append((res, task))

@pytest.mark.skip
def test_multiprocess():
    pool = Pool(processes=2)
    w = Wrapper()
    resource = Resource()

    #results = []
    #calls = []
    def finished(res):
        resource.add_finished(res, w)


    fn = w.inc1
    for x in (1, 2):
        pool.apply_async(fn, (x,), callback=finished)
        #calls.append(call)
        #results.append(r)

    while len(resource.finished) < 2:
        pass
        # for i, c in enumerate(calls):
        #     if c.ready():
        #         print("ready:", i)

    print()
    print(resource.finished)
    pool.close()

if __name__ == "__main__":
    test_visip_command("multiprocess.yaml", "simple.py")