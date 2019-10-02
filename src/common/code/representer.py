import typing_inspect as ti
from ..dev import type as dtype

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
        else:
            type_name = type_hint.__name__
            if type_name == 'List':
                type_args = ti.get_args(type_hint)
                assert len(type_args) == 1
                item_type = type_args[0]
                return 'typing.List[{}]'.format(self.type_code(item_type))
            else:
                print("No code representation for the type: {}[{}]"
                      .format(type_name, ti.get_args(type_hint)))
                return 'typing.Any'


"""
TODO:
- break cycle dependency to the action_base
- unwrap wrapped types in arguments of the parametric type annotations, should be done when annotations are processed:
1. class creation
2. action _evaluate annotations processed
- should have generic support to that
"""
