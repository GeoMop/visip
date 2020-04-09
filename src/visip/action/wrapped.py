"""
This module provides wrapped default actions defined in the 'action' directory.

Problematic are actions generated from special constructs by the 'code' package:
- convertors/constructors, operators, ...
- actions that are already wrapped are just imported
"""
from . import constructor
from ..code import wrap
from ..dev import meta

dict = wrap.public_action(constructor.A_dict())
list = wrap.public_action(constructor.A_list())
tuple = wrap.public_action(constructor.A_tuple())
If = wrap.public_action(meta._If())