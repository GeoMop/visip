import enum
import attr
from typing import *
from . import base
from .parameters import ActionParameter
from ..action.constructor import Value

from .type_inspector import TypeInspector
from enum import IntEnum
from .tools import decompose_arguments, compose_arguments, ArgsPair
from .exceptions import ExcTypeBase, ExcArgumentBindError

class ActionInputStatus(enum.IntEnum):
    error_impl  = -4     # Missing type hint or other error in the action implementation.
    missing     = -3     # missing value
    error_value = -2     # error input passed, can not be wrapped into an action
                         # actually not used during wrapping in 'wrap.into_action'
                         # TODO: unify error reporting.
    error_type  = -1     # type error
    none        = 0      # not checked yet
    seems_ok    = 1      # correct input, type not fully specified
    ok          = 2      # correct input


@attr.s(auto_attribs=True)
class ActionArgument:
    # TODO: try to remove, parameter and is_deault as it seems to not been used after ActionArgument is created
    parameter: ActionParameter
    value: Optional['ActionCall'] = None
    is_default: bool = False
    status: ActionInputStatus = ActionInputStatus.missing
    type_exception: ExcTypeBase = None



class ActionCall:
    """
    The call of an action within a workflow. ActionInstance objects are vertices of the
    call graph (DAG).
    """
    def __init__(self, action : base._ActionBase, name : str = None) -> None:
        self.name = name
        """ The instance name. (i.e. name of variable containing this instance.)
            This also seerves as a unique id within the workflow.
            TODO: separate ActonCall and assignment to a variable
        """
        self._proper_instance_name = False
        """ Indicates the instance name provided by user. Not generic name."""

        self.action = action
        """ The Action (instance of _ActionBase), have defined parameter. """
        
        self.args_in = [] 
        self.kwargs_in = {}
        # positional and keyword arguments passed to the call
        # only these can be modified, rest is produced by check
        self._bind_args_dict = {}
        # dictionary that binds parameter names to arguments after self.bind
        self._id_args_pair : ArgsPair[int] = None
        # args and kwargs IDs used to pass values,
        # None - not valid ActionCall
        self._arguments : List[ActionArgument] = []
        # input values - connected action calls, avery represented by ActionArgument (action_call, status, param)

        """ Inputs connected to the action parameters."""
        self._output_actions = []
        """ Actions connected to the output. Set during the workflow construction."""
        # TODO: remove, rather use a set in te DFS if necessart

    @property
    def arguments(self):
        return self._arguments

    def return_type_have_attributes(self):
        return TypeInspector().have_attributes(self.action.output_type)

    # def _fill_args(self):
    #     """
    #     Fill unset arguments.
    #     :return:
    #     TODO: update for new args
    #     """
    #     while len(self.arguments) < len(self.parameters):
    #         param = self.parameters.at(len(self.arguments))
    #         if param is None or param.name is None:
    #             break
    #         self.arguments.append(self.make_argument(param, None))


    @staticmethod
    def create(action, *args, **kwargs):
        """
        Create an action instance with given arguments.
        :param args:
        :param kwargs:
        :return:
        """
        if not isinstance(action, base._ActionBase):
            pass
        assert isinstance(action, base._ActionBase), f"{action.__name__}, {action.__class__}"
        instance = ActionCall(action)
        errors = instance.set_inputs(args, kwargs)
        if errors:
            # TODO: report also missing arguments, possibly in _arg_split
            arg, err = errors[0]

            raise ExcArgumentBindError(f"Action {str(action)}, binding error: {str(err)}, for argument: {arg}.")
        return instance


    @property
    def parameters(self):
        return self.action.parameters

    @property
    def output_type(self):
        return self.action.output_type

    @property
    def action_name(self):
        return self.action.name

    @property
    def have_proper_name(self):
        return self._proper_instance_name

    def make_argument(self, param, value: Optional['ActionCall']):
        """
        Make ActionArgument from the ActionParameter and a value or ActionCall.
        - possibly get default value
        - check result type of ActionCall
        :param param:
        :param value: ActionCall connected to this argument
        :return:
        """

        is_default = False
        if value is None:
            is_default, value = param.get_default()
            if is_default:
                value = ActionCall.create(Value(value))

        if value is None:
            return ActionArgument(param, None, False, ActionInputStatus.missing)

        assert isinstance(value, ActionCall), type(value)

        check_type = param.type
        if param.type is None:
            return ActionArgument(param, value, is_default, ActionInputStatus.error_impl)
        if TypeInspector().is_constant(param.type):
            if isinstance(value, Value):
                check_type = TypeInspector().constant_type(param.type)
            else:
                return ActionArgument(param, value, is_default, ActionInputStatus.error_value)

        if not TypeInspector().is_subtype(value.output_type, check_type):
            return  ActionArgument(param, value, is_default, ActionInputStatus.error_type)

        return ActionArgument(param, value, is_default, ActionInputStatus.seems_ok)




    def _arg_split(self, bound_args):
        args = []
        kwargs = {}
        for k, a in bound_args.items():
            kind = self.parameters[k].kind
            if kind in (ActionParameter.POSITIONAL_ONLY, ActionParameter.POSITIONAL_OR_KEYWORD):
                args.append(a)
            elif kind == ActionParameter.KEYWORD_ONLY:
                kwargs[k] = a
            elif kind == ActionParameter.VAR_POSITIONAL:
                assert isinstance(a, (list,))
                args.extend(a)
            elif kind == ActionParameter.VAR_KEYWORD:
                assert isinstance(a, (dict,))
                kwargs.update(a)
        return args, kwargs

    class BindError(IntEnum):
        KEYWORD_FOR_POSITIONAL_ONLY = 1
        DUPLICATE = 2
        POSITIONAL_OVER = 3
        KEYWORD_OVER = 4

    InputDict = Dict[str, 'ActionCall']
    InputList = List['ActionCall']
    ErrorArgs = List[Tuple['ActionCall', BindError]]

    def set_inputs(self, args: InputList, kwargs: InputDict = None) -> ErrorArgs:
        """
        Set inputs of an explicit action with fixed number of named parameters.
        input_list: [ input ]  positional arguments.
        input_dict: { parameter_name: input } named arguments

        All arguments must be actions, i.e. constant values must already be wrapped into Value action.
        """
        if kwargs is None:
            kwargs = {}
        self._bind_args_dict, errors = self.bind(args, kwargs)
        args_pair = self._arg_split(self._bind_args_dict)
        self._id_args_pair, self._arguments = decompose_arguments(args_pair)
        return errors

    def bind(self, args, kwargs):
        """
        Set self._arguments, i.e. parameter name to argument dict, according to passed arguments.
        Implementation based on inspect.bind in order to keep the same logic.
        Changes:
        - processing of default values
        - no exceptions, errors are reported as follows:
            - missing paremeter - appropriate status in the ActionArgument.status
            - positional passed as kyword - in remaining args (arg, WRONG_KEYWORD)
            - duplicate parameter - in remaining args (arg, DUPLICATE)
            - remaining positional (arg, POSITIONAL_OVER)
            - remaining keyword (arg, KEYWORD_OVER)
        """

        bound_args = dict()
        parameters = iter(self.parameters.parameters)
        #parameters_ex = ()
        arg_vals = iter(args)
        errors = []

        while True:
            # Let's iterate through the positional arguments and corresponding
            # parameters
            try:
                arg_val = next(arg_vals)
            except StopIteration:
                break
                # No more positional arguments
                # We process remaing parameters in the kwargs loop.
            else:
                # We have a positional argument to process
                try:
                    param = next(parameters)
                except StopIteration:
                    args_over = [arg_val]
                    args_over.extend(arg_vals)
                    errors.extend([(av, self.BindError.POSITIONAL_OVER) for av in args_over])
                    break
                else:
                    if param.kind == param.VAR_POSITIONAL:
                        # We have an '*args'-like argument, let's fill it with
                        # all positional arguments we have left and move on to
                        # the next phase
                        values = [arg_val]
                        values.extend(arg_vals)
                        values = [self.make_argument(param, v) for v in values]
                        tuple_args = tuple(values)
                        bound_args[param.name] = values
                        break

                    if param.name in kwargs:
                        errors.append((arg_val, self.BindError.DUPLICATE))

                    bound_args[param.name] = self.make_argument(param, arg_val)

        # Now, we iterate through the remaining parameters to process
        # keyword arguments
        kwargs_param = None
        #for param in itertools.chain(parameters_ex, parameters):
        for param in parameters:

            if param.kind == param.VAR_KEYWORD:
                # Memorize that we have a '**kwargs'-like parameter
                kwargs_param = param
                continue

            if param.kind == param.VAR_POSITIONAL:
                # Named arguments don't refer to '*args'-like parameters.
                # We only arrive here if the positional arguments ended
                # before reaching the last parameter before *args.
                continue

            try:
                arg_val = kwargs.pop(param.name)
            except KeyError:
                # We have no value for this parameter.  It's fine though,
                # if it has a default value, or it is an '*args'-like
                # parameter, left alone by the processing of positional
                # arguments.
                bound_args[param.name] = self.make_argument(param, None)
            else:
                if param.kind == param.POSITIONAL_ONLY:
                    errors.append((arg_val, self.BindError.KEYWORD_FOR_POSITIONAL_ONLY))
                # KEYWORD or KEYWORD_OR_POSITIONAL
                bound_args[param.name] = self.make_argument(param, arg_val)

        # trailing kwargs with no parameters
        if kwargs:
            if kwargs_param is not None:
                # Process our '**kwargs'-like parameter
                # can not use wrap.into_action due to circular dependencies
                kw = {k : self.make_argument(param, v) for k, v in kwargs.items()}
                bound_args[kwargs_param.name] = kw
            else:
                errors.extend([(arg, self.BindError.KEYWORD_OVER) for k, arg in kwargs.items()])

        return bound_args, errors


    def update_inputs(self, inputs):
        """
        API fro GUI, pass new values of the inputs for current self._id_args_pair.
        Setting any input to None will unbind corresponding parameter.

        Inputs are first converted to args, kwargs using self._id_args_pair and then self.set_inputs is used.

        :param inputs: List of inptus with length of self.arguments
        """
        # TODO: hiw to catch all errors in GUI, yet throw when loading
        # module during evaluation.
        # All errors must set a consistent state before raising an exception
        # all code processing (done during module import) should be without exceptions.
        #

        assert len(inputs) == len(self._arguments)
        args, kwargs = compose_arguments(self._id_args_pair, inputs)
        errors = self.set_inputs(args, kwargs)
        assert len(errors) == 0, "No remaining arguments allowed for GUI"

    # def set_input(self):
    #     assert False, "Removed"
    #     pass

    def set_name(self, instance_name: str):
        """
        Set name of the action instance. Used for code representation
        to name the variable.
        """
        self.name = instance_name
        self._proper_instance_name = True
        return self

    def __str__(self):
        if self.name is None:
            return "{}(...)".format(self.action_name)
        else:
            return self.name
        #code = self.code(representer.Representer())
        #return code.final_string()

    def get_code_instance_name(self):
        if self._proper_instance_name:
            return "{}.{}".format(base._VAR_, self.name)
        else:
            return self.name

    def code_substitution_probability(self):
        """
        Can tune substitution preference dependent on the action.
        :return:
        """
        if self._proper_instance_name:
            return 0.0
        else:
            return 0.5


    def code(self, representer):
        """
        Return a representation of the action instance.
        This is generic representation code that calls the constructor.

        Two

        :param inputs: Dictionary assigning strings to the Action's parameters.
        :param config: String used for configuration, call serialization of the configuration by default.
        :return:
        ( format, [instance names used in format])
        """
        arg_names = [arg.value.get_code_instance_name() for arg in self.arguments]
        arg_values = [arg.value for arg in self.arguments]

        full_action_name = representer.make_rel_name(self.action.__module__, self.action.__name__)
        #print(self.action)
        expr_format = self.action.call_format(representer, full_action_name, arg_names, arg_values)
        return expr_format
