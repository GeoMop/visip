"""
This module provides wrapped default actions defined in the 'action' directory.

Problematic are actions generated from special constructs by the 'code' package:
- convertors/constructors, operators, ...
- actions that are already wrapped are just imported
"""
from . import constructor
from  .converter import *
from ..code import wrap
from .constructor import Value

dict = wrap.public_action(constructor.dict_constr())
list = wrap.public_action(constructor.list_constr())
tuple = wrap.public_action(constructor.tuple_constr())
