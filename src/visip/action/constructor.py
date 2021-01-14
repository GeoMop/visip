import attr
import typing

from ..dev.base import _ActionBase
from ..dev import dtype as dtype
from ..dev.parameters import Parameters, ActionParameter, extract_func_signature
from ..dev import data


class Value(_ActionBase):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def action_hash(self):
        return data.hash(self.value)

    def _evaluate(self) -> typing.Any:
        return self.value

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.value_code(self.value)


class Pass(_ActionBase):
    """
    Do nothing action. Meant for internal usage in particular.
    """
    def __init__(self):
        super().__init__()

    def _evaluate(self, input: dtype.DataType):
        return input






class _ListBase(_ActionBase):
    """
    Base action class for actions accepting any number of unnamed parameters.
    """
    # We assume that parameters are used only in reinit, which do not use it
    # in this case. After reinit one should use only self.arguments.

    def __init__(self, action_name):
        super().__init__(action_name)
        self._parameters = Parameters()
        self._parameters.append(
            ActionParameter(name=None, type=typing.Any,
                                       default=ActionParameter.no_default))
        self._output_type = typing.Any


class A_list(_ListBase):
    def __init__(self):
        super().__init__(action_name='list')

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.list("[", "]", [(None, arg) for arg in arg_names])

    def evaluate(self, inputs) -> typing.Any:
        return list(inputs)


class A_tuple(_ListBase):
    """
    This action is necessary only for better typechecking, using fixed number of items
    of given type.
    """
    def __init__(self):
        super().__init__(action_name='tuple')

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.list("(", ")", [(None, arg) for arg in arg_names])

    def evaluate(self, inputs) -> typing.Any:
        return tuple(inputs)


class A_dict(_ActionBase):
    def __init__(self):
        super().__init__(action_name='dict')
        self._parameters = Parameters()
        self._parameters.append(
            ActionParameter(name=None, type=typing.Tuple[typing.Any, typing.Any],
                            default=ActionParameter.no_default))
        self._output_type = typing.Any

    def call_format(self, representer, action_name, arg_names, arg_values):
        # TODO: dict as action_name with prefix
        # Todo: check that inputs are pairs, extract key/value
        #return format.Format.list("{", "}", [(None, arg) for arg in arg_names])

        return _ActionBase.call_format(self, representer, action_name, arg_names, arg_values)

    def evaluate(self, inputs) -> typing.Any:
        return {key: val for key, val in inputs}
        #item_pairs = ( (key, val) for key, val in inputs)
        #return dict(item_pairs)

"""
TODO: 
- test for construction of list and tuple using action names
"""





class ClassActionBase(_ActionBase):
    base_data_type = dtype.DataClassBase
    """
    Action constructs particular Dataclass given in constructor.
    So the action is parametrized by the 'data_class'.
    """
    def __init__(self, data_class):
        super().__init__(data_class.__name__)
        self._data_class = data_class
        # Attr.s dataclass
        self.__visip_module__ = self._data_class.__module__
        # module where the data class is defined

        self._parameters, _ = extract_func_signature(data_class.__init__, skip_self=True)
        self._output_type = data_class
        # Initialize parameters of the action.


    @staticmethod
    def dataclass_from_params(name: str, params: Parameters, module=None):
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

        return attr.s(repr=False)(data_class)

    @classmethod
    def construct_from_params(cls, name: str, params: Parameters, module=None):
        """
        Use Params to consturct the data_class and then instance of ClassActionBase.
        :param name: name of the class
        :param params: instance of Parameters
        :return:
        """
        return cls(cls.dataclass_from_params(name, params, module))

    @property
    def constructor(self):
        return self._data_class

    def _evaluate(self, *args) -> dtype.DataClassBase:
        return self.constructor(*args)

    def code_of_definition(self, representer):
        """
        TODO:
        1. prefixin gfor typing.Any and other builtin types is wrong.
        2. need access to definitions of other classes.
        :param representer:
        :param make_rel_name:
        :return:
        """
        lines = ['@wf.Class']
        lines.append('class {}:'.format(self.name))
        for attribute in self.parameters:
            lines.append(representer.parameter(attribute))

        return "\n".join(lines)

    def action_hash(self):
        a_hash = data.hash(self.name)
        for param in self.parameters:
            a_hash = data.hash(param.name, previous=a_hash)
            a_hash = data.hash(param.name, previous=a_hash)
