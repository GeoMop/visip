import sys
import dagviz
import networkx as nx

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtSvg import QSvgWidget


class DAGViewWidget(QWidget):
    def __init__(self, svg):
        super().__init__()

        self.setGeometry(100, 100, 1100, 1100)
        self.widgetSvg = QSvgWidget(parent=self)
        self.widgetSvg.setGeometry(10, 10, 1080, 1080)
        self.widgetSvg.load(svg)



class DisplaySVG(QWidget):
    qt_app = None
    display = None
    @staticmethod
    def qt_display(svg):
        if DisplaySVG.qt_app is None:
            DisplaySVG.qt_app = QApplication(sys.argv)

        #DisplaySVG.disp = DisplaySVG(DisplaySVG.qt_app)
        DisplaySVG.disp = DisplaySVG()
        DisplaySVG.disp.update(svg)
        DisplaySVG.disp.show()
        DisplaySVG.qt_app.exec_()

    "A simple SVG display."
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(800,1024)
        self.setWindowTitle("Display SVG")
        self.widgetSvg = QSvgWidget(parent=self)
        self.widgetSvg.setGeometry(10, 5, 780, 1000)
        self.widgetSvg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
        #parent.addWidget(self.widgetSvg)

    def update(self, svg):
        svg_byte_array = QByteArray(bytearray(svg.encode()))
        self.widgetSvg.load(svg_byte_array)
        self.widgetSvg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        # act = QAction("Close", self)
        # act.setShortcuts([QtGui.QKeySequence(QtCore.Qt.Key_Escape)])
        # act.triggered.connect(self.close)
        # self.addAction(act)


class DAGView:
    """
    Simple interface to Task DAG visualizer.
    Ultimate solution:
    Interactive Scheduler graph viewer:
    - interactive expansion
    - topological sort (horizontal)
    - nonlinear horizontal axis (given by time)
    - assignement to resources
    """

    def __init__(self, name):
        self.G = nx.DiGraph()
        self.name = name

    def add_task_node(self, id, action_name, status_color, kind_style):
        self.G.add_node(id, label=action_name, color=status_color,  style=kind_style)

    def add_edge(self, from_id, to_id):
        self.G.add_edge(from_id, to_id)

    def make_svg(self):
        r = dagviz.render_svg(self.G)
        # https://stackoverflow.com/questions/61439815/how-to-display-an-svg-image-in-python
        return r

    def show_qt(self):
        DisplaySVG.qt_display(self.make_svg())
