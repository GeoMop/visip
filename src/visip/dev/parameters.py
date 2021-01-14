import attr
from typing import *
import inspect

from . import data

class NoDefault:
    """
    Mark no default value of the parameter.
    Can not use None, as it is valid default value.
    In order to make various comparisons consistent we need a single instance of this class.
    """
    pass


# @attr.s(auto_attribs=True)
# class ConfigDefault:
#     """
#     Mark a configuration parameter, that must be provided as a constant.
#     """
#     value: Any
#     # Optional default value of the configuration parameter.


@attr.s(auto_attribs=True, repr=False)
class ActionParameter:
    """
    Description of a single parameter of a function (action).
    """
    no_default = NoDefault()
    # Class attribute. Single instance object representing no default value.

    name: str
    # Name of the parameter, None for positional only.
    type: Any = None
    # Type annotation of the parameter (optional).
    default: Any = no_default
    # Default value of the parameter.
    # NoDefault
    # Indicates that the parameter must be constant wrapped into Value action.
    # Convention: Config parameters should be placed before other parameters since
    # they are part of the action specification.

    _idx: int = attr.ib(init=False, default=None)
    # Index of the parameter within Parameters.
    config_param: bool = False

    @property
    def idx(self):
        # Enforce the parameter index to be read-only.
        return self._idx

    def get_default(self) -> Tuple[bool, Any]:
        if not isinstance(self.default, NoDefault):
            return True, self.default
        else:
            return False, None

    def hash(self):
        p_hash = data.hash(self.name)
        # TODO: possibly remove type spec from hashing, as it doesn't influance evaluation
        p_hash = data.hash(str(self.type), previous=p_hash)
        p_hash = data.hash(self.default, previous=p_hash)
        p_hash = data.hash(self._idx, previous=p_hash)
        p_hash = data.hash(self.config_param, previous=p_hash)
        return p_hash

class Parameters:
    no_default = ActionParameter.no_default
    # For convenience when operating on the Parameters instance.

    def __init__(self):
        self.parameters: List[ActionParameter] = []
        # List of Action Parameters
        self._name_dict = {}
        # Map names to parameters.
        self._variable = False
        # indicates variable number of parameters, the last param have None name



    def is_variadic(self):
        return self._variable

    def size(self):
        return len(self.parameters)

    def append(self, param : ActionParameter):
        assert not self._variable, "Duplicate definition of variadic parameter."
        if param.name is None:
            self._variable = True
        else:
            assert param.name not in self._name_dict
            self._name_dict[param.name] = param
        param._idx = len(self.parameters)
        self.parameters.append(param)


    def get_name(self, name):
        return self._name_dict.get(name, None)


    def get_index(self, idx):
        if idx >= len(self.parameters):
            if self._variable:
                return self.parameters[-1]
            else:
                return None
        return self.parameters[idx]


    def __iter__(self):
        """
        Iter protocol just iterate over parameters.
        :return:
        """
        return iter(self.parameters)


def extract_func_signature(func, skip_self=True):
    """
    Inspect function signature and extract parameters, their types and return type.
    :param func: Function to inspect.
    :param skip_self: Skip first parameter if its name is 'self'.
    :return:
    """
    signature = inspect.signature(func)
    no_value = inspect.Parameter.empty
    parameters = Parameters()

    for param in signature.parameters.values():
        if parameters.size() == 0 and param.name == 'self':
            if skip_self:
                continue
            else:
                annotation = None
                default = ActionParameter.no_default
        else:

            annotation = param.annotation if param.annotation != no_value else None
            default = param.default if param.default != no_value else ActionParameter.no_default

        if param.kind == param.VAR_POSITIONAL:
            assert default == ActionParameter.no_default
            param = ActionParameter(None, annotation, default)
        else:
            assert param.kind == param.POSITIONAL_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD, str(param.kind)
            param = ActionParameter(param.name, annotation, default)
        parameters.append(param)
    return_type = signature.return_annotation if signature.return_annotation != no_value else None

    return parameters, return_type
