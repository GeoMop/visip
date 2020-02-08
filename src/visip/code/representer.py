import typing_inspect as ti
from ..dev import dtype as dtype
from . import formating
from ..dev import parameters

class Representer:
    """
    Auxiliary class for various common tools
    for code representation of the workflows.
    It is passed to the particular action representation
    methods as parameter.
    """

    def __init__(self, make_rel_name):
        self.make_rel_name = make_rel_name
        # function to make full name of the action (using correct name of module)

    def type_code(self, type_hint):
        """
        dtype is a type specification.
        TODO: More general type representation.
        :param type_hint:
        :return:
        """

        if type_hint is None:
            return 'None'
        elif dtype.is_base_type(type_hint):
            return type_hint.__name__
        elif issubclass(type_hint, dtype.DataClassBase):
            return type_hint.__name__
        else:
            type_name = type_hint.__name__
            if type_name == 'List':
                type_args = ti.get_args(type_hint)
                assert len(type_args) == 1
                item_type = type_args[0]
                list_typing = self.make_rel_name('visip', 'List')
                return '{}[{}]'.format(list_typing, self.type_code(item_type))
            else:
                print("No code representation for the type: {}[{}]"
                      .format(type_name, ti.get_args(type_hint)))
                any_typing = self.make_rel_name('visip', 'Any')
                return any_typing

    def value_code(self, value):
        if hasattr(value, '__code__'):
            expr = value.__code__(self)
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


    def parameter(self, param: parameters.ActionParameter, indent:int = 4) -> str:
        indent_str = indent * " "
        type_code = self.type_code(param.type)
        type_str = self.make_rel_name(param.type.__module__, type_code)

        if param.default == param.no_default:
            default = ""
        else:
            default = "={}".format(param.default)
        return "{}{}:{}{}".format(indent_str, param.name, type_str, default)


"""
TODO:
- unwrap wrapped types in arguments of the parametric type annotations, should be done when annotations are processed:
1. class creation
2. action _evaluate annotations processed
- should have generic support to that
"""
