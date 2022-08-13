from ..dev.base import ActionBase
from ..dev.extract_signature import _extract_signature
from visip.action.operator_functions import op_properties

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

