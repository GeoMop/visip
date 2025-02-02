import sys
from . import operator_functions as _of
from . import action_factory as _af
from . import wrapped as _wrapped

__visip_mod = sys.modules[__name__]
ops = ['lt', 'le', 'gt', 'ge', 'eq', 'ne', 'add', 'sub', 'mul', 'truediv', 'mod', 'floordiv', 'matmul', 'pos', 'neg']
for op_name in ops:
    fn = getattr(_of, op_name)
    mod_dir = __visip_mod.__dict__
    op_action = _af.ActionFactory.add_action(fn)
    mod_dir[op_action.name] = _wrapped._visip_action(op_action, module="visip.operator")
