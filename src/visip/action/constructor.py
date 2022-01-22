import attr
import typing

from ..dev.base import _ActionBase
from ..dev import dtype as dtype
from ..dev.parameters import Parameters, ActionParameter
from ..dev import data


class Value(_ActionBase):
    def __init__(self, value):
        name = "Value"
        params = Parameters([], typing.Any)
        super().__init__(name, params)
        self.value = value

    def action_hash(self):
        return data.hash(self.value)

    def _evaluate(self):
        return self.value

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.value_code(self.value)


class Pass(_ActionBase):
    """
    Do nothing action. Meant for internal usage in particular.
    """
    def __init__(self):
        signature =params = Parameters([])
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
        p = ActionParameter(name='args', p_type=typing.Any,
                             default=ActionParameter.no_default, kind=ActionParameter.VAR_POSITIONAL)
        params = Parameters((p,), return_type=typing.Any)
        super().__init__(action_name, params)
        #self._output_type = typing.Any


class A_list(_ListBase):
    def __init__(self):
        super().__init__(action_name='list')

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.list("[", "]", [(None, arg) for arg in arg_names])

    def _evaluate(self, *inputs) -> typing.Any:
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

    def _evaluate(self, *inputs) -> typing.Any:
        return tuple(inputs)


class A_dict(_ActionBase):
    def __init__(self):
        p =  ActionParameter(name='args', p_type=typing.Tuple[typing.Any, typing.Any],
                            default=ActionParameter.no_default, kind=ActionParameter.VAR_POSITIONAL)
        signature = Parameters((p, ), return_type=typing.Any)
        super().__init__('dict', signature)




    def call_format(self, representer, action_name, arg_names, arg_values):
        # TODO: dict as action_name with prefix
        # Todo: check that inputs are pairs, extract key/value
        #return format.Format.list("{", "}", [(None, arg) for arg in arg_names])

        return _ActionBase.call_format(self, representer, action_name, arg_names, arg_values)

    def _evaluate(self, *inputs) -> typing.Any:
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
    TODO: pass signature as parameter, use static method to extract the signature, use in the action_def decorator
    """
    def __init__(self, data_class, signature):
        super().__init__(data_class.__name__, signature)
        self._data_class = data_class
        # Attr.s dataclass
        self.__visip_module__ = self._data_class.__module__
        # module where the data class is defined


    @property
    def constructor(self):
        return self._data_class

    def _evaluate(self, *args, **kwargs) -> dtype.DataClassBase:
        return self.constructor(*args, **kwargs)

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
        return a_hash
