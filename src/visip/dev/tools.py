import os
import sys
import attr
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
############################################################

ArgsValue = TypeVar('ArgsValue')
ArgsPair = Tuple[List[ArgsValue], Dict[str, ArgsValue]]

DecomposedValue = TypeVar('DecomposedValue')
def decompose_arguments(args_pair: ArgsPair[DecomposedValue]) -> Tuple[ArgsPair[int], List[DecomposedValue]]:
    """
    Separate the arguments structure and argument values.
    Returns arguments pair (args, kwargs) with values replaced by IDs
            and list of the values inorder of IDs.
    :param args_pair: (args, kwargs) with values
    :return: (id_args, id_kwargs), values
    """
    args, kwargs = args_pair
    values = []
    id_args = []
    for a in args:
        id_args.append(len(values))
        values.append(a)
    id_kwargs = {}
    for k, a in kwargs.items():
        id_kwargs[k] = len(values)
        values.append(a)
    return  (id_args, id_kwargs), values


ComposedValue = TypeVar('ComposedValue')
def compose_arguments(id_args_pair: ArgsPair[int],
            values: [ComposedValue]) -> ArgsPair[ComposedValue]:
    """
    For given (id_args, id_kwargs) and list of values
    return (args, kwargs) with values.
    :param id_args_pair:
    :param values:
    :return:
    """
    id_args, id_kwargs = id_args_pair
    args = [values[ia] for ia in id_args]
    kwargs = { k: values[ia] for k, ia in id_kwargs.items()}
    return args, kwargs


##########################################################

@attr.s(auto_attribs=True)
class TaskBinding:
    child_name: str
    action: '_ActionBase'
    id_args_pair: ArgsPair[int]
    inputs: List['Task']

