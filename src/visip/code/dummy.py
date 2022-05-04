import inspect
import dis
from typing import *
from ..dev.dtype import _DummyClassBase
from . import operator_functions as of

class DummyAction(_DummyClassBase):
    """
    Have problems with actions wrapped directly into the Dummy, as it have dangerous __getattr__
    so we introduce separate wrapper class just for the static actions.
    """
    def __init__(self, af: 'ActionFactory', action: '_ActionBase') -> None:
        self._af = af
        self._action_value = action

    def wrapped(self):
        """
        Original definition before decoration.
        """
        return self._action_value

    def __call__(self, *args, **kwargs):
        """
        Catch call of the function values.
        Check that the value is function/action.
        Perform its call
        """
        return Dummy(self._af, self._af.create(self._action_value, *args, **kwargs))

    def __getattr__(self, key: str):
        """
        Catch access to enum items: `Enum.x`
        VISIP Enum is an action converting nt to the Enum value so it is wrapped into DummyAction.
        """
        if key[:2] == "__":     # __super_type__
            return None
        try:
            return Dummy(self._af, self._af.create_value(self._action_value._enum_class[key]))
        except AttributeError:
            raise AttributeError(obj=self._action_value, name=key)

    def evaluate(self, *args, **kwargs):
        """
        Direct (nonlazy) call of the wrapped action.
        :param args:
        :param kwargs:
        :return:
        """
        return self._action_value.evaluate(*args, **kwargs)

    def call(self, *args, **kwargs):
        """
        Call an action from an action_def, i.e. regular Python function.
        :param args:
        :param kwargs:
        :return:
        """
        return self._action_value.evaluate(*args, **kwargs)

    def __repr__(self):
        return f"DummyAction({self._action_value})"

class DummyWorkflow(_DummyClassBase):
    """
    In order to allow recursive workflows we have to postpone its construction to the first call.
    """
    def __init__(self, af: 'ActionFactory', workflow_func) -> None:
        self._af = af
        self._workflow_func = workflow_func
        self._workflow = None

    def wrapped(self):
        """
        Original definition before decoration.
        """
        return self.workflow

    @property
    def workflow(self):
        """
        Create and return the workflow instance.
        :return:
        """
        if self._workflow is None:
            self._workflow = self._af.create_workflow_from_source(self._workflow_func)
            # here recursion occures, but now 'self._workflow' is set, so it just creates the action call
            output_call, slots = self._af.actioncalls_from_function(self._workflow_func, self._workflow.parameters)
            self._workflow.set_result_action(output_call, slots)
        return self._workflow

    @property
    def _action_value(self):
        return self.workflow

    def __call__(self, *args, **kwargs):
        """
        Catch call of the function values.
        Check that the value is function/action.
        Perform its call
        """
        return Dummy(self._af, self._af.create(self.workflow, *args, **kwargs))

    def evaluate(self, *args, **kwargs):
        """
        Direct (nonlazy) call of the wrapped action.
        :param args:
        :param kwargs:
        :return:
        """
        assert False, "Not implemented yet."
        #wf = self._af.create_workflow_from_source(self._workflow_func)
        #return self._action_value.evaluate(*args, **kwargs)

    def __repr__(self):
        return f"DummyWorkflow({self._workflow_func})"


