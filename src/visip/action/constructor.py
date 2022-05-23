import enum

from ..dev.base import ActionBase
from ..dev import dtype
from ..dev.parameters import Parameters, ActionParameter
from ..dev import data
from ..dev import base
from ..dev.extract_signature import _extract_signature
from ..code.operator_functions import op_properties

class Value(ActionBase):
    def __init__(self, value):
        name = "Value"
        value_type = dtype.type_of_value(value)
        assert value_type is not dtype.EmptyType
        params = Parameters([], value_type)
        super().__init__(name, params)
        self.action_kind = base.ActionKind.Meta
        self.value = value

    def __repr__(self):
        return f"Value({self.value})"

    def action_hash(self):
        salt_hash = data.hash("Value")
        # In the case of "action" value with action having no parameters, we have to distinguish
        # hash of the result of action from the hash of the action itself (result of the Value action).
        # TODO: any way we should store action values to a separate storage private to the scheduler
        return data.hash(self.value, previous=salt_hash)

    def _evaluate(self):
        return self.value

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.value_code(self.value)


class Pass(ActionBase):
    """
    Propagate given single argument. Do nothing action. Meant for internal usage in particular.
    """
    def __init__(self):
        t = dtype.TypeVar(name="T")
        p = ActionParameter('input', t)
        signature = Parameters((p,), t)
        self.action_kind = base.ActionKind.Generic
        super().__init__('Pass', signature)

    def _evaluate(self, input):
        return input






class _ListBase(ActionBase):
    """
    Base action class for actions accepting any number of unnamed parameters.
    """
    # We assume that parameters are used only in reinit, which do not use it
    # in this case. After reinit one should use only self.arguments.

    def __init__(self, action_name):
        self.action_kind = base.ActionKind.Generic
        t = dtype.TypeVar(name="T")
        p = ActionParameter(name='args', p_type=t,
                            default=ActionParameter.no_default, kind=ActionParameter.VAR_POSITIONAL)
        params = Parameters((p,), return_type=dtype.List(t))
        super().__init__(action_name, params)


class A_list(_ListBase):
    def __init__(self):
        super().__init__(action_name='list')

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.list("[", "]", [(None, arg) for arg in arg_names])

    def _evaluate(self, *inputs):
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

    def _evaluate(self, *inputs):
        return tuple(inputs)


class A_dict(ActionBase):
    def __init__(self):
    	# TODO: TypeVar
        p =  ActionParameter(name='args', p_type=dtype.Tuple(dtype.Any, dtype.Any),
                            default=ActionParameter.no_default, kind=ActionParameter.VAR_POSITIONAL)
        self.action_kind = base.ActionKind.Generic
        signature = Parameters((p, ), return_type=dtype.Any)
        super().__init__('dict', signature)




    def call_format(self, representer, action_name, arg_names, arg_values):
        # TODO: dict as action_name with prefix
        # Todo: check that inputs are pairs, extract key/value
        #return format.Format.list("{", "}", [(None, arg) for arg in arg_names])

        return ActionBase.call_format(self, representer, action_name, arg_names, arg_values)

    def _evaluate(self, *inputs):
        return {key: val for key, val in inputs}
        #item_pairs = ( (key, val) for key, val in inputs)
        #return dict(item_pairs)

"""
TODO: 
- test for construction of list and tuple using action names
"""





class ClassActionBase(ActionBase):
    """
    Action constructs particular Dataclass given in constructor.
    So the action is parametrized by the 'data_class'.
    """
    def __init__(self, data_class, signature):
        super().__init__(data_class.__name__, signature)
        self._data_class = data_class
        # Attr.s dataclass
        self.__visip_module__ = self._data_class.__module__
        # module where the data class is defined

    def _evaluate(self, *args, **kwargs) -> dtype.DataClassBase:
        return self._data_class(*args, **kwargs)

    def code_of_definition(self, representer):
        """
        TODO:
        1. prefixin gfor typing.Any and other builtin types is wrong.
        2. need access to definitions of other classes.
        :param representer:
        :param make_rel_name:
        :return:
        """
        lines = [f"@{representer.make_rel_name('visip.code.decorators', 'Class')}"]
        lines.append('class {}:'.format(self.name))
        for attribute in self.parameters:
            lines.append(representer.parameter(attribute))

        return "\n".join(lines)

    def action_hash(self):
        a_hash = data.hash(self.name)
        for param in self.parameters:
            a_hash = data.hash(param.name, previous=a_hash)
        return a_hash



class EnumActionBase(ActionBase):
    """
    Conversion from int to the enum.
    """
    def __init__(self, enum_class):
        assert isinstance(enum_class, enum.EnumMeta), str(enum_class)
        enum_class.__visip_code__ = self.code_of_item
        signature = Parameters([ActionParameter("enum_item", dtype.Int)], return_type=dtype.Enum(enum_class))
        super().__init__(enum_class.__name__, signature)
        self._enum_class = enum_class
        # Attr.s dataclass
        #self.__module__ = self._enum_class.__module__
        # module where the data class is defined

    def _evaluate(self, *args, **kwargs) -> dtype.DataClassBase:
        return self._enum_class(*args, **kwargs)

    def action_hash(self):
        a_hash = data.hash(self.name)
        for param in self.parameters:
            a_hash = data.hash(param.name, previous=a_hash)
        return a_hash


    @staticmethod
    def code_of_item(self: enum.IntEnum, representer):
        """
        Behaves as method of IntEnum, returns string with representation of the enum value.
        """
        enum_base, key = str(self).split('.')
        enum_base = representer.make_rel_name(self.__module__, enum_base)
        return '.'.join([enum_base, key])

    def code_of_definition(self, representer):
        """
        """
        indent_str = representer.n_indent * " "
        lines = [f"@{representer.make_rel_name('visip.code.decorators', 'Enum')}"]
        lines.append('class {}:'.format(self.__name__))
        for item in self._enum_class:
            lines.append(f"{indent_str}{item.name} = {item.value}")

        return "\n".join(lines)


class _Operator(ActionBase):
    def __init__(self, op_fn):
        signature = _extract_signature(op_fn)
        name = op_fn.__name__
        self.op_repr, self.precedence = op_properties[name]
        self._evaluate = op_fn
        super().__init__(name, signature)

    def higher_precedence(self, other: ActionBase):
        return isinstance(other, _Operator) and self.precedence > other.precedence



    def call_format(self, representer, full_name, arg_names, arg_values):
        def parenthesis(arg_name, value):
            token = representer.token(arg_name)
            if self.higher_precedence(value.action):
                return ('(', token, ')')
            else:
                return (token,)

        assert len(self.parameters) == len(arg_names)
        if len(arg_names) == 1:
            return representer.format(
                self.op_repr, " ",
                *parenthesis(arg_names[0], arg_values[0])
            )
        elif len(arg_names) == 2:
            return representer.format(
                *parenthesis(arg_names[0], arg_values[0]), " ",
                self.op_repr, " ",
                *parenthesis(arg_names[1], arg_values[1])
            )
        else:
            assert False, "Wrong number of operator arguments."

