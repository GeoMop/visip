"""
This module provides wrapped default actions defined in the 'action' directory.

Problematic are actions generated from special constructs by the 'code' package:
- convertors/constructors, operators, ...
- actions that are already wrapped are just imported
"""
from . import constructor
from ..code.decorators import public_action
from ..dev import meta

dict = public_action(constructor.A_dict())
list = public_action(constructor.A_list())
tuple = public_action(constructor.A_tuple())
If = public_action(meta._If())
#partial = wrap.public_action(meta.Partial())