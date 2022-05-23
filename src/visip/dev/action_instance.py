import enum
import attr
from typing import *
from . import base
from .parameters import ActionParameter
from ..action.constructor import Value, A_list, A_dict, A_tuple
from .type_inspector import TypeInspector
from enum import IntEnum
from .exceptions import ExcTypeBase, ExcArgumentBindError, ExcConstantKey, ExcActionExpected
from ..code.dummy import Dummy, DummyAction, DummyWorkflow
from . import dtype


class ActionInputStatus(enum.IntEnum):
    error_default =  -5  # Invalid default value.
    error_impl  = -4     # Missing type hint or other error in the action implementation.
    missing     = -3     # missing value
    error_value = -2     # error input passed, can not be wrapped into an action
                         # actually not used during wrapping in 'wrap.into_action'
                         # TODO: unify error reporting.
    error_type  = -1     # type error
    none        = 0      # not checked yet
    seems_ok    = 1      # correct input, type not fully specified or involving Any
    ok          = 2      # correct input, possibly involving conversions to Named types
    exact       = 3      # Named types exact match



@attr.s(auto_attribs=True)
class ActionArgument:
    """
    Represents association of an argument to the parameters of an action.
    Contain data from usual function call including: the function/action,
    index or key of the argument binding, the argument itself in terms of connected result of other ActionCall
    """
    action_call: 'ActionCall'
    # identification of the action instance within the workflow
    # TODO: use hash instead
    index: int
    # Position binding, position of a positional argument, None for key binding.
    key: str
    # Key binding. None for positional binding.
    value: 'ActionCall'
    # identification of the binded argument == action call within the workflow
    # TODO: use hash
    parameter: ActionParameter
    # reference to associated parameter
    is_default: bool = None
    # 'argument' set as Value(default)
    status: ActionInputStatus = ActionInputStatus.missing
    # binding correctenss status
    type_exception: ExcTypeBase = None
    # exception or other kind of error specification
    call_type: Optional[dtype.DType] = None
    # parameter.type with unique typevar instances.
    actual_type: Optional[dtype.DType] = None
    # Type after workflow check and possible typevar substitutions.
    # @property
    # def value(self):
    #     if self._value is None:
    #         return dtype.empty
    #     else:
    #         return self._value

