from ..dev.type_inspector import TypeInspector
from ..dev import dtype
from . import formating
from ..dev import parameters

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
        return self.type_code_inner(dtype.to_typing(type_hint))

    def type_code_inner(self, type_hint):
        ti = TypeInspector()
        if type_hint is None:
            # TODO: represent None as no type annotation, but it should be forbidden.
            return 'None'
        elif ti.is_any(type_hint):
            return self.make_rel_name('typing', 'Any')
        elif ti.is_base_type(type_hint):
            return type_hint.__name__
        elif ti.is_dataclass(type_hint):
            return self.make_rel_name(type_hint.__module__, type_hint.__name__)
        else:
            args = ti.get_args(type_hint)
            if args:
                args_code = ", ".join([self.type_code_inner(arg) for arg in args])
                (module, name) = str(ti.get_typing_origin(type_hint)).split(".")
                origin_name = self.make_rel_name(module, name)
                code = "{}[{}]".format(origin_name, args_code)
                return code
            else:
                raise Exception(f"No code representation for the type: {type_hint}")


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

        if param.default == param.no_default:
            default = ""
        else:
            default = "={}".format(param.default)
        return "{}{}:{}{}".format(indent_str, param.name, type_code, default)


"""
TODO:
- unwrap wrapped types in arguments of the parametric type annotations, should be done when annotations are processed:
1. class creation
2. action _evaluate annotations processed
- should have generic support to that
"""
