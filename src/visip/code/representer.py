from ..dev.type_inspector import TypeInspector
from ..dev import dtype
from . import formating
from ..dev import parameters

import typing_inspect

class Representer:
    """
    Auxiliary class for various common tools
    for code representation of the workflows.
    It is passed to the particular action representation
    methods as parameter.
    """

    @staticmethod
    def make_rel_name(module, name):
        return module + name

    def __init__(self, make_rel_name=None):
        self.n_indent = 4
        if make_rel_name is None:
            make_rel_name = Representer.make_rel_name
        self.make_rel_name = make_rel_name
        # function to make full name of the action (using correct name of module)

    def type_code(self, type_hint):
        """
        dtype is a type specification.
        TODO: More general type representation.
        :param type_hint:
        :return:
        """
        return dtype.type_code(type_hint, self.make_rel_name)



    def value_code(self, value):
        if value is dtype.empty:
            return value
        elif hasattr(value, '__visip_code__'):
            expr = value.__visip_code__(self)
        elif type(value) is str:
            expr = "'{}'".format(value)
        else:
            expr = str(value)
        return formating.Format(expr)

    @staticmethod
    def action_call(name, *arguments):
        return formating.Format.action_call(name, arguments)

    @staticmethod
    def list(prefix, postfix, argument_list):
        return formating.Format.list(prefix, postfix, argument_list)

    @staticmethod
    def format(*token_list):
        return formating.Format(token_list)

    @staticmethod
    def token(name):
        return formating.Placeholder(name)

    @staticmethod
    def str_unless(prefix:str, str:object) -> str:
        return "" if str is dtype.empty else f"{prefix}{str}"

    def type_anotation(self, prefix, type_hint):
        type_code = self.type_code(type_hint)
        return self.str_unless(f"{prefix}{type_code}", type_code is None)

    def parameter(self, param: parameters.ActionParameter, indent:int = 4) -> str:
        indent_str = self.n_indent * " "
        type_anot = self.str_unless(':', self.type_code(param.type))
        default = self.str_unless('=', self.value_code(param.default))
        return f"{indent_str}{param.name}{type_anot}{default}"


"""
TODO:
- unwrap wrapped types in arguments of the parametric type annotations, should be done when annotations are processed:
1. class creation
2. action _evaluate annotations processed
- should have generic support to that
"""
