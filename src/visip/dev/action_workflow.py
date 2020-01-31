import attr
from typing import Any

from . import base
from . import dfs
from .action_instance import ActionCall
from ..action.constructor import _ListBase
from . parameters import Parameters, ActionParameter


"""
Implementation of the Workflow composed action.
- creating the 
"""


class _Slot(base._ActionBase):
    def __init__(self):
        super().__init__("_Slot")
        self._parameters = Parameters()
        self._output_type = Any

class _SlotCall(ActionCall):
    def __init__(self, slot_name):
        """
        Auxiliary action to connect to a named input slot of the workflow.
        :param slot_name: Slot name gives also name of appropriate Workflow's parameter.
        """
        super().__init__(_Slot(), slot_name)
        self.arguments = []
        # self.rank = i_slot
        # """ Slot rank. """
        self.type = None
        """ Slot type. None - slot not used. """


    # def is_used(self):
    #     return bool(self.output_actions)

    def substitution_probability(self):
        return 1.0

    def code(self, representer, module_dict):
        return None

class _Result(_ListBase):
    """
     Auxiliary result action.
     Takes arbitrary number of inputs, at least one input must be provided.
     Returns the first input, other inputs are used just for their side effects (using the Save action).

     TODO: Decide if we really want side effect values.
     Workflow decorator automatically connects all Save actions to the ignored result inputs.

    """
    def __init__(self):
        super().__init__(action_name='result')
        self._parameters = Parameters()
        self._parameters.append(ActionParameter(name="result", type=Any, default=ActionParameter.no_default))
        # The return value, there should be always some return value, as we want to use "functional style".
        self._parameters.append(ActionParameter(name=None, type=Any, default=ActionParameter.no_default))
        # The "side effects" of the workflow.


    def evaluate(self, inputs):
        return inputs[0]

    def format(self, representer, action_name, arg_names, arg_values):
        return representer.format("return", representer.token(arg_names[0]))

class _ResultCall(ActionCall):
    """ Auxiliary result action instance, used to treat the result connecting in the consistnet way."""
    def __init__(self):
        super().__init__(_Result(), "__result__")





