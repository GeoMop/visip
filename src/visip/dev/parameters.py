import attr
from typing import *
import inspect

class NoDefault:
    """
    Mark no default value of the parameter.
    Can not use None, as it is valid default value.
    """
    pass


@attr.s(auto_attribs=True)
class ActionParameter:
    """
    Description of a single parameter of a function (action).
    """
    name: str
    # Name of the parameter, None for positional only.
    type: Any = None
    # Type annotation of the parameter (optional).
    default: Any = NoDefault()
    # Default value of the parameter optional
    idx: int = attr.ib(init=False, default=None)
    # Index of the parameter within Parameters.

    def get_default(self) -> Tuple[bool, Any]:
        if not isinstance(self.default, NoDefault):
            return True, self.default
        else:
            return False, None

class Parameters:
    no_default = NoDefault()
    # Single instance object representing no default value.

    def __init__(self):
        self.parameters = []
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
        param.idx = len(self.parameters)
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
    parameters = Parameters()

    for param in signature.parameters.values():
        if skip_self and parameters.size() == 0 and param.name == 'self':
            continue

        annotation = param.annotation if param.annotation != param.empty else None
        default = param.default if param.default != param.empty else None

        if param.kind == param.VAR_POSITIONAL:
            assert default == None
            param = ActionParameter(None, annotation, default)
        else:
            assert param.kind == param.POSITIONAL_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD, str(param.kind)
            param = ActionParameter(param.name, annotation, default)
        parameters.append(param)
    return_type = signature.return_annotation
    return_type = return_type if return_type != signature.empty else None
    return parameters, return_type