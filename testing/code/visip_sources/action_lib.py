import visip as wf

@wf.action_def
def add_float(a:float, b:float) -> float:
    return a + b