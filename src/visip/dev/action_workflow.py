import attr
from typing import Any
from ..code.unwrap import into_action
from ..code.dummy import Dummy
from . import base
from . import dfs
from . import meta
from . import exceptions
from . import dtype
from ..action.action_factory import ActionFactory
from .action_instance import ActionCall
from ..action.constructor import _ListBase, Value
from . parameters import Parameters, ActionParameter
from .extract_signature import _extract_signature
from ..dev.tools import TaskBinding


"""
Implementation of the Workflow composed action.
- creating the 
"""


class _Slot(base._ActionBase):
    def __init__(self, param_type=None):
        super().__init__("_Slot")
        self._parameters = Parameters([], return_type=param_type)

class _SlotCall(ActionCall):
    def __init__(self, slot_name, param_type):
        """
        Auxiliary action to connect to a named input slot of the workflow.
        :param slot_name: Slot name gives also name of appropriate Workflow's parameter.
        """
        super().__init__(_Slot(param_type), slot_name)
        self._arguments = []
        # self.rank = i_slot
        # """ Slot rank. """
        self.type = param_type
        """ Slot type. None - slot not used. """


    # def is_used(self):
    #     return bool(self.output_actions)

    def code_substitution_probability(self):
        return 1.0

    def code(self, representer):
        return None

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

        params = []
        params.append(ActionParameter(name="result", p_type=out_type, default=ActionParameter.no_default))
        # The return value, there should be always some return value, as we want to use "functional style".
        params.append(ActionParameter(name='args', p_type=Any, default=ActionParameter.no_default, kind=ActionParameter.VAR_POSITIONAL))
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