class _Workflow(base._ActionBase):
    """
    Represents a composed action.
    - Allows composition of the actions into a DAG
    - Is a child of _ActionBase, encapsulates its internal structure.
    - All actions are kept in the self._action_calls set.
    - action cals connected to the result are are topologicaly sorted in the 'update' method
      and stored in correct order in self._sorted_calls.
    - action_calls can be freely renamed as workflow makes name -> action_call dict only temporally
      (the. name_to_action_call property)
    """

    def __init__(self, name):
        """

        :param name:
        :param slots:
        :param result:
        :param params:
        :param output_type:
        """
        super().__init__(name)
        self._module = None
        # Name of the module were the workflow is defined.
        self.task_type = base.TaskType.Composed
        # Task type determines how the actions are converted to the tasks.
        # Composed tasks are expanded.
        self._result_call = _ResultCall()
        # Result action instance.
        self._slots = []
        # Definition of the workspace parameters ?
        self._action_calls = set()
        # Dict:  unique action instance name -> action instance.
        self._sorted_calls = []
        # topologically sorted action instance names

        self.update_parameters()

    @property
    def result(self):
        return self._result_call

    @property
    def action_call_dict(self):
        return {ac.name : ac for ac in self._action_calls}

    @property
    def slots(self):
        return self._slots

    def set_from_source(self, slots, output_type, output_action):
        """
        Used by the workflow decorator to setup the instance.
        """
        self._slots = slots
        self._result_call.set_single_input(0, output_action)
        self._result_call.action._output_type = output_type

        is_dfs = self.update(self._result_call)
        assert is_dfs
        self.update_parameters()


    def update(self, result_instance):
        """
        DFS through the workflow DAG given be the result action:
        - set unique action call names
        - set back references to action calls connected to outputs: action.output_actions
        - make topology sort of action calls
        - update list of action calls
        :param result_instance: the result action
        :return: True in the case of sucessfull update, False - detected cycle
        """
        actions = set()
        topology_sort = []
        instance_names = {}
        # clear output_actions
        for action in self._action_calls:
            action.output_actions = []

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
            topology_sort.append(action_call.name)

        # def edge_visit(previous, action, i_arg):
        #     return previous.output_actions.append((action, i_arg))

        is_dfs = dfs.DFS(neighbours=lambda action_call: (arg.value for arg in action_call.arguments),
                         postvisit=construct_postvisit).run([result_instance])
        if not is_dfs:
            return False

        self._action_calls = actions
        self._sorted_calls = topology_sort
        # set backlinks
        for action in self._action_calls:
            for i_arg, arg in enumerate(action.arguments):
                if arg.value is not None:
                    arg.value.output_actions.append((action, i_arg))
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
    
    def code_of_definition(self, representer, make_rel_name):
        """
        Represent workflow by its source.
        :return: list of lines containing representation of the workflow as a decorated function.
        Code sugar:
        1. substitute all results used just once in single parameter actions
        2. try to substitute to multiparameter actions, check line length.
        """
        indent = 4 * " "
        decorator = 'analysis' if self.is_analysis else 'workflow'
        params = [base._VAR_]
        params.extend([self._slots[islot].name for islot in range(len(self._slots))])
        head = "def {}({}):".format(self.name, ", ".join(params))
        body = ["@{base_module}.{decorator}".format(base_module='wf', decorator=decorator), head]

        # Make dict: full_instance_name -> (format, [arg full names])
        inst_order = []
        inst_exprs = {}
        name_to_action = self.action_call_dict
        for iname in self._sorted_calls:
            action_call = name_to_action[iname]
            full_name = action_call.get_code_instance_name()
            subst_prob = action_call.substitution_probability()
            code = action_call.code(representer, make_rel_name)
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


        result_action = self._result_call.arguments[0].value
        body.append("    return {}".format(result_action.name))
        return "\n".join(body)


    def move_slot(self, from_pos, to_pos):
        """
        Move the slot at position 'from_pos' to the position 'to_pos'.
        Slots in between are shifted
        """
        assert 0 <= from_pos < len(self._slots)
        assert 0 <= to_pos < len(self._slots)
        from_slot = self._slots[from_pos]
        direction = 1 if to_pos > from_pos else -1
        for i in range(from_pos, to_pos, direction):
            self._slots[i] = self._slots[i + direction]
        self._slots[to_pos] = from_slot
        self.update_parameters()


    def insert_slot(self, i_slot:int, slot: _SlotCall) -> None:
        """
        Insert a new slot on i_th position shifting the slot on i-th position and remaining to the right.
        Change of the name
        """
        assert 0 <= i_slot < len(self._slots) + 1
        self._slots.insert(i_slot, slot)
        self.update_parameters()


    def remove_slot(self, i_slot:int) -> None:
        """
        Disconnect and remove the i-th slot.
        """
        for dep_action, i_arg in self._slots[i_slot].output_actions:
            self.set_action_input(dep_action, i_arg, None)
        self._slots.pop(i_slot)
        self.update_parameters()


    def set_action_input(self, action: ActionCall, i_arg:int, input_action: ActionCall) -> bool:
        """
        Set argument 'i_arg' of the 'action' to the 'input_action'.

        E.g. wf.set_action_input(list_1, 0, slot_a)
        The result of the workflow is an action that takes arbitrary number of arguments but




        """
        if i_arg < len(action.arguments):
            orig_input = action.arguments[i_arg]
        else:
            orig_input = None
        action.set_single_input(i_arg, input_action)
        is_dfs = self.update(self._result_call)
        if not is_dfs:
            action.set_single_input(i_arg, orig_input)
            return False
        return True

        # # update back references: output_actions
        # action_arg = (action, i_arg)
        # if input_action is not None:
        #     input_action.output_actions.append(action_arg)
        # if orig_input is not None:
        #     orig_input.output_actions = [aa  for aa in orig_input.output_actions if aa != action_arg]


    def set_result_type(self, result_type):
        """
        TOOD: Test after introduction of typing.
        :param result_type:
        :return:
        """
        self.result.output_type = result_type


    def update_parameters(self):
        """
        Update outer interface: parameters and result_type according to slots and result actions.
        TODO: Check and set types.
        """
        self._parameters = Parameters()
        for i_param, slot in enumerate(self._slots):
            slot_expected_types = [a.arguments[i_arg].parameter.type  for a, i_arg in slot.output_actions]
            common_type = None #types.closest_common_ancestor(slot_expected_types)
            p = ActionParameter(slot.name, common_type)
            self._parameters.append(p)


    def expand(self, inputs, task_creator):
        """
        Expansion of the composed task with given data inputs (possibly None if not evaluated yet).
        :param inputs: List[Task]
        :param task_creator: Dependency injection method for creating tasks from action instances:
            task_creator(instance_name, action, input_tasks)
        :return:
            None if can not be expanded yet.
            Dict action_instance_name -> (TaskType, task_spec)
                task_spec:
                    - existing task from 'inputs', in the case of task type 'Slot'
                    - (action, arguments) where arguments are the action_instance_names

            In particular slots are named by corresponding parameter name and result task have name '__result__'
        """
        childs = {}
        assert len(self._slots) == len(inputs)
        # TODO: fix connection of slots to inputs
        for slot, input in zip(self._slots, inputs):
            childs[slot.name] = input
        name_to_action = self.action_call_dict
        for action_instance_name in self._sorted_calls:
            if action_instance_name not in childs:
                action_instance = name_to_action[action_instance_name]
                arg_tasks = [childs[arg.value.name] for arg in action_instance.arguments]
                childs[action_instance.name] = task_creator(action_instance.name, action_instance.action, arg_tasks)
        return childs















