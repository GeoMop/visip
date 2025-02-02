from visip.dev import dtype
from ..dev.base import ActionBase
from ..dev.extract_signature import _extract_signature


AT = dtype.NewType(dtype.Union(dtype.Int, dtype.Float), name="TArithmetic")
Array = AT  # temporary

# (operator_representation, operator_precedence)
op_properties = dict(
    lt=('<',3), le=('<=',3), gt=('>',3), ge=('>=',3), eq=('==',3), ne=('!=',3),
    add=('+',8), sub=('-',8),
    mul=('*',9), truediv=('/',9), mod=('%',9), floordiv=('//',9), matmul=('@', 9),
    pos=('+',10), neg=('-',10),
    pow=('**',11),
)
# TODO: modify _Operator for unary operator
# use action def for function operators.
# test all

# TODO: use bounded TypeVar if ready
def add(x:AT, y:AT) -> AT:
    return x+y

def sub(x:AT, y:AT) -> AT:
    return x-y

def mul(x:AT, y:AT) -> AT:
    return x*y

def matmul(x:Array, y: Array) -> Array:
    return x @ y

def truediv(x:AT, y:AT) -> AT:
    return x/y

def floordiv(x:AT, y:AT) -> AT:
    return x//y

def mod(x:AT, y:AT) -> AT:
    return x%y

def pow(x:AT, y:AT) -> AT:
    return x**y



def lt(x:AT, y:AT) -> dtype.Bool:
    return x<y

def le(x:AT, y:AT) -> dtype.Bool:
    return x<=y

def gt(x:AT, y:AT) -> dtype.Bool:
    return x>y

def ge(x:AT, y:AT) -> dtype.Bool:
    return x>=y

def eq(x:AT, y:AT) -> dtype.Bool:
    return x==y

def ne(x:AT, y:AT) -> dtype.Bool:
    return x!=y

def pos(x:AT) -> AT:
    return x

def neg(x:AT) -> AT:
    return -x




class _Operator(ActionBase):
    def __init__(self, op_fn):
        signature = _extract_signature(op_fn)
        name = f"__op__{op_fn.__name__}"
        self.op_repr, self.precedence = op_properties[op_fn.__name__]
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

