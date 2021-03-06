import enum
from . import data
from .parameters import Parameters, extract_func_signature



# Name for the first parameter of the workflow definiton function that is used
# to capture instance names.
_VAR_="self"


class ExcMissingArgument(Exception):
    pass

class ExcActionExpected(Exception):
    pass

class ExcTooManyArguments(Exception):
    pass

class ExcUnknownArgument(Exception):
    pass

class ExcDuplicateArgument(Exception):
    pass



class TaskType(enum.Enum):
    Atomic = 1
    Composed = 2




class _ActionBase:

    """
    Base of all actions.
    - have defined parameters
    - have defined output type
    - implement expansion to the Task DAG.
    - have _code representation
    """
    def __init__(self, action_name = None, action_module="visip"):
        self.task_type = TaskType.Atomic
        self.is_analysis = False
        self.name = action_name or self.__class__.__name__
        self.__module__ = action_module
        self.__name__ = self.name
        # Module where the action is defined.
        self._parameters = None
        # Parameter specification list, class attribute, no parameters by default.
        self._output_type = None
        # Output type of the action, class attribute.
        # Both _parameters and _outputtype can be extracted from type annotations of the evaluate method using the _extract_input_type.


    @property
    def module(self):
        """
        Module prefix used in code generationn.
        :return:
        """
        #TODO: TB - I think this property became obsolete. Also it currently doesn't work because __visip_module__ doesn't exist
        assert self.__visip_module__
        return self.__visip_module__

    def action_hash(self):
        """
        Hash of values representing the action. Hash must be different if the action
        produce different result for the same input.
        TODO: Make generic implementation more general. Possibly replacing nearly all specializations.
        - hash action parameters
        - hash values of constant parameters
        :return:
        """
        return data.hash(self.name)


    def _extract_input_type(self, func=None, skip_self=True) -> None:
        """
        Extract input and output types of the action from its evaluate method.
        Only support fixed numbeer of parameters named or positional.
        set: cls._input_type, cls._output_type
        """
        if self._parameters is not None:
            return
        if func is None:
            func = self._evaluate
        self._parameters, self._output_type = extract_func_signature(func, skip_self)
        self.check_type_annotations()

    def check_type_annotations(self):
        for param in self.parameters:
            assert param.type is not None, "Missing type annotation of parameter: {}  of action: {}".format(param.name, self.name)
        assert self.output_type is not None, "Missing return type annotation of action: {}".format(self.name)

    @property
    def output_type(self):
        self._extract_input_type()
        return self._output_type


    @property
    def parameters(self):
        self._extract_input_type()
        return self._parameters


    def evaluate(self, inputs):
        """
        Common evaluation function for all actions.
        Call _evaluate which actually implements the action.
        :param inputs: List of arguments.
        :return: action result
        """
        return self._evaluate(*inputs)


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
        """
        args = []
        for i, arg in enumerate(arg_names):
            if  self.parameters.is_variadic():
                param_name = None
            else:
                param = self.parameters.get_index(i)
                assert param is not None
                param_name = param.name
            args.append( (param_name, arg) )
        return representer.action_call(full_action_name, *args)



    def validate(self, inputs):
        return self.evaluate(inputs)


    def code_of_definition(self, representer):
        # TODO: make derived class for actions implemented in user module
        # and move thic method there
        type_code = representer.type_code(self.output_type)
        type_code = representer.make_rel_name(self.output_type.__module__, type_code)
        params_code = ", ".join([representer.parameter(p, indent = 0) for p in self.parameters])
        lines = [
            "@wf.action_def",
            "def {}({}) -> {}:".format(self.name, params_code, type_code),
            "    # User defined action cen not been represented.",
            "    pass"]
        return "\n".join(lines)







# need different way to instantiate a defined dataclass type


# class Zip(dev._ActionBase):
#     # zip number of lists into single list of lists
#
# class ZipToClass(dev.ActionBase):
#     # given a dict of lists convert to list of dicts

