from common import Value
from frontend.parameter_tree_custom.slot_param import SlotParam


class EvalParam(SlotParam):
    def __init__(self, arg_g_action, arg, **opts):
        super(EvalParam, self).__init__(arg, **opts)
        self.arg_g_action = arg_g_action
        if not arg_g_action is None:
            self.fill_data_info(arg_g_action.widget.data)

    def get_data(self):
        if self.arg is not None and self.arg.value is not None:
            if isinstance(self.arg.value.action, Value):
                typ = type(self.arg.value.action.value).__name__
                if typ in ['str', 'int', 'float', 'bool']:
                    return self.arg.value.action.value
                else:
                    return str(self.arg.value.action.value)
            else:
                return str(self.arg_g_action.widget.data)
        else:
            return "Not Connected"
