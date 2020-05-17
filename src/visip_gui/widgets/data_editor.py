from visip_gui.parameter_tree_custom.root_param_item import RootParamItem

from visip_gui.parameter_tree_custom.eval_param import EvalParam
from visip_gui.parameter_tree_custom.root_param import RootParam
from visip_gui.widgets.inputs_editor import InputsEditor


class DataEditor(InputsEditor):
    def __init__(self, g_action=None, parent=None):
        super(DataEditor, self).__init__(g_action, parent)
        self.itemExpanded.connect(self.expand_item)
    def insert_item_with_data(self, arg_g_action, arg, name="", idx=None):
        data = None
        if arg_g_action is not None:
            data = arg_g_action.widget.data
        EvalParam.fill_item(self.root_item, data)
        #temp = EvalParam(data, name=name, type='group', readonly=True)
        #temp.sig_value_changed.connect(self.on_value_changed)
        #temp.sig_constant_changed.connect(self.on_constant_changed)
        #self.root_item.insertChild(len(self.root_item.children()), temp)

    def update_editor(self):
        i = 0
        data = {}
        self.root_item = RootParam(self.g_action, readonly=True)
        for arg in self.g_action.w_data_item.arguments:
            arg_g_action = self.g_action.get_arg_action(arg)
            name = arg.parameter.name or self.g_action.in_ports[i].name
            if arg_g_action is None:
                data[name] = arg.value.action.value.__repr__()
            else:
                data[name] = arg_g_action.widget.data
            #self.insert_item_with_data(arg_g_action, arg, arg.parameter.name or self.g_action.in_ports[i].name)
            i += 1

        EvalParam.fill_item(self.root_item, data, first=True)
        self.setParameters(self.root_item, showTop=True)

    def expand_item(self, item):
        if "on_expand" in dir(item):
            item.param.on_expand(self.addParameters)

    def on_constant_changed(self, param, val: bool):
        pass

    def on_value_changed(self, param, val):
        pass

    def contextMenuEvent(self, ev):
        pass