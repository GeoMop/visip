import inspect
import indexed
import enum
import attr
import pytypes
from typing import *
from collections import defaultdict
from common import data
from common import task
from common.code import format

# Name for the first parameter of the workflow definiton function that is used
# to capture instance names.
_VAR_ = "self"


class ExcMissingArgument(Exception):
    pass


class ExcActionExpected(Exception):
    pass


class ExcTooManyArguments(Exception):
    pass


class ExcUnknownArgument(Exception):
    pass


class ExcDuplicateArgument(Exception):
    pass


class NoDefault:
    pass


@attr.s(auto_attribs=True)
class ActionParameter:
    idx: int
    name: str
    type: Any = None
    default: Any = NoDefault()

    def get_default(self) -> Tuple[bool, Any]:
        if not isinstance(self.default, NoDefault):
            return True, self.default
        else:
            return False, None


class Parameters:
    def __init__(self):
        self.parameters = []
        # List of Action Parameters
        self._name_dict = {}
        # Map names to parameters.
        self._variable = False
        # indicates variable number of parameters, the last param have None name
        self.no_default = NoDefault()

    def is_variadic(self):
        return self._variable

    def size(self):
        return len(self.parameters)

    def append(self, param: ActionParameter):
        assert not self._variable, "Duplicate definition of variadic parameter."
        if param.name is None:
            self._variable = True
        else:
            assert param.name not in self._name_dict
            self._name_dict[param.name] = param
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
        idx = parameters.size()
        if skip_self and idx == 0 and param.name == 'self':
            continue

        annotation = param.annotation if param.annotation != param.empty else None
        default = param.default if param.default != param.empty else None

        if param.kind == param.VAR_POSITIONAL:
            assert default == None
            param = ActionParameter(idx, None, annotation, default)
        else:
            assert param.kind == param.POSITIONAL_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD, str(param.kind)
            param = ActionParameter(idx, param.name, annotation, default)
        parameters.append(param)
    return_type = signature.return_annotation
    return_type = return_type if return_type != signature.empty else None
    return parameters, return_type


class _ActionBase:
    """
    Base of all actions.
    - have defined parameters
    - have defined output type
    - implement expansion to the Task DAG.
    - have _code representation
    """

    def __init__(self, action_name=None):
        self.task_class = task.Atomic
        self.is_analysis = False
        self.name = action_name or self.__class__.__name__
        self._module = "wf"
        # Module where the action is defined.
        self.parameters = Parameters()
        # Parameter specification list, class attribute, no parameters by default.
        self.output_type = None
        # Output type of the action, class attribute.
        # Both _parameters and _outputtype can be extracted from type annotations of the evaluate method using the _extract_input_type.
        self._extract_input_type()

    @property
    def module(self):
        if self._module:
            return self._module
        else:
            return self.__module__

    def _extract_input_type(self, func=None, skip_self=True):
        """
        Extract input and output types of the action from its evaluate method.
        Only support fixed numbeer of parameters named or positional.
        set: cls._input_type, cls._output_type
        """
        if func is None:
            func = self._evaluate
        self.parameters, self.output_type = extract_func_signature(func, skip_self)
        pass

    def hash(self):
        """
        Hash of the atomic action. Should be unique for the particular Action instance.
        """
        return data.hash(self.name)

    def evaluate(self, inputs):
        """
        Common evaluation function for all actions.
        Call _evaluate which actually implements the action.
        :param inputs: List of arguments.
        :return: action result
        """
        return self._evaluate(*inputs)

    def _evaluate(self):
        """
        Pure virtual method.
        If the validate method is defined it is used for type compatibility validation otherwise
        this method must handle both a type tree and the data tree on the input
        returning the appropriate output type tree or the data tree respectively.
        :param inputs: List of actual inputs. Same order as the action arguments.
        :return:
        """
        assert False, "Implementation has to be provided."

    def format(self, full_action_name, arg_names):
        """
        Return a format string for the expression that constructs the action.
        :param n_args: Number of arguments, number of placeholders. Can be None if the action is not variadic.
        :return: str, format
        Format contains '{N}' placeholders for the given N-th argument, the named placeholer '{VAR}'
        is used for the variadic arguments, these are substituted as an argument list separated by comma and space.
        E.g. "Action({0}, {1}, {})" can be expanded to :
        "Action(arg0, arg1, arg2, arg3)"
        """
        args = []
        for i, arg in enumerate(arg_names):
            param = self.parameters.get_index(i)
            assert param is not None
            args.append((param.name, arg))
        return format.Format.action_call(full_action_name, args)

    def validate(self, inputs):
        return self.evaluate(inputs)


class Value(_ActionBase):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def hash(self):
        return data.hash(self.value)

    def _evaluate(self):
        return self.value

    def format(self, action_name, arg_names):
        value = self.value
        if type(value) is str:
            expr = "'{}'".format(value)
        else:
            expr = str(value)

        return format.Format([expr])


class Pass(_ActionBase):
    """
    Do nothing action. Meant for internal usage in particular.
    """

    def __init__(self):
        super().__init__()

    def _evaluate(self, input: data.DataType):
        return input


class _ListBase(_ActionBase):

    # We assume that parameters are used only in reinit, which do not use it
    # in this case. After reinit one should use only self.arguments.

    def __init__(self):
        super().__init__()
        self.parameters = Parameters()
        self.parameters.append(ActionParameter(idx=0, name=None, type=Any, default=self.parameters.no_default))


# class Tuple(_ListBase):
#     #__action_parameters = [('input', 'Any')]
#     """ Merge any number of parameters into tuple."""
#     def _code(self):
#         return self._code_with_brackets(format = "({})")
#
#     def evaluate(self, inputs):
#         return tuple(inputs)


class List(_ListBase):
    def format(self, action_name, arg_names):
        return format.Format.list("[", "]", [(None, arg) for arg in arg_names])

    def evaluate(self, inputs):
        return list(inputs)


class ClassActionBase(_ActionBase):
    """
    Dataclass action
    """

    def __init__(self, data_class):
        super().__init__(data_class.__name__)
        self._data_class = data_class
        self._module = self._data_class.__module__
        self._extract_input_type(func=data_class.__init__, skip_self=True)

    @staticmethod
    def construct_from_params(name: str, params: Parameters):
        """
        Use Params to consturct the data_class and then instance of ClassActionBase.
        :param name:
        :param params:
        :return:
        """
        attributes = {}
        for param in params:
            attributes[param.name] = attr.ib(default=param.default, type=param.type)
        data_class = type(name, (data.DataClassBase,), attributes)
        data_class = attr.s(data_class)
        return ClassActionBase(data_class)

    @property
    def constructor(self):
        return self._data_class

    def _evaluate(self, *args) -> data.DataClassBase:
        return self._data_class(*args)

    def code_of_definition(self, make_rel_name):
        lines = ['@wf.Class']
        lines.append('class {}:'.format(self.name))
        for attribute in self._data_class.__attrs_attrs__:
            if attribute.type:
                type_str = make_rel_name(attribute.type.__module__, attribute.type.__name__)
            else:
                type_str = "Any"

            if attribute.default == attr.NOTHING:
                default = ""
            else:
                default = "={}".format(attribute.default)
            lines.append("    {}:{}{}".format(attribute.name, type_str, default))

        return "\n".join(lines)
