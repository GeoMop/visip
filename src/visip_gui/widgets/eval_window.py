from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QDockWidget, QMessageBox

from visip_gui.config.config_data import ConfigData
from visip_gui.widgets.data_editor import DataEditor
from visip_gui.widgets.eval_tab_widget import EvalTabWidget
from visip_gui.widgets.evaluation_navigation import EvaluationNavigation
from visip_gui.widgets.inputs_editor import InputsEditor


class EvalWindow(QMainWindow):
    def __init__(self):
        super(EvalWindow, self).__init__()
        self.cfg = ConfigData()
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setTabShape(1)
        self.tab_widget.tabCloseRequested.connect(self.on_close_tab)
        self.setWindowTitle("Evaluation")

        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.setCentralWidget(self.tab_widget)

        self.data_editor_dock = QDockWidget("Data Inspection", self)
        self.data_editor_dock.setObjectName("data_editor_dock")
        self.data_editor_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.data_editor_dock)

        self.data_editor = DataEditor()
        self.data_editor_dock.setWidget(self.data_editor)

        self.navigation_dock = QDockWidget("Navigation Stack", self)
        self.navigation_dock.setObjectName("navigation_dock")
        self.navigation_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.navigation_dock)
        self.last_tab_widget = None
        if not self.cfg.contains("evalWindow/geometry"):
            self.resize(1000, 700)
        else:
            self.restoreGeometry(self.cfg.value("evalWindow/geometry", QByteArray()))
        self.restoreState(self.cfg.value("evalWindow/windowState", QByteArray()))

    def add_eval(self, gui_eval):
        self.show()
        self.activateWindow()

        self.tab_widget.setCurrentIndex(self.tab_widget.addTab(gui_eval, gui_eval.view.scene.workflow.name))

    def tab_changed(self, index):
        if index >= 0:
            curr_widget = self.tab_widget.currentWidget()
            curr_widget.view.scene.on_selection_changed()
            self.navigation_dock.setWidget(curr_widget.navigation)
            self.last_tab_widget = curr_widget

    def on_close_tab(self, index):
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.close()

    def closeEvent(self, *args, **kwargs):
        save_to_close = True
        for index in range(self.tab_widget.count()):
            if self.tab_widget.widget(index).running:
                save_to_close = False
                break

        if not save_to_close:
            msg = QMessageBox(self)
            msg.setText("There are unfinished evaluations")
            msg.setInformativeText("Do you want to terminate them?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg.setIcon(QMessageBox.Warning)
            if msg.exec() == QMessageBox.Yes:
                while self.tab_widget.currentIndex() != -1:
                    evaluation = self.tab_widget.currentWidget()
                    if evaluation.running:
                        evaluation.end_evaluation()

            self.tab_widget.clear()

        self.cfg.setValue("evalWindow/geometry", self.saveGeometry())
        self.cfg.setValue("evalWindow/windowState", self.saveState())

