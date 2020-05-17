import visip as wf

@wf.workflow
def true_body():
    return 101

@wf.workflow
def false_body():
    return 100


@wf.workflow
def wf_condition(cond: int) -> int:
    return wf.If(cond, true_body, false_body)
