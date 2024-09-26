import pytest
import time
import visip.eval.process_worker as pw


class MyWorker:
    """
    Worker with some permanent context.
    In VISIP:
    - imported main script module
    - cache (in future)
    """
    def __init__(self, ctx_info:str):
        self.prefix = ctx_info

    def eval(self, all_args):
        module, action, *args = all_args
        return f"{self.prefix} {module}.{action}{tuple(args)}"

#@pytest.mark.skip
def test_worker():
    proc = pw.WorkerProxy(MyWorker, ("A:",))
    proc.put( ("std", "system", "my_script", 1) )
    assert proc.n_assigned == 1 and proc.n_finished == 0
    proc.put( ("std", "system", "my_script", 2) )
    assert proc.n_assigned == 2 and proc.n_finished == 0
    assert proc.get() == None
    finished = []
    n_iter = 0
    while len(finished) < 2 and n_iter < 10:
        n_iter += 1
        r = proc.get()
        if r is None:
            time.sleep(0.1)
            print("No data")
            continue
        if r.error is None:
            finished.append(r)
        else:
            raise r.error

    assert proc.n_assigned == 2 and proc.n_finished == 2
    assert finished[0].id == 0
    assert finished[0].value == "A: std.system('my_script', 1)"
    assert finished[1].id == 1
    assert finished[1].value == "A: std.system('my_script', 2)"
    proc.close()

#@pytest.mark.skip
def test_preliminary_close():
    proc = pw.WorkerProxy(MyWorker, ("A:",))
    proc.put( ("std", "system", "my_script", 1) )
    proc.close()


class ErrWorker:
    def eval(self, all_args):
        raise ValueError("Intentional error")

#@pytest.mark.skip
def test_exception_construct():
    proc = pw.WorkerProxy(ErrWorker, ("A:",))
    proc.put(("std", "system", "my_script", 1))

#@pytest.mark.skip
def test_exception_eval():
    proc = pw.WorkerProxy(ErrWorker, tuple())
    proc.put(("std", "system", "my_script", 1))
    proc.close()
