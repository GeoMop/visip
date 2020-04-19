import os
import sys
from typing import *

class classproperty(object):
    """
    Decorator to define a class property getter, i.e. a function that
    returns value of class property.
    """
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def fallback(fallback_class, before_version: Tuple[int, int, int]):
    """
    Usage:

    @fallback((MyClass_36, before_version=(3.7.0))
    class MyClass:
        ...
    """
    if sys.version_info[:3] < before_version:
        return lambda decorated_class : fallback_class
    else:
        return lambda decorated_class : decorated_class


class change_cwd:
    """
    Context manager that change CWD, to given relative or absolute path.
    """
    def __init__(self, path: str):
        self.path = path
        self.orig_cwd = ""

    def __enter__(self):
        if self.path:
            self.orig_cwd = os.getcwd()
            os.chdir(self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.orig_cwd:
            os.chdir(self.orig_cwd)

