import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction, QStyle

from common.analysis.action_workflow import _Workflow
from frontend.analysis.menu.module_view_menu import ModuleViewMenu
from .workspace import Workspace


class ModuleView(QTreeWidget):
    workspace_changed = pyqtSignal(int)
    def __init__(self, tab_widget, module, edit_menu, parent=None):
        super(ModuleView, self).__init__(parent)
        self.edit_menu = edit_menu
        self.tab_widget = tab_widget
        self.menu = ModuleViewMenu()

        self.menu.show_wf.triggered.connect(self._change_workflow)
        self.menu.new_workflow.triggered.connect(self.create_new_workflow)
        self.menu.remove_workflow.triggered.connect(self.remove_workflow)

        self._module = module
        self._current_workspace = None
        self.setHeaderHidden(True)
        self.doubleClicked.connect(self._double_clicked)

        self.workspaces = {}

        for wf in module.definitions:
            if issubclass(type(wf), _Workflow):
                self.workspaces[wf.name] = (Workspace(wf, edit_menu, self.tab_widget.main_widget.toolbox.action_database))
                item = QTreeWidgetItem(self, [wf.name])
                item.setExpanded(True)
                self.addTopLevelItem(item)
                self.curr_wf_item = item

                if wf.slots:
                    for slot in wf.slots:
                        input_item = QTreeWidgetItem(item, [slot.name])
                        input_item.setIcon(0, QIcon(os.path.join(os.getcwd(), "analysis\\icons\\arrow_right.png")))

                if wf._result:
                    output_item = QTreeWidgetItem(item, [wf.result.name])
                    output_item.setIcon(0, QIcon(os.path.join(os.getcwd(), "analysis\\icons\\arrow_left.png")))

        if self.topLevelItemCount() > 0:
            self.mark_active_wf_item(self.topLevelItem(0))
            self._current_workspace = self.workspaces[self.topLevelItem(0).data(0, 0)]

    def remove_workflow(self):
        curr_item = self.currentItem()
        while curr_item.parent() != self:
            curr_item = curr_item.parent()
        wf_name = curr_item.data(0, 0)
        if len(self.workspaces) > 1:
            if self.current_workspace is self.workspaces[wf_name]:
                index = self.indexOfTopLevelItem(curr_item)
                if self.topLevelItem(index + 1) is None:
                    item = self.topLevelItem(index - 1)
                else:
                    item = self.topLevelItem(index + 1)

                self.mark_active_wf_item(item)
                self.set_current_workspace(item.data(0, 0))

        self.tab_widget.currentWidget().removeWidget(self.workspaces[wf_name])

        self.workspaces.pop(wf_name)

        for definiton in self.module.definitions:
            if definiton.name == wf_name:
                del definiton
                break

        self.takeTopLevelItem(self.indexOfTopLevelItem(curr_item))

    def create_new_workflow(self):
        wf_name = "new_workflow"
        index = 0
        while wf_name in self.workspaces.keys():
            index += 1
            wf_name = "new_workflow" + str(index)

        item = QTreeWidgetItem(self, [wf_name])
        item.setExpanded(True)
        self.addTopLevelItem(item)
        self.curr_wf_item = item

        wf = _Workflow(wf_name)
        self.module.definitions.append(wf)

        self.workspaces[wf_name] = (Workspace(wf, self.edit_menu, self.tab_widget.main_widget.toolbox.action_database))
        self.tab_widget.currentWidget().addWidget(self.workspaces[wf_name])

        self.mark_active_wf_item(item)
        self.set_current_workspace(wf_name)


    def _change_workflow(self):
        curr_item = self.currentItem()
        while curr_item.parent() is not None:
            curr_item = curr_item.parent()

        self.mark_active_wf_item(curr_item)
        self.set_current_workspace(curr_item.data(0, 0))


    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, module):
        self._module = module

    @property
    def current_workspace(self):
        return self._current_workspace

    def set_current_workspace(self, name):
        self._current_workspace = self.workspaces[name]
        self.tab_widget.change_workspace(self._current_workspace)
        self.tab_widget.main_widget.toolbox.on_workspace_change(self.module, self._current_workspace)

    def _double_clicked(self, model_index):
        if model_index.parent().data() == "Inputs":
            temp = model_index.data()
            action = self._current_workspace.scene.get_action(model_index.data())
            self._current_workspace.centerOn(action)

    def mark_active_wf_item(self, item):
        font = QFont()
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i).setFont(0, font)
        font.setBold(True)
        item.setFont(0, font)
        self.curr_wf_item = item

    def contextMenuEvent(self, event):
        """Open context menu on right mouse button click if no dragging occurred."""
        super(ModuleView, self).contextMenuEvent(event)
        clicked_item = self.itemAt(event.pos())
        self.setCurrentItem(clicked_item)
        if clicked_item == None:
            self.menu.show_wf.setEnabled(False)
            self.menu.remove_workflow.setEnabled(False)
        else:
            self.menu.show_wf.setEnabled(True)
            self.menu.remove_workflow.setEnabled(True)

        self.menu.exec_(event.globalPos())

