from visip_gui.parameter_tree_custom.eval_param import EvalParam
from visip_gui.parameter_tree_custom.root_param import RootParam
from visip_gui.widgets.property_editor import PropertyEditor


class DataEditor(PropertyEditor):
    def insert_item_with_data(self, arg_g_action, arg, name="", idx=None):
        temp = EvalParam(arg_g_action, arg, name=name, type='group', readonly=True)
        temp.sig_value_changed.connect(self.on_value_changed)
        temp.sig_constant_changed.connect(self.on_constant_changed)
        self.root_item.insertChild(len(self.root_item.children()), temp)

    def update_editor(self):
        i = 0
        self.root_item = RootParam(self.g_action, readonly=True)
        for arg in self.g_action.w_data_item.arguments:
            arg_g_action = self.g_action.get_arg_action(arg)
            self.insert_item_with_data(arg_g_action, arg, arg.parameter.name or self.g_action.in_ports[i].name)
            i += 1

        self.setParameters(self.root_item, showTop=True)

    def on_constant_changed(self, param, val: bool):
        pass

    def on_value_changed(self, param, val):
        pass

    def contextMenuEvent(self, ev):
        pass