"""
Wrap an action instance construction in order to return the constructec ActionInstance be
wrapped into Dummy object.
"""
from typing import Any, Dict
from numpy import array
from common import action_base as base
from common import action_instance as instance
from common.code import dummy



def into_action(value):
    """
    Wrap a value into action.
    :param value: Value can be raw value, List, Tuple, Dummy, etc.
    :return: ActionInstance that can be used as the input to other action instance.
    """
    base_types = [bool, int, float, complex, str, array]
    if value is None:
        return None
    elif isinstance(value, instance.ActionInstance):
        return value
    elif type(value) in base_types:
        return instance.ActionInstance.create(base.Value(value))
    elif type(value) in [tuple, list]:
        wrap_values = [into_action(val) for val in value]
        return instance.ActionInstance.create(base.List(), *wrap_values)
    elif isinstance(value, dummy.Dummy):
        return value._action
    else:
        raise base.ExcActionExpected("Can not wrap into action, value: {}".format(str(value)))


def unwrap_type(value):
    """
    Convert value to a type.
    - unwrap DataClass
    - check that output is a valid type
    TODO: must be called recursively for composed data types or we must define our own typing
    e.g. List[ActionWrapper(Point)]
    :param value:
    :return:
    """
    if isinstance(value, ActionWrapper):
        assert isinstance(value.action, base.ClassActionBase)
        return value.action._data_class

    else:
        return value


def separate_underscored_keys(arg_dict: Dict[str, Any]):
    underscored = {}
    regular = {}
    for key, value in arg_dict.items():
        if dummy.is_underscored(key):
            underscored[key] = value
        else:
            regular[key] = value
    return (regular, underscored)



class ActionWrapper:
    def __init__(self, action):
        assert isinstance(action, base._ActionBase)
        self.action = action
        self.is_analysis = False


    def __call__(self, *args, **kwargs):
        """
        Catch all arguments.
        Separate private params beginning with underscores.
        (Undummy action inputs, wrap non-action inputs)
        Create under laying action, connect to inputs.
        Return action wrapped into the Dummy.
        """
        args = [into_action(arg) for arg in args]
        kwargs = { key: into_action(val) for key, val in kwargs.items() }
        regular_inputs, private_args = separate_underscored_keys(kwargs)
        # print("Instance: ", self.action.name, args, regular_inputs)
        action_instance = instance.ActionInstance.create(self.action, *args, **regular_inputs)
        # TODO: check that inputs are connected.
        # action_instance.set_metadata(private_args)
        return dummy.Dummy.wrap(action_instance)



def public_action(action):
    """
    Decorator makes a wrapper function for an action that should be used explicitelty in workspace.
    A wrapper is called instead of the action constructor in order to:
    1. preprocess arguments
    2. return constructed action wrapped into the Dummy object.
    """
    return ActionWrapper(action)
