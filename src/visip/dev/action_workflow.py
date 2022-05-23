import attr
import enum
from typing import *
from typing import Any, Optional
from . import base, data
from . import dfs
from . import meta
from . import exceptions
from . import dtype
from .action_instance import ActionCall, ActionArgument, ActionInputStatus
from ..action.constructor import _ListBase, Value
from .parameters import Parameters, ActionParameter
from .extract_signature import _extract_signature
from ..dev.tools import TaskBinding
from ..action.slots import _SlotCall, _Slot   # provide to GUI

"""
Implementation of the Workflow composed action.
- creating the 
"""


class _Result(_ListBase):
    """
     Auxiliary result action.
     Takes arbitrary number of inputs, at least one input must be provided.
     Returns the first input, other inputs are used just for their side effects (using the Save action).

     TODO: Decide if we really want side effect values.
     Workflow decorator automatically connects all Save actions to the ignored result inputs.

    """

    def __init__(self, out_type):
        super().__init__(action_name='result')
        self.action_kind = base.ActionKind.Generic
        params = []
        params.append(ActionParameter(name="result", p_type=out_type, default=ActionParameter.no_default))
        # The return value, there should be always some return value, as we want to use "functional style".
        params.append(ActionParameter(name='args', p_type=dtype.TypeVar(name="U"), default=ActionParameter.no_default,
                                      kind=ActionParameter.VAR_POSITIONAL))
        self._parameters = Parameters(params, return_type=out_type)
        # The "side effects" of the workflow.
        # TODO: Do we realy need this? We should rather introduce an action Head(*args): return args[0], that way one can do desired efect explicitly
        # TODO: suport multiple return values ( better in GUI)

    def _evaluate(self, *args, **kwargs):
        return args[0]

    def call_format(self, representer, action_name, arg_names, arg_values):
        return representer.format("return", representer.token(arg_names[0]))


class _ResultCall(ActionCall):
    """ Auxiliary result action instance, used to treat the result connecting in the consistnet way."""
    def __init__(self, output_action, out_type):
        super().__init__(_Result(out_type), "__result__")
        self.set_inputs([output_action])


class WorkflowTypeErrorItem:
    def __init__(self, call, arg, subtype, type):
        self.call = call
        self.arg = arg
        self.subtype = subtype
        self.type = type

    def __repr__(self):
        return "In {} {}, {} is not subtype of {}".format(self.call, self.arg, self.subtype, self.type)


