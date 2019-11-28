"""
Implementation of meta actions other then Workflow.

We need syntax for inline workflow definitions.

Like Lambda(x=a, y=b, x[0] + y[1])

result = If(cond, true_res, false_res)
# possibly detect expressions as minimum independent chains

result = If(cond, true_wf, false_wf)(input)

While(body_


"""
from . import base

class MetaAction(base._ActionBase):
    """
    Common ancestor of the meta actions.
    """
    def __init__(self, name):
        super().__init__(name)

        self.task_type = base.TaskType.Composed
        # Task type determines how the actions are converted to the tasks.
        # Composed tasks are expanded.

    def expand(self, inputs, task_creator):
        assert False, "Missing definition."


class If(MetaAction):
    """
    This possibly should not be meta action, since scheduler should
    How to inform scheduler, that evaluaation of the condition hve higher priority
    then the true and false inputs?
    """

class While(MetaAction):
    def __init__(self):

    def expand(self, ):