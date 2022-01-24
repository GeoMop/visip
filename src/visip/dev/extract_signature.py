import inspect
from .type_inspector import TypeInspector
from . parameters import Parameters, ActionParameter
from .exceptions import ExcTypeBase
from ..code.dummy import DummyAction
from ..dev import dtype


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
    elif ti.is_any(type_hint):
        return type_hint
    elif ti.is_base_type(type_hint):
        return type_hint
    elif ti.is_dataclass(type_hint):
        return type_hint
    elif ti.is_newtype(type_hint):
        return type_hint
    else:
        args = ti.get_args(type_hint)
        if args:
            # Is a generic, process its parameters recursively.
            uargs = tuple(unwrap_type(arg) for arg in args)
            typing_origin = ti.get_typing_origin(type_hint)
            return typing_origin[uargs]
        else:
            raise ExcTypeBase(f"Unknown type annotation: {type_hint}")



def _parameter_from_inspect(param: inspect.Parameter) -> 'ActionParameter':
    param_type = unwrap_type(param.annotation)
    return ActionParameter(param.name, param_type, param.default, param.kind)

def _extract_signature(func, omit_self=False):
    """
    Inspect function signature and extract parameters, their types and return type.
    :param func: Function to inspect.
    :param skip_self: Skip first parameter if its name is 'self'.
    :return:
    """
    signature = inspect.signature(func)
    params = [_parameter_from_inspect(param) for param in signature.parameters.values()]
    had_self = False
    if omit_self and params and params[0].name == 'self':
        params = params[1:]
        had_self = True
    return_type = unwrap_type(signature.return_annotation)
    return Parameters(params, return_type , had_self)

