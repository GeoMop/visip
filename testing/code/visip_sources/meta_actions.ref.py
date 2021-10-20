import visip as wf


@wf.workflow
def true_body(self):
    Value_1 = 101
    return Value_1


@wf.workflow
def false_body(self):
    Value_1 = 100
    return Value_1


@wf.workflow
def wf_condition(self, cond):
    If_1 = wf.If(condition=cond, true_body=true_body, false_body=false_body)
    return If_1
