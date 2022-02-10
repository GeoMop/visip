import inspect
from .type_inspector import TypeInspector
from . parameters import Parameters, ActionParameter
from .exceptions import ExcTypeBase
from ..code.dummy import DummyAction
from ..dev import dtype_new


def unwrap_type(type_hint):
    """
    Remove DummyAction from (class) types.
    :param type_hint: Python annotation or DummyAction
    :return:
    """
    ti = TypeInspector()
    if isinstance(type_hint, DummyAction):
        constructor_action = type_hint._action_value
        data_class = constructor_action._data_class
        type_hint = data_class
        #assert isinstance(action_call, ActionCall)

    if type_hint == ActionParameter.no_default:
        return None
    elif type_hint is None:
        return None   #raise TypeError("Type annotation is required.")
    #elif type_hint is type(None):
    #    return None
    elif isinstance(type_hint, dtype_new.DTypeBase):
        return type_hint
    elif isinstance(type_hint, dtype_new.DTypeGeneric):
        args = type_hint.get_args()
        if args:
            # Is a generic, process its parameters recursively.
            uargs = tuple(unwrap_type(arg) for arg in args)
            typing_origin = type(type_hint)
            return typing_origin(*uargs)
        else:
            raise ExcTypeBase(f"Unknown type annotation: {type_hint}")



def _parameter_from_inspect(param: inspect.Parameter) -> 'ActionParameter':
    assert param.annotation is not None
    param_type = unwrap_type(dtype_new.from_typing(param.annotation))
    return ActionParameter(param.name, param_type, param.default, param.kind)


def _check_type_var(parameters):
    in_set = set()
    for param in parameters.parameters:
        in_set.update(dtype_new.extract_type_var(param.type))
    out_set = dtype_new.extract_type_var(parameters.return_type)
    assert out_set.issubset(in_set), "All TypeVars at output there are not also at input."


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
    return_type = unwrap_type(dtype_new.from_typing(signature.return_annotation))
    parameters = Parameters(params, return_type , had_self)
    _check_type_var(parameters)
    return parameters

