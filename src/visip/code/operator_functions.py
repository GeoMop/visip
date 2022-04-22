from ..dev import dtype


AT = dtype.NewType(dtype.Union(dtype.Int, dtype.Float), name="TArithmetic")

# (operator_representation, operator_precedence)
op_properties = dict(
    lt=('<',0), le=('<=',0), gt=('>',0), ge=('>=',0), eq=('==',0), ne=('!=',0),
    add=('+',1), sub=('-',1), mul=('*',2), truediv=('/',2), mod=('%',2), pow=('**',3),
         )

# TODO: use bounded TypeVar if ready
def add(x:AT, y:AT) -> AT:
    return x+y

def sub(x:AT, y:AT) -> AT:
    return x-y

def mul(x:AT, y:AT) -> AT:
    return x*y

def truediv(x:AT, y:AT) -> AT:
    return x/y

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