class ActionCall:
    @staticmethod
    def action_wrap(value: Any) -> 'ActionCall':
        if isinstance(value, ActionCall):
            return value
        else:
            return ActionCall.create(Value(value))

    @staticmethod
    def _into_action(value: Any) -> Any:
        """
        Recursively unwrap data,
        :param value:
        :return:
        """
        ti = TypeInspector()

        if isinstance(value, Dummy):
            action_call = value._value
            assert isinstance(action_call, ActionCall)
            return action_call
        elif isinstance(value, (DummyAction, DummyWorkflow)):
            action = value._action_value
            assert isinstance(action, dtype._ActionBase)
            return action
        elif value is dtype.empty:
            return value
        elif type(value) is list:
            args = [ActionCall._into_action(val) for val in value]
            if any(isinstance(arg, ActionCall) for arg in args):
                # some arg is a result of an ActionCall
                args = [ActionCall.action_wrap(arg) for arg in args]
                return ActionCall.create(A_list(), *args)
            else:
                # just values
                return args
        elif type(value) is tuple:
            args = [ActionCall._into_action(val) for val in value]
            if any(isinstance(arg, ActionCall) for arg in args):
                # some arg is a result of an ActionCall
                args = [ActionCall.action_wrap(arg) for arg in args]
                return ActionCall.create(A_tuple(), *args)
            else:
                # just values
                return tuple(args)
        elif type(value) is dict:
            kwargs = [(ActionCall._into_action(key), ActionCall._into_action(val)) for key, val in value.items()]
            for k, v in kwargs:
                if isinstance(k, ActionCall):
                    raise ExcConstantKey(str(k))
            if any(isinstance(arg, ActionCall) for k, arg in kwargs):
                kwargs = [ActionCall.into_action((k, arg)) for k, arg in kwargs]
                return ActionCall.create(A_dict(), *kwargs)
            else:
                return dict(kwargs)
        elif value is None \
                or ti.is_base_type(type(value)) \
                or ti.is_enum(type(value)) \
                or ti.is_dataclass(type(value)):
            return value
        elif isinstance(value, ActionCall):
            return value
        else:
            raise ExcActionExpected("Can not wrap into action, value: {}".format(str(value)))

    @staticmethod
    def into_action(value: Any) -> 'ActionCall':
        """
        In value remove recursively all Dummy and DummyAction wrappers.
        Convert all list, dict, tuple, dataclass having at leas one ActionCall
        argument into appropriate constructor actions.
        Wrap data values (without any action calls) into Value action.
        Wrap the None value as well.
        Return the ActionCall.

        :param value: Value can be raw value, List, Tuple, Dummy, etc.
        :return: ActionCall that can be used as the input to other action instance.
        """
        unwrapped = ActionCall._into_action(value)
        return ActionCall.action_wrap(unwrapped)

    """
    The call of an action within a workflow. ActionInstance objects are vertices of the
    call graph (DAG).
    """
    def __init__(self, action: dtype._ActionBase, name : str = None) -> None:
        self.name = name
        """ The instance name. (i.e. name of variable containing this instance.)
            This also seerves as a unique id within the workflow.
            TODO: separate ActonCall and assignment to a variable
        """
        self._proper_instance_name = False
        """ Indicates the instance name provided by user. Not generic name."""

        self.action = action
        """ The Action (instance of _ActionBase), have defined parameter. """

        self._type_var_map = {}
        """Map from TypeVars used in action definition to TypeVars used in Workflow type check."""
        self.call_output_type, self._type_var_map = dtype.substitute_type_vars(self.output_type, self._type_var_map, create_new=True)
        """Call output type substituted unique TypeVars."""
        self.actual_output_type = None
        """Actual output type after substitution of TypeVars with concrete type in Workflow type check."""

        self._arguments : List[ActionArgument] = []
        # input values - connected action calls, every represented by ActionArgument (action_call, status, param)
        # ActionCall is marked invalid by setting _arguments to None


    @property
    def arguments(self):
        for arg in self._arguments:
            if arg.value is not None and arg.value.is_invalid:
                arg.value = None
                arg.status = ActionInputStatus.missing
        return self._arguments

    @property
    def is_invalid(self):
        return self._arguments is None

    def mark_invalid(self):
        self._arguments = None

    @property
    def id_args_pair(self):
        return self._arg_split(self.arguments)

    def return_type_have_attributes(self):
        assert isinstance(self.action.output_type, dtype.DType)
        return dtype.TypeInspector().have_attributes(self.action.output_type)

    @staticmethod
    def create(action, *args, **kwargs):
        """
        Create an action instance with given arguments.
        :param args:
        :param kwargs:
        :return:
        TODO: Make a global error buffer, report errors there so that
        all parsing can proceed, possibly we can stop at given number of errors.
        Then we can remove create_and_check
        """
        assert isinstance(action, dtype._ActionBase), f"{action.__name__}, {action.__class__}"
        instance = ActionCall(action)
        instance.errors = instance.set_inputs(args, kwargs)
        if instance.errors:
            # TODO: report also missing arguments, possibly in _arg_split
            arg, err = instance.errors[0]
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

    def make_argument(self, i_arg: Optional[int], param: ActionParameter, value: Optional['ActionCall'], key:str = None ) -> ActionArgument:
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
                value = ActionCall.into_action(value)
                # if TypeInspector().is_subtype(value.output_type, param.type):
                #     status = ActionInputStatus.default
                #
                # else:
                #     return ActionArgument(param, value, is_default, ActionInputStatus.error_default)
        status = ActionInputStatus.seems_ok
        if value is None:
            status = ActionInputStatus.missing
            #return self._make_argument(i_arg, key, param, None)_ActionArgument(param, None, False, ActionInputStatus.missing)
        elif param.type is None:
            status = ActionInputStatus.error_impl
            #return ActionArgument(param, value, is_default, ActionInputStatus.error_impl)
        else:
            assert isinstance(value, ActionCall), type(value)
            check_type = param.type


            if dtype.TypeInspector().is_constant(param.type):
                check_type = dtype.TypeInspector().constant_type(param.type)
                if not isinstance(value, Value):
                    status = ActionInputStatus.error_value
                    #return ActionArgument(param, value, is_default, ActionInputStatus.error_value)

            if TypeInspector().is_subtype(value.output_type, check_type):
                status = ActionInputStatus.seems_ok
            else:
                status = ActionInputStatus.error_type

        call_type, self._type_var_map = dtype.substitute_type_vars(param.type, self._type_var_map, create_new=True)

        return ActionArgument(self, i_arg, key, value, param, is_default, status, None, call_type)

    @staticmethod
    def _arg_split(bound_args):
        args = []
        kwargs = {}
        for ia, a in enumerate(bound_args):
            if a.index is None:
                assert a.key is not None
                kwargs[a.key] = ia
            else:
                args.append(ia)
        return args, kwargs

    class BindError(IntEnum):
        KEYWORD_FOR_POSITIONAL_ONLY = 1
        DUPLICATE = 2
        POSITIONAL_OVER = 3
        KEYWORD_OVER = 4
        MISSING = 5

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
        self._arguments, errors = self.bind(args, kwargs)
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

        bound_args = list()
        parameters = iter(self.parameters.parameters)
        #parameters_ex = ()
        arg_vals = enumerate(iter(args))
        errors = []

        while True:
            # Let's iterate through the positional arguments and corresponding
            # parameters
            try:
                i_arg, arg_val = next(arg_vals)
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
                    args_over.extend([v for i,v in arg_vals])
                    errors.extend([(av, self.BindError.POSITIONAL_OVER) for av in args_over])
                    break
                else:
                    if param.kind == param.VAR_POSITIONAL:
                        # We have an '*args'-like argument, let's fill it with
                        # all positional arguments we have left and move on to
                        # the next phase
                        values = [(i_arg, arg_val)]
                        values.extend(arg_vals)
                        for i, v in values:
                            arg = self.make_argument(i, param, v) # try without parem, getting it from self.parameters
                            bound_args.append(arg)
                        break

                    if param.name in kwargs:
                        errors.append((arg_val, self.BindError.DUPLICATE))

                    arg = self.make_argument(i_arg, param, arg_val)
                    bound_args.append(arg)

        # Now, we iterate through the remaining parameters to process
        # keyword arguments
        kwargs_param = None
        #for param in itertools.chain(parameters_ex, parameters):
        for param in parameters:
            if param.kind == param.POSITIONAL_ONLY:
                errors.append( (arg, self.BindError.MISSING_POSSITIONAL) )

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
                bound_args.append( self.make_argument(None, param, None, key=param.name))
            else:
                if param.kind == param.POSITIONAL_ONLY:
                    errors.append((arg_val, self.BindError.KEYWORD_FOR_POSITIONAL_ONLY))
                # KEYWORD or KEYWORD_OR_POSITIONAL
                bound_args.append(self.make_argument(None, param, arg_val, key=param.name))

        # trailing kwargs with no parameters
        if kwargs:
            if kwargs_param is not None:
                # Process our '**kwargs'-like parameter
                # can not use wrap.into_action due to circular dependencies
                for k, v in kwargs.items():
                    bound_args.append(self.make_argument(None, param, v, key=k))
            else:
                errors.extend([(arg, self.BindError.KEYWORD_OVER) for k, arg in kwargs.items()])

        return bound_args, errors

    def check_arguments(self):
        errors = []
        assert len(self.arguments) == len(self.action.parameters)
        for a in self.arguments:
            if a.status < ActionInputStatus.error_type:
                errors.append((a, self.BindError.MISSING))
        return errors


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
        """
        name_for_val = lambda v : "__empty__" if v is None else v.get_code_instance_name()
        arg_names = [name_for_val(arg.value) for arg in self.arguments]
        arg_values = [arg.value for arg in self.arguments]

        full_action_name = representer.make_rel_name(self.action.__module__, self.action.__name__)
        expr_format = self.action.call_format(representer, full_action_name, arg_names, arg_values)
        return expr_format
