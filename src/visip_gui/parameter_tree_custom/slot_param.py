
from PyQt5.QtCore import pyqtSignal
from pyqtgraph import parametertree
from visip.action.constructor import Value
from visip.dev import dtype
from visip_gui.parameter_tree_custom.group_param import GroupParam
from visip_gui.parameter_tree_custom.slot_param_item import SlotParamItem


class SlotParam(parametertree.parameterTypes.GroupParameter):
    default_val = {
        'str': '',
        'float': 0.0,
        'int': 0
    }
    itemClass = SlotParamItem
    sig_view_update_needed = pyqtSignal()
    sig_value_changed = pyqtSignal(object, object)
    sig_constant_changed = pyqtSignal(object, bool)

    def __init__(self, arg, **opts):
        self.orig_name = opts['name']
        self.arg = arg
        opts['type'] = 'str'
        if arg is not None and arg.value is not None:
            if not isinstance(arg.value.action, Value):
                opts['name'] = self.get_label()
                opts['readonly'] = True
            elif isinstance(self.arg.value.action.value, dtype._ActionBase):
                opts['name'] = self.get_label()
                opts['readonly'] = True
        else:
            opts['readonly'] = True
            opts['name'] = self.get_label()


        super(SlotParam, self).__init__(**opts)

        if arg is not None and arg.value is not None:
            if isinstance(arg.value.action, Value):
                self.fill_data_info(self.arg.value.action.value.__repr__)


    def get_label(self):
        name = self.orig_name
        if self.arg is None:
            return self.orig_name
        if hasattr(self.arg.parameter.type, '__name__'):
            return name + "={" + self.arg.parameter.type.__name__ + "}"
        else:
            return name + "={" + self.arg.parameter.type.__class__.__name__ + "}"

    def get_data(self):
        if self.arg is not None and self.arg.value is not None:
            if isinstance(self.arg.value.action, Value):
                if isinstance(self.arg.value.action.value, dtype._ActionBase):
                    return "Connected to: " + self.arg.value.name
                else:
                    return self.arg.value.action.value.__repr__()
            else:
                return "Connected to: " + self.arg.value.name
        else:
            return "Not Connected"

    def fill_item(self, item, data):
        if hasattr(data, "__dict__"):
            for key, value in data.__dict__.items():
                child = GroupParam(str(key) + " = {" + type(value).__name__ + '} ' + repr(value), value)
                item.addChild(child)
                #self.fill_item(child, value)
        elif isinstance(data, dict):
            for key, value in data.items():
                child = GroupParam(repr(key) + " = {" + type(value).__name__ + '} ' + repr(value), value)
                item.addChild(child)
                #self.fill_item(child, value)

        elif isinstance(data, (tuple, list)):
            i = 0
            for value in data:
                child = GroupParam(str(i) + " = {" + type(value).__name__ + '} ' + repr(value), value)
                i += 1
                item.addChild(child)
                #self.fill_item(child, value)

    def fill_data_info(self, data):

        self.setName(self.get_label())
        if isinstance(data, (tuple, list, dict)):
            self.fill_item(self, data)
        return

    def addNew(self, typ=None):
        val = self.default_val[typ]
        temp = parametertree.Parameter.create(name="param " + str(len(self.children())),
                                              type=typ,
                                              value=val)
        self.addChild(temp)
        temp.sigValueChanged.connect(self.on_value_changed)
        self.on_value_changed(temp, temp.value())

    def on_value_changed(self, param, val):
        self.sig_value_changed.emit(self, val)






