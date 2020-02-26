"""
Wrap an action instance construction in order to return the constructec ActionInstance be
wrapped into Dummy object.
"""
import typing
import typing_inspect as ti


from ..dev import dtype as dtype
from ..dev import base
from ..action import constructor
from ..dev import action_instance as instance
from . import dummy


def into_action(value):
    """
    Wrap a value into action.
    :param value: Value can be raw value, List, Tuple, Dummy, etc.
    :return: ActionInstance that can be used as the input to other action instance.
    """
    ti = dtype.TypeInspector()
    if value is None:
        return None
    elif isinstance(value, instance.ActionCall):
        return value
    elif ti.is_base_type(type(value)) or ti.is_enum(type(value)):
        return instance.ActionCall.create(constructor.Value(value))
    elif type(value) is list:
        wrap_values = [into_action(val) for val in value]
        return instance.ActionCall.create(constructor.A_list(), *wrap_values)
    elif type(value) is tuple:
        wrap_values = [into_action(val) for val in value]
        return instance.ActionCall.create(constructor.A_tuple(), *wrap_values)
    elif type(value) is dict:
        wrap_values = [into_action((key, val)) for key, val in value.items()]
        return instance.ActionCall.create(constructor.A_dict(), *wrap_values)
    elif isinstance(value, dummy.Dummy):
        return value._action_call
    else:
        raise base.ExcActionExpected("Can not wrap into action, value: {}".format(str(value)))



def unwrap_type(type_hint):
    """
    Remove ActionWrapper from (class) types.
    :param type_hint:
    :return:
    """
    ti = dtype.TypeInspector()
    if isinstance(type_hint, ActionWrapper):
        assert isinstance(type_hint.action, constructor.ClassActionBase)
        data_type = type_hint.action._data_class
        assert ti.is_dataclass(data_type)
        return data_type

    if type_hint is None:
        raise TypeError("Type annotation is required.")
    elif type_hint is type(None):
        return type_hint
    elif ti.is_any(type_hint):
        return type_hint
    elif ti.is_base_type(type_hint):
        return type_hint
    elif ti.is_dataclass(type_hint):
        return type_hint
    else:
        args = ti.get_args(type_hint)
        if args:
            uargs = tuple(unwrap_type(arg) for arg in args)
            typing_origin = ti.get_typing_origin(type_hint)
            return typing_origin[uargs]
        else:
            print("Can not unwrap the type_hint: {}"
                  .format(type_hint))


def separate_underscored_keys(arg_dict: typing.Dict[str, typing.Any]):
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
        action_instance = instance.ActionCall.create(self.action, *args, **regular_inputs)
        # TODO: check that inputs are connected.
        # action_instance.set_metadata(private_args)
        return dummy.Dummy.wrap(action_instance)

    def call(self,  *args):
        """
        Call an action from an action_def, i.e. regular Python function.
        :param args:
        :param kwargs:
        :return:
        """
        # TODO: assert for arguments types
        return self.action.evaluate(args)

def public_action(action):
    """
    Decorator makes a wrapper function for an action that should be used explicitelty in workspace.
    A wrapper is called instead of the action constructor in order to:
    1. preprocess arguments
    2. return constructed action wrapped into the Dummy object.
    """

    return ActionWrapper(action)

