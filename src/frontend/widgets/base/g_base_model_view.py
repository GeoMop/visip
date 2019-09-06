"""
Base class for view of graphics scene containing DAG.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView


class GBaseModelView(QGraphicsView):
    def __init__(self, parent=None):
        super(GBaseModelView, self).__init__(parent)

        self.setRenderHint(QtGui.QPainter.Antialiasing, True)

        self.setDragMode(self.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.verticalScrollBar().blockSignals(True)
        self.setViewportUpdateMode(self.FullViewportUpdate)

        # settings for zooming the workspace
        self.zoom = 1.0
        self.zoom_factor = 1.1
        self.max_zoom = pow(self.zoom_factor, 10)
        self.min_zoom = pow(1 / self.zoom_factor, 20)


    def wheelEvent(self, event):
        """Handle zoom on wheel rotation."""
        super(GBaseModelView, self).wheelEvent(event)
        if event.modifiers() & Qt.ControlModifier:
            degrees = event.angleDelta() / 8
            steps = degrees.y() / 15
            self.setTransformationAnchor(self.AnchorUnderMouse)
            if steps > 0:
                if self.zoom < self.max_zoom:
                    self.scale(self.zoom_factor, self.zoom_factor)
                    self.zoom = self.zoom * self.zoom_factor
            else:
                if self.zoom > self.min_zoom:
                    self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
                    self.zoom = self.zoom / self.zoom_factor