class Dummy:
    """
    Dummy object for wrapping action as its output value.
    Absorbs all possible operations supported by the corresponding data type and convert then to
    appropriate implicit actions.
    """

    def __init__(self, af: 'ActionFactory', value: Any) -> None:
        self._af = af
        self._value = value

    def __repr__(self):
        return f"Dummy({self._value})"


    def __getattr__(self, key: str):
        try:
            if not self._value.return_type_have_attributes():
                raise AttributeError(f"{self._value} does not have attributes ({key}).")
            return Dummy(self._af, self._af.GetAttribute(key, self._value))
        except AttributeError:
            raise AttributeError(f"{self._value} does not have attribute {key}.")
        # TODO: update the type to know that it is a dataclass containing 'key'
        # TODO: check that type is dataclass

    def __getitem__(self, idx: int):
        return Dummy(self._af, self._af.GetItem(self._value, idx))

    def __call__(self, *args, **kwargs):
        """
        Catch call of the function values.
        Check that the value is function/action.
        Perform its call
        """
        return Dummy(self._af, self._af.create_dynamic_call(self._value, *args, **kwargs))

    def _expecting(self, offset=0):
        """Return how many values the caller is expecting"""
        f = inspect.currentframe().f_back.f_back
        i = f.f_lasti + offset
        bytecode = f.f_code.co_code
        instruction = bytecode[i]
        if instruction == dis.opmap['UNPACK_SEQUENCE']:
            return bytecode[i + 1]
        elif instruction == dis.opmap['POP_TOP']:
            return 0
        else:
            return 1
    def __iter__(self):
        """
        Unpack Dummy as a tuple.
        :return:
        """
        # offset = 3 bytecodes from the call op to the unpack op
        for i in range(self._expecting(offset=0)):
            yield Dummy(self._af, self._af.GetItem(self._value, i))

    def binary_op(self, op,  x, y):
        return Dummy(self._af, self._af.create_operator(op, x, y))

    def unary_op(self, op,  x):
        return Dummy(self._af, self._af.create_operator(op, x))

    # Arithmetic operators

    def __add__(self, other):
        return self.binary_op(of.add, self._value, other)

    def __radd__(self, other):
        return self.binary_op(of.add, other, self._value)


    def __sub__(self, other):
        return self.binary_op(of.sub, self._value, other)

    def __rsub__(self, other):
        return self.binary_op(of.sub, other, self._value)

    def __mul__(self, other):
        return self.binary_op(of.mul, self._value, other)

    def __rmul__(self, other):
        return self.binary_op(of.mul, other, self._value)


    def __truediv__(self, other):
        return self.binary_op(of.truediv, self._value, other)

    def __rtruediv__(self, other):
        return self.binary_op(of.truediv, other, self._value, )

    def __floordiv__(self, other):
        return self.binary_op(of.floordiv, self._value, other)

    def __rfloordiv__(self, other):
        return self.binary_op(of.floordiv, self._value, other)

    def __mod__(self, other):
        return self.binary_op(of.mod, self._value, other)

    def __rmod__(self, other):
        return self.binary_op(of.mod, other, self._value)


    def __pow__(self, other):
        return self.binary_op(of.pow, self._value, other)

    def __rpow__(self, other):
        return self.binary_op(of.pow, other, self._value)

    # Comparison operators

    def __lt__(self, other):
        return self.binary_op(of.lt, self._value, other)

    def __le__(self, other):
        return self.binary_op(of.le, self._value, other)

    def __gt__(self, other):
        return self.binary_op(of.gt, self._value, other)

    def __ge__(self, other):
        return self.binary_op(of.ge, self._value, other)

    def __eq__(self, other):
        return self.binary_op(of.eq, self._value, other)

    def __ne__(self, other):
        return self.binary_op(of.ne, self._value, other)

    # Unary operators
    def __pos__(self):
        return self.unary_op(of.pos, self._value)

    def __neg__(self):
        return self.unary_op(of.neg, self._value)



    """    
    __int__
    __float__
    __complex__
    __oct__
    __hex__
    __index__
    __floordiv__ 
    
    """




    # Binary
    # Operators
    #
    # // object.__floordiv__(self, other)
    # / object.__div__(self, other)
    # << object.__lshift__(self, other)
    # >> object.__rshift__(self, other)
    # & object.__and__(self, other)
    # ^ object.__xor__(self, other)
    # | object.__or__(self, other)
    #
    # Assignment
    # Operators:
    #
    # Operator
    # Method
    # += object.__iadd__(self, other)
    # -= object.__isub__(self, other)
    # *= object.__imul__(self, other)
    # /= object.__idiv__(self, other)
    # //= object.__ifloordiv__(self, other)
    # %= object.__imod__(self, other)
    # **= object.__ipow__(self, other[, modulo])
    # <<= object.__ilshift__(self, other)
    # >>= object.__irshift__(self, other)
    # &= object.__iand__(self, other)
    # ^= object.__ixor__(self, other)
    # |= object.__ior__(self, other)
    #
    # Unary
    # Operators:
    #
    # Operator
    # Method
    # -                       object.__neg__(self)
    # +                      object.__pos__(self)
    # abs()
    # object.__abs__(self)
    # ~                      object.__invert__(self)
    # complex()
    # object.__complex__(self)
    # int()
    # object.__int__(self)
    # long()
    # object.__long__(self)
    # float()
    # object.__float__(self)
    # oct()
    # object.__oct__(self)
    # hex()
    # object.__hex__(self)
    #
    # Comparison
    # Operators
    #
    # Operator
    # Method
    # < object.__lt__(self, other)
    # <= object.__le__(self, other)
    # == object.__eq__(self, other)
    # != object.__ne__(self, other)
    # >= object.__ge__(self, other)
    # > object.__gt__(self, other)