class _Workflow(meta.MetaAction):
    """
    Represents a composed action.
    - Allows composition of the actions into a DAG
    - Is a child of _ActionBase, encapsulates its internal structure.
    - All actions are kept in the self._action_calls set.
    - action calls connected to the result are are topologicaly sorted in the 'update' method
      and stored in correct order in self._sorted_calls.
    - action_calls can be freely renamed as workflow makes name -> action_call dict only temporally
      (the. name_to_action_call property)
    TODO:
    - use DAG based signature, but use types from function signature to set them to slots and to the return type.
    - similar functionality should be available from GUI
    """

    class Status(enum.IntEnum):
        unknown = 0
        ok = 1
        error_type = -1  # contains ActionArgument with ActionInputStatus.missing
        error_missing = -3  # some missing arguments
        cycle = -4  # update detected a cycle
        no_result = -10  # uncomplete initialization from function

    @classmethod
    def from_source(cls, func):
        # Returns instance with setup signature, but missing actions.
        # _Workflow.initialize_from_function(func) has to be called to full initialization
        new_workflow = cls(func.__name__, func.__module__)
        new_workflow.set_signature_from_function(func)
        return new_workflow

    def __init__(self, name, module=None):
        """
        Worflow minimal constructor, full setting of the workflow should be done through modifiers:
        - initialize_from_function
        - insert_slot, remove_slot, move_slot (could be possibly removed or implemented by outher two
        - set_action_inputs - modification of the internal ActionCall connections

        :param name:
        :param slots:
        :param result:
        :param params:
        :param output_type:
        """
        super().__init__(name)
        self.__name__ = name
        if module is None:
            module = 'no_module'
        self.__module__ = module
        # Name of the module were the workflow is defined.

        self._parameters = Parameters([])
        # Signature of the workflow.
        self._slots = []
        # slots represents the parameters in the DAG of action calls
        # we should keep slots corresponding to the parameters
        # however we must preserve their instances so that we do not break action call links
        # no initial parameters, nor slots
        self._status = self.Status.unknown
        # Result of last update()

        self._result_call = None
        self.set_result_action(ActionCall.create(Value(None)), self._slots)
        # Result ActionCall, initaliy returning None
        # calls self.update()

        #######################
        # internal structures
        self._action_calls = {self._result_call}
        # Dict:  unique action instance name -> action instance.
        self._sorted_calls: List[ActionCall] = []
        # topologically sorted action instance names (result last)
        self._type_var_map = {}
        # type_var mapping, define lower limit of TypeVar, in algorithm may be raised, like T -> Int to T -> Union[Int, Str]
        self._type_var_restraints = {}
        # type_var restraints, define upper limit of TypeVar, in algorithm may be lowered, like T -> Union[Int, Str] to T -> Int
        self._type_error_list = []
        # list of errors after _check_types
        self._unable_check_types = False
        # if True types cannot be checked


    @property
    def result_call(self):
        return self._result_call

    @property
    def action_call_dict(self):
        return {ac.name: ac for ac in self._action_calls}

    @property
    def slots(self):
        return self._slots

    @property
    def is_valid(self) -> bool:
        assert self._status != self.Status.unknown
        return self._status == self.Status.ok

    @property
    def status(self):
        return self._status

    def action_hash(self):
        self.update()
        a_hash = data.hash(self.name)
        for acall in self._sorted_calls:
            a_hash = data.hash(acall.action.action_hash(), previous=a_hash)
        return a_hash


    def set_signature_from_function(self, func):
        #try:
        func_signature = _extract_signature(func, omit_self=True)
        # except exceptions.ExcTypeBase as e:
        #     raise exceptions.ExcTypeBase(f"Wrong signature of workflow:  {func.__module__}.{func.__name__}") from e
        func_signature.process_empty(lambda var: dtype.TypeVar(origin_type=dtype.EmptyType, name="__Slot__"))
        self._parameters = func_signature

        self._status = self.Status.no_result

    def set_result_action(self, action_call, slots):
        if action_call is None:
            self._result_call = None
            self._status = self.Status.no_result
        else:
            self._slots = slots
            self._result_call = _ResultCall(action_call, self.parameters.return_type)
            self._status = self.Status.unknown
            if self.update() != self.Status.ok:
                raise exceptions.ExcInvalidWorkflow(f"Workflow status: {self.status}")

    def update(self):
        """
        DFS through the workflow DAG given be the result action:
        - set unique action call names
        - set back references to action calls connected to outputs: action.output_actions
        - make topology sort of action calls
        - update list of action calls
        :param result_instance: the result action
        :return: True in the case of sucessfull update, False - detected cycle
        """
        if self._status == self.Status.no_result:
            return self.Status.no_result

        self._status = self.Status.ok
        actions = set()
        topology_sort = []
        instance_names = {}

        def construct_postvisit(action_call):
            #
            # remove obsolate slots

            # get instance name proposal
            if action_call.name is None:
                name_base = action_call.action_name
                instance_names.setdefault(name_base, 1)
            else:
                name_base = action_call.name

            # set unique instance name
            if name_base in instance_names:
                action_call.name = "{}_{}".format(name_base, instance_names[name_base])
                instance_names[name_base] += 1
            else:
                action_call.name = name_base
                instance_names[name_base] = 0

            actions.add(action_call)
            topology_sort.append(action_call)
            # TODO: check if the Action call is _slot, check that it is in self._slots
            # outer slots

        def check_argument(arg: ActionArgument) -> ActionCall:
            if arg.status < ActionInputStatus.error_type:
                # TODO: force strong type check when types are ready
                self._status = min(self._status, arg.status)
                return None
            return arg.value

        good_dfs = dfs.DFS(neighbours=lambda action_call: (check_argument(arg) for arg in action_call.arguments),
                           postvisit=construct_postvisit).run([self._result_call])
        if not good_dfs:
            self._status = self.Status.cycle

        self._action_calls = actions
        self._sorted_calls = topology_sort

        if self._status != self.Status.cycle:
            #print("Check WF ", self.name)
            self._check_types()

        return self.status

    def _check_types(self):
        self._type_var_map = {}
        self._type_var_restraints = {}
        types_ok = True
        self._type_error_list = []
        self._unable_check_types = False

        # backward
        for call in reversed(self._sorted_calls):
            if isinstance(call, _SlotCall):
                # restraints in _SlotCall convert to type_var map
                vts = call._type_var_map.values()
                for vt in vts:
                    if vt in self._type_var_restraints:
                        self._type_var_map[vt] = self._type_var_restraints[vt]
                continue

            for arg in call.arguments:
                type_var_map_back = self._type_var_map
                type_var_restraints_back = self._type_var_restraints
                try:
                    b, self._type_var_map, self._type_var_restraints = dtype.is_subtype_map(
                        arg.value.call_output_type, arg.call_type, self._type_var_map, self._type_var_restraints)
                    if not b:
                        types_ok = False
                        arg.status = ActionInputStatus.error_type
                        self._type_error_list.append(WorkflowTypeErrorItem(call, arg, arg.value.call_output_type, arg.call_type))
                        self._type_var_map = type_var_map_back
                        self._type_var_restraints = type_var_restraints_back
                except TypeError:
                    self._unable_check_types = True
                    arg.status = ActionInputStatus.seems_ok
                    self._type_var_map = type_var_map_back
                    self._type_var_restraints = type_var_restraints_back

        # if not types_ok:
        #     raise TypeError("Error in workflow typing.")

        self._type_var_map = dtype.expand_var_map(self._type_var_map)

        # forward
        for call in self._sorted_calls:
            for arg in call.arguments:
                arg.actual_type, _ = dtype.substitute_type_vars(arg.call_type, self._type_var_map)
            call.actual_output_type, _ = dtype.substitute_type_vars(call.call_output_type, self._type_var_map)

    def dependencies(self):
        """
        :return: List of used actions (including workflows and converters).
        """
        return [v.action_name() for v in self._action_calls]

    @attr.s(auto_attribs=True)
    class InstanceRepr:
        code: 'format.Format'
        # A formatting string for the code.
        subst_prob: float
        # Preference of inline substitution.
        n_uses: int = 0

        def prob(self):
            if self.n_uses > 1:
                return 0.0
            else:
                return self.subst_prob

    def code_of_definition(self, representer):
        """
        Represent workflow by its source.
        :return: list of lines containing representation of the workflow as a decorated function.
        Code sugar:
        1. substitute all results used just once in single parameter actions
        2. try to substitute to multiparameter actions, check line length.

        TODO:
        - return short expressions without local variables
        - omit self if not necessary, or require it always
        - missing self local vars
        """
        indent = representer.n_indent * " "

        decorator = 'analysis' if self.is_analysis else 'workflow'
        params = [base._VAR_]
        for i, param in enumerate(self.parameters):
            assert (param.name == self._slots[i].name), f"{param.name} != {self._slots[i].name}"
            type_anot = representer.str_unless(': ', representer.type_code(param.type))

            param_def = f"{param.name}{type_anot}"
            params.append(param_def)
        result_hint = representer.str_unless(' -> ', representer.type_code(self.parameters.return_type))
        head = f"def {self.name}({', '.join(params)}){result_hint}:"

        body = [
                f"@{representer.make_rel_name('visip.code.decorators', decorator)}",
                head
        ]

        # Make dict: full_instance_name -> (format, [arg full names])
        inst_order = []
        inst_exprs = {}
        for action_call in self._sorted_calls:
            full_name = action_call.get_code_instance_name()
            subst_prob = action_call.code_substitution_probability()
            code = action_call.code(representer)
            if code:
                inst_repr = self.InstanceRepr(code, subst_prob)
                for name in code.placeholders:
                    if name in inst_exprs:
                        inst_exprs[name].n_uses += 1
                inst_order.append(full_name)
            else:
                inst_repr = self.InstanceRepr(None, 0.0)
            inst_exprs[full_name] = inst_repr

        # Delete unused calls without proper name.
        for inst_name, inst_repr in list(inst_exprs.items()):
            if inst_repr.n_uses == 0 and inst_repr.subst_prob > 0.0:
                del inst_exprs[inst_name]

        # Substitute single used, single param instances
        for full_inst in reversed(inst_order):
            if full_inst in inst_exprs:
                inst_repr = inst_exprs[full_inst]
                placeholders = inst_repr.code.placeholders
                while len(placeholders) == 1:
                    arg_full_name = placeholders.pop()
                    if arg_full_name in inst_exprs:
                        arg_repr = inst_exprs[arg_full_name]
                        if arg_repr.subst_prob > 0.0 and arg_repr.n_uses < 2:
                            inst_repr.code = inst_repr.code.substitute(arg_full_name, arg_repr.code)
                            del inst_exprs[arg_full_name]
                        else:
                            break

        # Substitute into multi arg actions
        for full_inst in reversed(inst_order):
            if full_inst in inst_exprs:
                inst_repr = inst_exprs[full_inst]
                # subst_candidates works as a priority queue

                while True:
                    subst_candidates = [(inst_exprs[n].code.len_est(), n)
                                        for n in inst_repr.code.placeholders if n in inst_exprs and inst_exprs[n].prob() > 0]
                    if not subst_candidates:
                        break
                    len_est, name = min(subst_candidates)
                    # substitute, update substitute_candidates
                    new_code = inst_repr.code.substitute(name, inst_exprs[name].code)
                    if new_code.len_est() > 120:
                        break
                    inst_repr.code = new_code
                    del inst_exprs[name]
                    if new_code.len_est() > 100:
                        break

        # output code
        for full_inst in inst_order:
            if full_inst in inst_exprs:
                inst_repr = inst_exprs[full_inst]
                if inst_repr.code:
                    line = "{}{} = {}".format(indent, full_inst, inst_repr.code.final_string())
                    body.append(line)

        assert len(self._result_call.arguments) > 0
        result_action_call = self._result_call.arguments[0].value
        body.append("{}return {}".format(indent, result_action_call.get_code_instance_name()))
        return "\n".join(body)

    def insert_slot(self, i_slot: int, name: str, p_type: dtype.DType,
                    default: Any = ActionParameter.no_default,
                    kind: int = ActionParameter.POSITIONAL_OR_KEYWORD) -> None:
        """
        Insert a new parameter on i_th position shifting the slots starting form i-th position.
        """
        assert len(self._slots) == len(self._parameters)
        assert 0 <= i_slot < len(self._slots) + 1
        params = list(self._parameters)
        self._slots.insert(i_slot, _SlotCall(name, p_type))
        params.insert(i_slot, ActionParameter(name, p_type, default, kind))
        self._parameters = Parameters(params, self._parameters.return_type)
        # no need to update

    def remove_slot(self, i_slot: int) -> None:
        """
        Remove parameter at position 'i'.
        """
        slot = self._slots.pop(i_slot)
        slot.mark_invalid()

        params = list(self._parameters)
        params.pop(i_slot)
        self._parameters = Parameters(params, self._parameters.return_type)

    def remove_action(self, action_call: ActionCall) -> '_Workflow.Status':
        # TODO: check here and for other actions, that they are part of the workflow
        action_call.mark_invalid()
        return self.update()

    def move_slot(self, from_pos, to_pos):
        """
        Move the slot at position 'from_pos' to the position 'to_pos'.
        Slots in between are shifted
        TODO: remove this function
        """
        assert 0 <= from_pos < len(self._slots)
        assert 0 <= to_pos < len(self._slots)
        params = list(self._parameters)
        from_slot = self._slots[from_pos]
        from_param = params[from_pos]
        direction = 1 if to_pos > from_pos else -1

        for i in range(from_pos, to_pos, direction):
            self._slots[i] = self._slots[i + direction]
            params[i] = params[i + direction]
        self._slots[to_pos] = from_slot
        params[to_pos] = from_param
        self._parameters = Parameters(params, self._parameters.return_type)
        # no need to update

    def set_action_input(self, action_call: ActionCall, i_arg: int, input_action: Optional[ActionCall],
                         key: str = None) -> bool:
        """
        Set positional or keyword argument (i_arg, key) of the 'action_call' to the 'input_action'.
        Unset the argument if input_action is None.
        TODO:
        - change interface to identify the action by a hash (simpler association with graphical elements)
        - rename and introduce key binding variant

        E.g. wf.set_action_input(list_1, 0, slot_a)
        """
        args, kwargs = action_call.id_args_pair

        if i_arg is not None:
            # positional argument
            try:
                id_arg = args[i_arg]
            except IndexError:
                var_param = action_call.parameters.var_positional
                if var_param is None:
                    return False  # raise IndexError
                elif input_action is not None:
                    new_arg = action_call.make_argument(i_arg, var_param, input_action)
                    id_arg = len(args)
                    action_call.arguments.insert(id_arg, new_arg)
            else:
                param = action_call.arguments[id_arg].parameter
                if input_action is None and param.kind == ActionParameter.VAR_POSITIONAL:
                    # remove unset variadic arguments
                    action_call.arguments.pop(id_arg)
                    # shift other positional arguments
                    while id_arg < len(action_call.arguments) and action_call.arguments[id_arg].key is None:
                        action_call.arguments[id_arg].index -= 1
                        assert action_call.arguments[id_arg].index == id_arg
                        id_arg += 1

                else:
                    # keep all non variadic arguments (marked as missing)
                    action_call.arguments[id_arg] = action_call.make_argument(i_arg, param, input_action)
        else:
            # keyword argument
            assert key is not None
            try:
                id_arg = kwargs[key]
            except KeyError:
                var_keyword = action_call.parameters.var_keyword
                if var_keyword is None:
                    return False  # raise IndexError
                elif input_action is not None:
                    new_arg = action_call.make_argument(None, var_keyword, input_action, key=key)
                    action_call.arguments.append(new_arg)
            else:
                param = action_call.arguments[id_arg].parameter
                if input_action is None and param.kind == ActionParameter.VAR_KEYWORD:
                    # remove unset variadic arguments
                    action_call.arguments.pop(id_arg)
                else:
                    # keep all non variadic arguments (marked as missing)
                    action_call.arguments[id_arg] = action_call.make_argument(None, param, input_action, key=key)

        if self.update() == self.Status.cycle:
            # revert
            assert self.set_action_input(action_call, i_arg, None, key=key)
            # return False only in the case of cycle, otherwise keep going
            # as this method is meant for the GUI use
            return False

        return True

    def set_result_type(self, result_type):
        """
        TOOD: Test after introduction of typing.
        :param result_type:
        :return:
        """
        self.result_call.output_type = result_type

    def expand(self, task, task_creator, cache):
        """
        Expansion of the composed task with given data inputs (possibly None if not evaluated yet).
        :param inputs: List[Task]
        :param task_creator: Dependency injection method for creating tasks from action instances:
            task_creator(action_call, input_tasks)
        :param cache: Result cache instance
        :return:
            None if can not be expanded yet.
            List of created actions.

            In particular slots are named by corresponding parameter name and result task have name '__result__'
        """
        if self.update() != self.Status.ok:
            raise exceptions.ExcInvalidWorkflow(self.status)
        childs = {}
        tasks = {}
        assert len(self._slots) == len(task.inputs)
        for slot, input in zip(self._slots, task.inputs):
            # shortcut the slots
            # task = task_creator(slot.name, Pass(), [input])
            tasks[slot.name] = input
        for action_call in self._sorted_calls:
            if isinstance(action_call, _SlotCall):
                continue
            # TODO: eliminate dict usage, assign a call rank to the action calls
            # TODO: use it to index tasks in the resulting task list 'childs'
            arg_tasks = [tasks[arg.value.name] for arg in action_call.arguments]
            task_binding = TaskBinding(action_call.name, action_call.action, action_call.id_args_pair, arg_tasks)
            child_task = task_creator(task_binding)
            childs[action_call.name] = child_task
            tasks[action_call.name] = child_task
        return childs