class _Variables:
    """
    Helper class to store local variables of the workflow and use
    their names as instance names for the assigned actions, i.e.

    self.x = action_y(...)
    other_action(self.x)

    Without `self` the variable name is not accessible at runtime.
    therefore

    x = action_y(...)
    other_action(x)

    works, but the name `x` is not preserved during code representation.
    """
    def __setattr__(self, key, value):
        value = into_action(value)
        value = value.set_name(key)
        self.__dict__[key] = Dummy(ActionFactory.instance(), value)

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

    @classmethod
    def from_source(cls, func):
        new_workflow = cls(func.__name__, func.__module__)
        new_workflow.initialize_from_function(func)
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
        # no initial parameters, nor slots
        none_value = ActionCall.create(Value(None))
        self._result_call = _ResultCall(none_value, None)
        # Result ActionCall, initaliy returning None
        self._is_valid = False
        # Result of last update()

        #######################
        # internal structures
        self._action_calls = set()
        # Dict:  unique action instance name -> action instance.
        self._sorted_calls = []
        # topologically sorted action instance names
        self.update()


    @property
    def result_call(self):
        return self._result_call

    @property
    def action_call_dict(self):
        return {ac.name : ac for ac in self._action_calls}

    @property
    def slots(self):
        return self._slots

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    def initialize_from_function(self, func):
        try:
            func_signature = _extract_signature(func, omit_self=True)
        except exceptions.ExcTypeBase as e:
            raise exceptions.ExcTypeBase(f"Wrong signature of workflow:  {func.__module__}.{func.__name__}") from e

        func_args = []
        _self = _Variables()
        if func_signature.had_self:
            func_args.append(_self)

        self._slots = []
        for p in func_signature:
            slot = _SlotCall(p.name, p.type)
            self._slots.append(slot)
        dummies = [Dummy(ActionFactory.instance(), slot) for slot in self._slots]
        func_args.extend(dummies)
        output_action = into_action(func(*func_args))
        self._result_call = _ResultCall(output_action, func_signature.return_type)
        self._parameters = func_signature
        self.update()


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
        self._is_valid = False
        actions = set()
        topology_sort = []
        instance_names = {}
        # clear output_actions
        for action in self._action_calls:
            action._output_actions = []

        def construct_postvisit(action_call):
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

            # handle slots
            #if isinstance(action, Slot):
            #    assert action is self._slots[action.rank]
            actions.add(action_call)
            topology_sort.append(action_call)

        # def edge_visit(previous, action, i_arg):
        #     return previous.output_actions.append((action, i_arg))

        is_dfs = dfs.DFS(neighbours=lambda action_call: (arg.value for arg in action_call.arguments),
                         postvisit=construct_postvisit).run([self._result_call])
        if not is_dfs:
            return False

        self._action_calls = actions
        self._sorted_calls = topology_sort
        # set backlinks
        for action in self._action_calls:
            for i_arg, arg in enumerate(action.arguments):
                if arg.value is not None:
                    arg.value._output_actions.append((action, i_arg))

        self._is_valid = True
        return True

    # def evaluate(self, input):
    #     pass



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
        indent = 4 * " "
        decorator = 'analysis' if self.is_analysis else 'workflow'
        params = [base._VAR_]
        for i, param in enumerate(self.parameters):
            assert(param.name == self._slots[i].name)
            if param.type_defined is None:
                type_hint = ""
            else:
                type_hint = ": {}".format(representer.type_code(param.type_defined))


            param_def = "{}{}".format(param.name, type_hint)
            params.append(param_def)
        result_hint = ""
        return_type = self.parameters.return_type_defined
        if return_type is not None:
            result_hint = " -> {}".format(representer.type_code(return_type))
        head = "def {}({}){}:".format(self.name, ", ".join(params), result_hint)
        body = ["@{base_module}.{decorator}".format(base_module='wf', decorator=decorator), head]

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
                                        for n in inst_repr.code.placeholders if inst_exprs[n].prob() > 0]
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


    def move_slot(self, from_pos, to_pos):
        """
        Move the slot at position 'from_pos' to the position 'to_pos'.
        Slots in between are shifted
        TODO: remove this function
        """
        assert 0 <= from_pos < len(self._slots)
        assert 0 <= to_pos < len(self._slots)
        from_slot = self._slots[from_pos]
        direction = 1 if to_pos > from_pos else -1
        for i in range(from_pos, to_pos, direction):
            self._slots[i] = self._slots[i + direction]
        self._slots[to_pos] = from_slot
        self._parameters = self.signature_from_dag()


    def insert_slot(self, i_slot:int, slot: _SlotCall) -> None:
        """
        Insert a new slot on i_th position shifting the slot on i-th position and remaining to the right.
        Change of the name
        """
        assert 0 <= i_slot < len(self._slots) + 1
        self._slots.insert(i_slot, slot)
        self._parameters = self.signature_from_dag()


    def remove_slot(self, i_slot:int) -> None:
        """
        Disconnect and remove the i-th slot.
        """
        for dep_action, i_arg in self._slots[i_slot]._output_actions:
            self.set_action_input(dep_action, i_arg, None)
        self._slots.pop(i_slot)
        self._parameters = self.signature_from_dag()

    # def bind_action_argument(self, action: ActionCall, param_name: str, input_action: ActionCall):
    #     try:
    #         orig_input = action.arguments[param_name].value
    #     except KeyError:
    #         return False
    #     action.bind_argument(param_name, input_action)
    #     is_correct = self.update()
    #     if not is_correct:
    #         action.bind_argumant(param_name, orig_input)
    #         return False
    #     return True

    def _set_ac(self, action_call):
        errors = action_call.set_inputs(action_call.args_in, action_call.kwargs_in)
        return self.update()

    def set_action_input(self, action_call: ActionCall, i_arg:int, input_action: ActionCall) -> bool:
        """
        Set argument 'i_arg' of the 'action' to the 'input_action'.

        E.g. wf.set_action_input(list_1, 0, slot_a)
        The result of the workflow is an action that takes arbitrary number of arguments but
        """
        if input_action is None and i_arg == len(action_call.args_in) - 1:
            orig_arg = action_call.args_in.pop()
            if not self._set_ac(action_call):
                action_call.args_in[i_arg] = orig_arg
                assert self._set_ac(action_call)
                return False
        try:
            orig_arg = action_call.args_in[i_arg]
            action_call.args_in[i_arg] = input_action
            if not self._set_ac(action_call):
                action_call.args_in[i_arg] = orig_arg
                assert self._set_ac(action_call)
                return False
        except IndexError:
            action_call.args_in.append(input_action)
            if not self._set_ac(action_call):
                action_call.args_in.pop()
                assert self._set_ac(action_call)
                return False
        return True


    def set_result_type(self, result_type):
        """
        TOOD: Test after introduction of typing.
        :param result_type:
        :return:
        """
        self.result_call.output_type = result_type



    def expand(self, task, task_creator):
        """
        Expansion of the composed task with given data inputs (possibly None if not evaluated yet).
        :param inputs: List[Task]
        :param task_creator: Dependency injection method for creating tasks from action instances:
            task_creator(action_call, input_tasks)
        :return:
            None if can not be expanded yet.
            List of created actions.

            In particular slots are named by corresponding parameter name and result task have name '__result__'
        """
        self.update()
        childs = {}
        assert len(self._slots) == len(task.inputs)
        for slot, input in zip(self._slots, task.inputs):
            # shortcut the slots
            #task = task_creator(slot.name, Pass(), [input])
            childs[slot.name] = input
        for action_call in self._sorted_calls:
            if isinstance(action_call, _SlotCall):
                continue
            # TODO: eliminate dict usage, assign a call rank to the action calls
            # TODO: use it to index tasks in the resulting task list 'childs'
            arg_tasks = [childs[arg.value.name] for arg in action_call.arguments]
            task_binding = TaskBinding(action_call.name, action_call.action, action_call._id_args_pair, arg_tasks)
            task = task_creator(task_binding)
            childs[action_call.name] = task
        return childs.values()















