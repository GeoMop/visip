from ..dev import dtype


AT = dtype.NewType(dtype.Union(dtype.Int, dtype.Float), name="TArithmetic")

op_char = dict(
    add='+', sub='-', mul='*', truediv='/', mod='%', pow='**',
    lt='<', le='<=', gt='>', ge='>=', eq='==', ne='!=')

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