import enum
import inspect
import typing
import attr
#from ..code import wrap
from ..dev import dtype
from ..dev.base import ActionBase
from ..dev import action_workflow as wf
from ..action import constructor
# from ..dev.parameters import ActionParameter, Parameters
# from ..dev import exceptions, dtype_new
from ..action.action_factory import ActionFactory
from ..dev.extract_signature import _extract_signature, ActionParameter
from ..dev.parameters import Parameters
from ..dev import exceptions
from .dummy import DummyAction, Dummy, DummyWorkflow


def public_action(action: dtype._ActionBase):
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
    return DummyWorkflow(ActionFactory.instance(), func)


def analysis(func):
    """
    Decorator for the main analysis workflow of the module.
    """
    w: DummyWorkflow = workflow(func)
    # analysis have no parameters so it can not be resursive
    # we make workflow instance.
    wflow = w.workflow
    assert isinstance(wflow, wf._Workflow)
    assert len(wflow._slots) == 0
    wflow.is_analysis = True
    return w


def _dataclass_from_params(name: str, params: typing.List[ActionParameter], module=None):
    attributes = {}
    for param in params:
        attributes[param.name] = attr.ib(default=param.default, type=param.type)
    # 'yaml_tag' is not processed by attr.s and thus ignored by visip code representer.
    # however it allows correct serialization to yaml
    # Note: replaced by the DataClassBase classproperty 'yaml_tag'.
    #attributes['yaml_tag'] = u'!{}'.format(name)
    data_class = type(name, (dtype.DataClassBase,), attributes)
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
    signature_with_return_type = Parameters(params, return_type=dtype.from_typing(data_class))
    return constructor.ClassActionBase(data_class, signature_with_return_type)

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
        attr_type = dtype.from_typing(ann)
        if attr_type is dtype.EmptyType:
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
    int_enum_cls.__module__ = enum_cls.__module__
    enum_action = constructor.EnumActionBase(int_enum_cls)
    enum_action.__module__ = int_enum_cls.__module__
    return public_action(enum_action)


def action_def(func):
    """
    Decorator to make an action class from the evaluate function.
    Action name is given by the nama of the function.
    Input types are given by the type hints of the function params.
    """

    signature = _extract_signature(func)
    try:
        signature.process_empty(lambda var: dtype.Any)
    except exceptions.ExcNoType as e:
        raise exceptions.ExcNoType(f"Wrong signature of action:  {func.__module__}.{func.__name__}") from e

    action_name = func.__name__
    action_module = func.__module__  # attempt to fix imported modules, but it brakes chained (successive) imports
    action = ActionBase(action_name, signature)
    action.__module__ = func.__module__
    action.__name__ = func.__name__
    action._evaluate = func
    return public_action(action)




