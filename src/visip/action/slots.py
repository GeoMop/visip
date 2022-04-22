from ..dev import base
from ..dev.exceptions import ExcVariableOverwrite
from ..dev.parameters import Parameters
from ..code.dummy import Dummy
from ..dev.action_instance import ActionCall, ActionArgument, ActionInputStatus

class _Slot(base.ActionBase):
    def __init__(self, param_type=None):
        super().__init__("_Slot")
        self._parameters = Parameters([], return_type=param_type)



class _SlotCall(ActionCall):
    """
    Auxiliary action call representing an input parameter.
    Slots are created according to the extracted parameters in
    `actioncalls_from_function`

    """
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

    def set_name(self, instance_name: str):
        """
        Do not set _proper_instance_name, to omit "self." prefix for slots.
        """
        self.name = instance_name
        return self



def actioncalls_from_function(af: 'ActionFactory', func, parameters) -> ActionCall:
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
            if key in self.__dict__:
                raise ExcVariableOverwrite("Overwriting variable or parameter: ", key)
            value = ActionCall.into_action(value)
            value = value.set_name(key)
            self.__dict__[key] = Dummy(af, value)

    func_args = []
    _self = _Variables()
    if parameters.had_self:
        func_args.append(_self)

    slots = []
    for p in parameters:
        slot = _SlotCall(p.name, p.type)
        slots.append(slot)
        _self.__setattr__(p.name, slot)
    dummies = [Dummy(af, slot) for slot in slots]
    func_args.extend(dummies)
    output_action = ActionCall.into_action(func(*func_args))
    return output_action, slots
