from visip import _Value
from visip_gui.parameter_tree_custom.slot_param import SlotParam


class EvalParam(SlotParam):
    def __init__(self, arg_g_action, arg, **opts):
        super(EvalParam, self).__init__(arg, **opts)
        opts['readonly'] = False
        opts['type'] = 'str'
        opts['name'] = self.get_label()
        self.setOpts(**opts)
        self.arg_g_action = arg_g_action
        if not arg_g_action is None:
            self.fill_data_info(arg_g_action.widget.data)

    def get_data(self):
        if self.arg is not None and self.arg.value is not None:
            if isinstance(self.arg.value.action, _Value):
                return self.arg.value.action.value.__repr__()
            else:
                return self.arg_g_action.widget.data.__repr__()
        else:
            return "Not Connected"
