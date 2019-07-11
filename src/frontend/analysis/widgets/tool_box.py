from PyQt5.QtWidgets import QToolBox

from common.analysis import SlotInstance, Result
from frontend.analysis.data.tree_item import TreeItem
from frontend.analysis.graphical_items.g_action import GAction
from frontend.analysis.graphical_items.g_input_action import GInputAction
from frontend.analysis.graphical_items.g_output_action import GOutputAction
from frontend.analysis.widgets.action_category import ActionCategory

import common.analysis as analysis
import common.analysis.action_instance as instance

from frontend.analysis.widgets.toolbox_view import ToolboxView


class ToolBox(QToolBox):
    def __init__(self, main_widget, parent=None):
        super(ToolBox, self).__init__(parent)
        self.main_widget = main_widget

        self.system_actions_layout = ActionCategory()

        for action in analysis.base_system_actions:
            if isinstance(action, SlotInstance):
                ToolboxView(GInputAction(TreeItem(["Input", 0, 0, 50, 50]), action), self.system_actions_layout)
            elif isinstance(action, Result):
                ToolboxView(GOutputAction(TreeItem(["Output", 0, 0, 50, 50]), action), self.system_actions_layout)
            else:
                ToolboxView(GAction(TreeItem([action.name, 0, 0, 50, 50]),
                                    instance.ActionInstance.create(action)), self.system_actions_layout)

        # ToolboxView(GAction(TreeItem(["List", 0, 0, 50, 50]), instance.ActionInstance.create( base.List())), toolbox_layout2)
        self.setMinimumWidth(180)
        self.addItem(self.system_actions_layout, "System actions")
        # self.toolBox.addItem(toolbox_layout2, "Data manipulation")

        self.import_modules = {}

    def on_workspace_change(self, module, curr_workspace):
        last_index = self.currentIndex()
        if module.name in self.import_modules:
            category_index = self.indexOf(self.import_modules[module.name])
            self.removeItem(category_index)
        else:
            category_index = self.count()
        module_category = ActionCategory()
        for item in module.definitions:
            if not item.is_analysis and item.name != curr_workspace.scene.workflow.name:
                ToolboxView(GAction(TreeItem([item.name, 0, 0, 50, 50]),
                                    instance.ActionInstance.create(item)), module_category)

        self.import_modules[module.name] = module_category
        self.insertItem(category_index, module_category, module.name)
        self.setCurrentIndex(last_index)


    def on_module_change(self, module, curr_workspace):
        while self.count() > 1:
            self.removeItem(self.count()-1)
        #self.addItem(self.system_actions_layout, "System actions")
        if module is not None:
            self.on_workspace_change(module, curr_workspace)
