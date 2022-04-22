import inspect
from . parameters import Parameters, ActionParameter
from ..dev import dtype





def _parameter_from_inspect(param: inspect.Parameter) -> 'ActionParameter':
    assert param.annotation is not None
    param_type = dtype.from_typing(param.annotation)
    default =  ActionParameter.no_default if param.default is inspect.Signature.empty else param.default
    return ActionParameter(param.name, param_type, default, param.kind)


def _extract_signature(func, omit_self=False):
    """
    Inspect function signature and extract parameters, their types and return type.
    :param func: Function to inspect.
    :param skip_self: Skip first parameter if its name is 'self'.
    :return:
    """
    signature = inspect.signature(func)
    params = []
    had_self = False
    for i, param in enumerate(signature.parameters.values()):
        if omit_self and i == 0 and param.name == 'self':
            had_self = True
            continue
        params.append(_parameter_from_inspect(param))
    #assert signature.return_annotation is not None
    return_type = dtype.from_typing(signature.return_annotation)
    parameters = Parameters(params, return_type , had_self)
    parameters.check_type_vars()
    # TODO: move this check possibly to ActionBase, not needed for Workflow
    return parameters

