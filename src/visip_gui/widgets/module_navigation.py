from PyQt5.QtCore import QMargins
from PyQt5.QtWidgets import QTabWidget, QWidget, QFrame, QVBoxLayout

from visip.dev.action_workflow import _Workflow
from visip_gui.dialogs.get_text import GetText
from visip_gui.menu.module_navigation_menu import ModuleNavigationMenu
from visip_gui.widgets.workspace import Workspace


class ModuleNavigation(QTabWidget):
    def __init__(self, module, tab_widget,  parent=None):
        super(ModuleNavigation, self).__init__(parent)
        self.setLayout(QVBoxLayout(self))
        self._module = module
        self._tab_widget = tab_widget
        #self.setTabShape(1)
        self.menu = ModuleNavigationMenu()
        self.menu.new_workflow.triggered.connect(self.add_workflow)

        for wf in self._module.definitions:
            if issubclass(type(wf), _Workflow):
                self.addTab(Workspace(wf, self._tab_widget.main_widget,
                                      self._tab_widget.main_widget.toolbox.action_database), wf.name)

    def contextMenuEvent(self, event):
        self.menu.exec_(event.globalPos())

    def add_workflow(self):
        dialog = GetText(self, "New Workflow Name")
        dialog.setWindowTitle("New Workflow")
        if dialog.exec_():
            wf_name = dialog.text





