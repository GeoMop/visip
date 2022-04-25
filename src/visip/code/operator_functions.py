from ..dev import dtype


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



