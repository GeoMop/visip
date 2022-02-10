import enum
import inspect
import typing
import attr
#from ..code import wrap
from ..dev import dtype_new
from ..dev import base
from ..dev import action_workflow as wf
from ..action import constructor
from ..action.action_factory import ActionFactory
from ..dev.extract_signature import unwrap_type, _extract_signature, ActionParameter
from ..dev import exceptions
from .dummy import DummyAction, Dummy

def public_action(action: base._ActionBase):
    """
    Decorator makes a wrapper function for an action that should be used explicitly in a workflow.
    A wrapper is called instead of the action constructor in order to:
    1. preprocess arguments
    2. return constructed ActionCall wrapped into a Dummy object.
    :param action: Instance of _ActionBase.
    """

    return DummyAction(ActionFactory.instance(), action)



def workflow(func) -> DummyAction:
    """
    Decorator to crate a Workflow class from a function.
    """
    new_workflow = wf._Workflow.from_source(func)
    return public_action(new_workflow)


def analysis(func):
    """
    Decorator for the main analysis workflow of the module.
    """
    w: DummyAction = workflow(func)
    assert isinstance(w._action_value, wf._Workflow)
    workflow_action = w._action_value
    assert len(workflow_action._slots) == 0
    workflow_action.is_analysis = True
    return w


def _dataclass_from_params(name: str, params: typing.List[ActionParameter], module=None):
    attributes = {}
    for param in params:
        attributes[param.name] = attr.ib(default=param.default, type=param.type)
    # 'yaml_tag' is not processed by attr.s and thus ignored by visip code representer.
    # however it allows correct serialization to yaml
    # Note: replaced by the DataClassBase classproperty 'yaml_tag'.
    #attributes['yaml_tag'] = u'!{}'.format(name)
    data_class = type(name, (dtype_new.DataClassBase,), attributes)
    if module:
        data_class.__module__ = module

    return attr.s(data_class)


def _construct_from_params(name: str, params: typing.List[ActionParameter], module=None):
    """
    Use Params to consturct the data_class and then instance of ClassActionBase.
    :param name: name of the class
    :param params: instance of Parameters
    :return:
    """
    data_class = _dataclass_from_params(name, params, module)
    signature = _extract_signature(data_class.__init__, omit_self=True)
    return constructor.ClassActionBase(data_class, signature)

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
    params = []
    for name, ann in data_class.__annotations__.items():
        try:
            attr_type = unwrap_type(ann)
        except exceptions.ExcTypeBase:
            raise exceptions.ExcNoType(
                f"Missing type for attribute '{name}' of the class '{data_class.__name__}'.")
        attr_default = data_class.__dict__.get(name, ActionParameter.no_default)
        # Unwrapping of default value and type checking should be part of the Action creation.
        params.append(ActionParameter(name, attr_type, attr_default))
    dataclass_action = _construct_from_params(data_class.__name__, params, module=data_class.__module__)
    dataclass_action.__module__ = data_class.__module__
    return public_action(dataclass_action)

def Enum(enum_cls):
    items = {key: val for key,val in inspect.getmembers(enum_cls) if not key.startswith("__") and not key.endswith("__")}
    int_enum_cls = enum.IntEnum(enum_cls.__name__, items)
    def code(self, representer):
        enum_base, key = str(self).split('.')
        enum_base = representer.make_rel_name(enum_cls.__module__, enum_base)
        return '.'.join([enum_base, key])
    int_enum_cls.__code__ = code
    int_enum_cls.__module__ = enum_cls.__module__
    return int_enum_cls


def action_def(func):
    """
    Decorator to make an action class from the evaluate function.
    Action name is given by the nama of the function.
    Input types are given by the type hints of the function params.
    """
    try:
        signature = _extract_signature(func)
    except exceptions.ExcTypeBase as e:
        raise exceptions.ExcTypeBase(f"Wrong signature of action:  {func.__module__}.{func.__name__}") from e
    action_name = func.__name__
    action_module = func.__module__  # attempt to fix imported modules, but it brakes chained (successive) imports
    action = base._ActionBase(action_name, signature)
    action.__module__ = func.__module__
    action.__name__ = func.__name__
    action._evaluate = func
    return public_action(action)




