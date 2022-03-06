from typing import *

class DummyAction:
    """
    Have problems with actions wrapped directly into the Dummy, as it have dangerous __getattr__
    so we introduce separate wrapper class just for the static actions.
    """
    def __init__(self, af: 'ActionFactory', action: '_ActionBase') -> None:
        self._af = af
        self._action_value = action

    def __call__(self, *args, **kwargs):
        """
        Catch call of the function values.
        Check that the value is function/action.
        Perform its call
        """
        return Dummy(self._af, self._af.create(self._action_value, *args, **kwargs))

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


class DummyWorkflow:
    """
    In order to allow recursive workflows we have to postpone its construction to the first call.
    """
    def __init__(self, af: 'ActionFactory', workflow_func) -> None:
        self._af = af
        self._workflow_func = workflow_func
        self._workflow = None

    @property
    def workflow(self):
        """
        Create and return the workflow instance.
        :return:
        """
        if self._workflow is None:
            self._workflow = self._af.create_workflow_from_source(self._workflow_func)
            # here recursion occures, but now 'self._workflow' is set, so it just creates the action call
            output_call, slots  = self._af.actioncalls_from_function(self._workflow_func, self._workflow.parameters)
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



class Dummy:
    """
    Dummy object for wrapping action as its output value.
    Absorbs all possible operations supported by the corresponding data type and convert then to
    appropriate implicit actions.
    """

    def __init__(self, af: 'ActionFactory', value: Any) -> None:
        self._af = af
        self._value = value


    def __getattr__(self, key: str):
        try:
            assert self._value.return_type_have_attributes(), self._value.action
            return Dummy(self._af, self._af.GetAttribute(key, self._value))
        except AttributeError or AssertionError:
            raise AttributeError
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


    # Binary
    # Operators
    #
    # Operator
    # Method
    # +                       object.__add__(self, other)
    # -                        object.__sub__(self, other)
    # *object.__mul__(self, other)
    # // object.__floordiv__(self, other)
    # / object.__div__(self, other)
    # % object.__mod__(self, other)
    # ** object.__pow__(self, other[, modulo])
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





