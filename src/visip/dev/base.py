import enum
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
    def __init__(self, action_name = None ):
        self.task_type = TaskType.Atomic
        self.is_analysis = False
        self.name = action_name or self.__class__.__name__
        self._module = "wf"
        # Module where the action is defined.
        self.parameters = Parameters()
        # Parameter specification list, class attribute, no parameters by default.
        self.output_type = None
        # Output type of the action, class attribute.
        # Both _parameters and _outputtype can be extracted from type annotations of the evaluate method using the _extract_input_type.
        self._extract_input_type()

    @property
    def module(self):
        """
        Module prefix used in code generationn.
        :return:
        """
        assert self._module
        return self._module


    def _extract_input_type(self, func=None, skip_self=True):
        """
        Extract input and output types of the action from its evaluate method.
        Only support fixed numbeer of parameters named or positional.
        set: cls._input_type, cls._output_type
        """
        if func is None:
            func = self._evaluate
        self.parameters, self.output_type = extract_func_signature(func, skip_self)
        pass

    # def hash(self):
    #     """
    #     Hash of the atomic action. Should be unique for the particular Action instance.
    #     """
    #     return data.hash(self.name)


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


    def format(self, representer, full_action_name, arg_names):
        """
        Return a format string for the expression that constructs the action.
        :param n_args: Number of arguments, number of placeholders. Can be None if the action is not variadic.
        :return: str, format
        Format contains '{N}' placeholders for the given N-th argument, the named placeholer '{VAR}'
        is used for the variadic arguments, these are substituted as an argument list separated by comma and space.
        E.g. "Action({0}, {1}, {})" can be expanded to :
        "Action(arg0, arg1, arg2, arg3)"
        """
        args = []
        for i, arg in enumerate(arg_names):
            param = self.parameters.get_index(i)
            assert param is not None
            args.append( (param.name, arg) )
        return representer.action_call(full_action_name, args)



    def validate(self, inputs):
        return self.evaluate(inputs)









# need different way to instantiate a defined dataclass type


# class Zip(dev._ActionBase):
#     # zip number of lists into single list of lists
#
# class ZipToClass(dev.ActionBase):
#     # given a dict of lists convert to list of dicts

