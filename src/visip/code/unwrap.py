from ..dev.action_instance import ActionCall
from typing import Any

def action_wrap(v):
    return ActionCall.action_wrap(v)

def into_action(value: Any) -> ActionCall:
    """
    In value remove recursively all Dummy and DummyAction wrappers.
    Convert all list, dict, tuple, dataclass having at leas one ActionCall
    argument into appropriate constructor actions.
    Wrap data values (without any action calls) into Value action.
    Wrap the None value as well.
    Return the ActionCall.

    :param value: Value can be raw value, List, Tuple, Dummy, etc.
    :return: ActionCall that can be used as the input to other action instance.
    """
    return ActionCall.into_action(value)
