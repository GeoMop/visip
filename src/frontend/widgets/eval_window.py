from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QDockWidget

from frontend.widgets.data_editor import DataEditor
from frontend.widgets.eval_tab_widget import EvalTabWidget
from frontend.widgets.evaluation_navigation import EvaluationNavigation
from frontend.widgets.property_editor import PropertyEditor


class EvalWindow(QMainWindow):
    def __init__(self):
        super(EvalWindow, self).__init__()
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.setCentralWidget(self.tab_widget)

        self.data_editor_dock = QDockWidget("Data Inspection", self)
        self.data_editor_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.data_editor_dock)

        self.data_editor = DataEditor()
        self.data_editor_dock.setWidget(self.data_editor)

        self.navigation_dock = QDockWidget("Navigation Stack", self)
        self.navigation_dock.setMinimumWidth(150)



        self.navigation_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.navigation_dock)
        self.last_tab_widget = None

        self.resize(1000, 700)
        self.navigation_dock.show()
        self.show()
        self.navigation_dock.hide()
        self.hide()

    def add_eval(self, gui_eval):
        self.show()
        self.activateWindow()

        self.tab_widget.addTab(gui_eval, gui_eval.view.scene.workflow.name)

    def tab_changed(self, index):
        curr_widget = self.tab_widget.currentWidget()
        curr_widget.view.scene.on_selection_changed()
        self.navigation_dock.setWidget(curr_widget.navigation)
        self.last_tab_widget = curr_widget


