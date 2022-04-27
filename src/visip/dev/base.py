import enum
from . import data
from . import dtype
from .parameters import Parameters
from ..dev import dtype
# Name for the first parameter of the workflow definiton function that is used
# to capture instance names.
_VAR_="self"




class TaskType(enum.Enum):
    Atomic = 1
    Composed = 2


class ActionKind(enum.IntEnum):
    """
    Indicates some restrictions on the resource used for evaluation of the action.
    Meta actions should lead to Composed tasks, that are mostly expanded not evaluated.
    ... needs refined description.
    TODO: After stabilization of the metaactions should be extened to a concept of ActionRequirement
    e.g. an action requires MPI or GPU etc. However would be better if the action can run everywhere but possibly with
    limited efficiency, other wise we loose on portability.
    """
    Regular = 1  # input and output have specific type
    Meta = 2     # input or output is function / action
    Generic = 3  # input or output is generic type



class ActionBase(dtype._ActionBase):

    """
    Base of all actions.
    - have defined parameters
    - have defined output type
    - implement expansion to the Task DAG.
    - have _code representation
    """
    def __init__(self, action_name = None, signature = None):
        self.task_type = TaskType.Atomic
        self.action_kind = ActionKind.Regular
        self.is_analysis = False
        if action_name is None:
            action_name = self.__class__.__name__
        self.name = action_name
        self.__name__ = self.name

        # Module where the action is defined.
        if signature is None:
            signature = Parameters([])

        self._parameters = signature
        # Parameter specification list, class attribute, no parameters by default.

    def __repr__(self):
        return self.name

    # @property
    # def module(self):
    #     """
    #     Module prefix used in code generationn.
    #     :return:
    #     """
    #     #TODO: TB - I think this property became obsolete. Also it currently doesn't work because __visip_module__ doesn't exist
    #     assert self.__visip_module__
    #     return self.__visip_module__

    def action_hash(self):
        """
        Hash of values representing the action. Hash must be different if the action
        produce different result for the same input.
        TODO: Make generic implementation more general. Possibly replacing nearly all specializations.
        - hash action parameters
        - hash values of constant parameters
        :return:
        """
        name_hash = data.hash((self.__module__, self.__name__))
        try:
            code = self._evaluate.__code__
        except AttributeError:
            assert self._evaluate.__module__ == 'builtins'
            code = self.name

        return data.hash(code.__hash__(), previous=name_hash)

    @property
    def output_type(self):
        return self.parameters.return_type


    @property
    def parameters(self):
        return self._parameters


    def evaluate(self, *args, **kwargs):
        """
        Common evaluation function for all actions.
        Call _evaluate which actually implements the action.
        :param inputs: List of arguments.
        :return: action result
        """
        return self._evaluate(*args, **kwargs)


    def _evaluate(self):
        """
        Pure virtual method.
        If the validate method is defined it is used for type compatibility validation otherwise
        this method must handle both a type tree and the data tree on the input
        returning the appropriate output type tree or the data tree respectively.
        :param inputs: List of actual inputs. Same order as the action arguments.
        :return:
        """
        assert False, "Implementation has to be provided."


    def call_format(self, representer, full_action_name, arg_names, arg_values):
        """
        Return a Format of the action call with placeholders for the actual arguments.
        Names of placehloders are given by action_call names 'arg_names'.
        TODO: Keyword arguments.
        - usually it is better to use keyword arguments as it is more desriptive
        - if there is variadic parameter, we can not use keyword arguments at all
        - some actions are so common, that we may prefer to not use the keyword
          or use it only for some parameter

        1. don't use named arguments if there is variadic parameter
        2. don't use named argument if value is named action_call
        3. otherwise use named argument

        :param representer ... Representer
        :param full_action_name ... name with correct module prefix
        :param arg_names ... action_call names within workflow
        :param arg_values ... action_calls
        :return: Format ... basically list of strings and placeholders (for argument values).
        TODO: modify to represent to deal with new scheme of arguments as dict.
        """
        args = []
        have_variadic = any(p.kind == p.VAR_POSITIONAL for p in self.parameters)
        for i, arg in enumerate(arg_names):
            param = self.parameters.at(i)
            if param.kind == param.POSITIONAL_ONLY or \
               param.kind == param.POSITIONAL_OR_KEYWORD and have_variadic or\
               param.kind == param.VAR_POSITIONAL:
                param_name = None
            else:
                assert param.name is not None
                param_name = param.name
            args.append( (param_name, arg) )
        return representer.action_call(full_action_name, *args)



    # def validate(self, inputs):
    #     return self.evaluate(inputs)


    def code_of_definition(self, representer):
        # TODO: make derived class for actions implemented in user module
        # and move thic method there

        indent_str = representer.n_indent * " "

        params = []
        for i, param in enumerate(self.parameters):
            type_anot = representer.str_unless(': ', representer.type_code(param.type))

            param_def = f"{param.name}{type_anot}"
            params.append(param_def)
        result_hint = representer.str_unless(' -> ', representer.type_code(self.parameters.return_type))

        lines = [
            f"@{representer.make_rel_name('visip.code.decorators', 'action_def')}",
            f"def {self.name}({', '.join(params)}){result_hint}:",
            f"{indent_str}# User defined action cen not been represented.",
            f"{indent_str}pass"]
        return "\n".join(lines)

    def __visip_code__(self, representer):
        return representer.make_rel_name(self.__module__, self.name)





# need different way to instantiate a defined dataclass type


# class Zip(dev._ActionBase):
#     # zip number of lists into single list of lists
#
# class ZipToClass(dev.ActionBase):
#     # given a dict of lists convert to list of dicts

