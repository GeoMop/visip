import typing_inspect as ti
from ..dev import dtype as dtype
from . import formating


class Representer:
    """
    Auxiliary class for various common tools
    for code representation of the workflows.
    It is passed to the particular action representation
    methods as parameter.
    """
    def __init__(self):
        pass

    def type_code(self, type_hint):
        """
        dtype is a type specification.
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
                return 'wf.List[{}]'.format(self.type_code(item_type))
            else:
                print("No code representation for the type: {}[{}]"
                      .format(type_name, ti.get_args(type_hint)))
                return 'wf.Any'

    #TODO: Move Format into this file. Replace Format static methods by these two directly.
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

"""
TODO:
- unwrap wrapped types in arguments of the parametric type annotations, should be done when annotations are processed:
1. class creation
2. action _evaluate annotations processed
- should have generic support to that
"""
