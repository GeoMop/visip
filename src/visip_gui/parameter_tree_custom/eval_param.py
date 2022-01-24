from PyQt5.QtWidgets import QTreeWidgetItem
from pyqtgraph import parametertree

from visip import _Value
from visip_gui.parameter_tree_custom.eval_param_item import EvalParamItem
from visip_gui.parameter_tree_custom.slot_param import SlotParam


class EvalParam(parametertree.Parameter):
    itemClass = EvalParamItem
    def __init__(self, data, **opts):
        super(EvalParam, self).__init__(**opts)
        opts['readonly'] = True
        opts['type'] = 'str'
        opts["expanded"] = False
        self.setOpts(**opts)
        self.data = data
        self.populated = False
        self.expandable = False

    def makeTreeItem(self, depth):
        self.opts["expanded"] = self.populated
        self.tree_item = self.itemClass(self, depth, self.on_expand)
        if self.expandable:
            self.tree_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        return self.tree_item

    def on_expand(self, fnc_add_param):
        if not self.populated:
            self.fill_item(self, self.data, fnc_add_param)
            self.populated = True
            return True
        else:
            return False


    def get_data(self):
        if self.arg is not None and self.arg.value is not None:
            if isinstance(self.arg.value.action, _Value):
                return self.arg.value.action.value.__repr__()
            else:
                return self.data.__repr__()
        else:
            return "Not Connected"

    @staticmethod
    def fill_item(item, data, fnc_add_param=None, first=False):
        if hasattr(data, "__dict__"):
            for key, value in data.__dict__.items():
                child = EvalParam(value, name=str(key) + " = {" + type(value).__name__ + '} ', value=repr(value))
                EvalParam.insert_item_and_make_expandable(item, child, value, fnc_add_param)

        elif isinstance(data, dict):
            for key, value in data.items():
                if first:
                    child = EvalParam(value, name=str(key) + " = {" + type(value).__name__ + '} ', value=repr(value))
                else:
                    child = EvalParam(value, name=repr(key) + " = {" + type(value).__name__ + '} ', value=repr(value))
                EvalParam.insert_item_and_make_expandable(item, child, value, fnc_add_param)

        elif isinstance(data, (tuple, list)):
            i = 0
            for value in data:
                child = EvalParam(value, name=str(i) + " = {" + type(value).__name__ + '} ', value=repr(value))
                i += 1
                EvalParam.insert_item_and_make_expandable(item, child, value, fnc_add_param)


    @staticmethod
    def insert_item_and_make_expandable(root, child, value, fnc_add_param):
        if isinstance(value, (dict, tuple, list)) or hasattr(value, "__dict__"):
            child.expandable = True

        if fnc_add_param is None:
            root.addChild(child)
        else:
            #fnc_add_param(child, root)
            root.addChild(child)
            item = child.makeTreeItem(root.tree_item.depth + 1)
            item.treeWidgetChanged()