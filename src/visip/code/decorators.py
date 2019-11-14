from ..code import dummy, wrap
from ..dev import base
from ..dev import action_workflow as wf
from ..action import constructor
from ..dev.parameters import ActionParameter, Parameters


class _Variables:
    """
    Helper class to store local variables of the workflow and use
    their names as instance names for the assigned actions, i.e.
    variables.x = action_y(...)
    will set the instance name of 'action_y' to 'x'. This allows to
    use 'x' as the variable name in subsequent code generation. Otherwise
    a Python variable name is not accessible at runtime.
    """
    def __setattr__(self, key, value):
        value = wrap.into_action(value)
        value = value.set_name(key)
        self.__dict__[key] = dummy.Dummy(value)




def workflow(func):
    """
    Decorator to crate a Workflow class from a function.
    """
    workflow_name = func.__name__

    params, output_type = base.extract_func_signature(func, skip_self=False)
    param_names = [param.name for param in params]
    func_args = []
    variables = _Variables()
    if param_names[0] == 'self':
        func_args.append(variables)
        param_names = param_names[1:]

    slots = [wf._SlotCall(name) for i, name in enumerate(param_names)]
    dummies = [dummy.Dummy(slot) for slot in slots]
    func_args.extend(dummies)
    #print(func)
    output_action = wrap.into_action(func(*func_args))
    new_workflow = wf._Workflow(workflow_name)
    new_workflow.set_from_source(slots, output_type, output_action)
    new_workflow._module = func.__module__
    return wrap.public_action(new_workflow)


def analysis(func):
    """
    Decorator for the main analysis workflow of the module.
    """
    w: wrap.ActionWrapper = workflow(func)
    assert isinstance(w.action, wf._Workflow)
    assert len(w.action._slots) == 0
    w.action.is_analysis = True
    return w


def Class(data_class):
    """
    Decorator to convert a data class definition into the constructor action.
    The data_class__annotations__ are converted into Parameters object.

    Usage:
    @Class
    class Point:
        x:float         # attribute with given type
        y:float = 0.0   # attribute with defined type and default value

    The resulting constructor action is wrapped into a function in order to convert passed parameters
    to the connected actions.
    """
    params = Parameters()
    for name, ann in data_class.__annotations__.items():
        attr_type = wrap.unwrap_type(ann)
        attr_default = data_class.__dict__.get(name, params.no_default)
        # Unwrapping of default value and type checking should be part of the Action creation.
        params.append(ActionParameter(name, attr_type, attr_default))
    dataclass_action = constructor.ClassActionBase.construct_from_params(data_class.__name__, params, module=data_class.__module__)
    return wrap.public_action(dataclass_action)



def action(func):
    """
    Decorator to make an action class from the evaluate function.
    Action name is given by the nama of the function.
    Input types are given by the type hints of the function params.
    """
    action_name = func.__name__
    action = base._ActionBase(action_name)
    action._evaluate = func
    return wrap.public_action(action)


