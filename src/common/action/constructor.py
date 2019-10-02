import attr
import typing

from ..dev.base import _ActionBase
from ..dev.list_base import _ListBase
from ..evaluation import data
from ..dev.parameters import Parameters, ActionParameter


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
    Action constructs particular Dataclass given in constructor.
    So the action is parametrized by the 'data_class'.
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


    def code_of_definition(self, make_rel_name, representer):
        lines = ['@wf.Class']
        lines.append('class {}:'.format(self.name))
        for attribute in self._data_class.__attrs_attrs__:
            if attribute.type:
                type_code = representer.type_code(attribute.type)
                type_str = make_rel_name(attribute.type.__module__, type_code)
            else:
                type_str = "typing.Any"

            if attribute.default == attr.NOTHING:
                default = ""
            else:
                default = "={}".format(attribute.default)
            lines.append("    {}:{}{}".format(attribute.name, type_str, default))

        return "\n".join(lines)

