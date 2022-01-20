from ..dev.base import _ActionBase
from ..dev.action_instance import ActionCall
from ..dev.exceptions import ExcActionExpected
from ..action import constructor
from .dummy import Dummy, DummyAction
from ..dev.type_inspector import  TypeInspector


def into_action(value):
    """
    Wrap a value into action.
    :param value: Value can be raw value, List, Tuple, Dummy, etc.
    :return: ActionInstance that can be used as the input to other action instance.
    """
    ti = TypeInspector()

    if value is None:
        return None


    if isinstance(value, ActionCall):
        return value
    elif ti.is_base_type(type(value)) or ti.is_enum(type(value)):
        return ActionCall.create(constructor.Value(value))
    elif type(value) is list:
        wrap_values = [into_action(val) for val in value]
        return ActionCall.create(constructor.A_list(), *wrap_values)
    elif type(value) is tuple:
        wrap_values = [into_action(val) for val in value]
        return ActionCall.create(constructor.A_tuple(), *wrap_values)
    elif type(value) is dict:
        wrap_values = [into_action((key, val)) for key, val in value.items()]
        return ActionCall.create(constructor.A_dict(), *wrap_values)
    elif isinstance(value, Dummy):
        action_call = value._value
        assert isinstance(action_call, ActionCall)
        return action_call
    elif isinstance(value, DummyAction):
        action = value._action_value
        assert isinstance(action, _ActionBase)
        return ActionCall.create(constructor.Value(action))
    else:
        raise ExcActionExpected("Can not wrap into action, value: {}".format(str(value)))
