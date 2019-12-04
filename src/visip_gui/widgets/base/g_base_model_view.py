"""
Base class for view of graphics scene containing DAG.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QGraphicsView, QApplication


class GBaseModelView(QGraphicsView):
    def __init__(self, parent=None):
        super(GBaseModelView, self).__init__(parent)

        self.setRenderHint(QtGui.QPainter.Antialiasing, True)

        self.setDragMode(self.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(self.FullViewportUpdate)

        # settings for zooming the workspace
        self.zoom = 1.0
        self.zoom_factor = 1.1
        self.max_zoom = pow(self.zoom_factor, 10)
        self.min_zoom = pow(1 / self.zoom_factor, 20)

        self.shift_pressed = False


    def wheelEvent(self, event):
        """Handle zoom on wheel rotation."""
        if event.modifiers() & Qt.ControlModifier:
            degrees = event.angleDelta() / 8
            steps = degrees.y() / 15
            self.setTransformationAnchor(self.AnchorUnderMouse)
            if steps > 0:
                if self.zoom < self.max_zoom:
                    self.scale(self.zoom_factor, self.zoom_factor)
                    self.zoom = self.zoom * self.zoom_factor
            elif steps < 0:
                if self.zoom > self.min_zoom:
                    self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
                    self.zoom = self.zoom / self.zoom_factor

            event.setAccepted(True)
            
        if event.modifiers() & Qt.ShiftModifier:
            angle_delta = QPoint(event.angleDelta().y(), event.angleDelta().x())
            pixel_delta = QPoint(event.pixelDelta().y(), event.pixelDelta().x())
            modifiers = event.modifiers() & ~Qt.ShiftModifier
            new_event = QWheelEvent(event.posF(), event.globalPosF(), pixel_delta, angle_delta, event.buttons(),
                                    modifiers, event.phase(), event.inverted(), event.source())
            event = new_event

        super(GBaseModelView, self).wheelEvent(event)

    def keyPressEvent(self, key_event):
        super(GBaseModelView, self).keyPressEvent(key_event)
        if key_event.key() == QtCore.Qt.Key_Control:
            self.setDragMode(self.RubberBandDrag)
        if key_event.key() == QtCore.Qt.Key_Shift:
            self.shift_pressed = True

    def keyReleaseEvent(self, key_event):
        super(GBaseModelView, self).keyReleaseEvent(key_event)
        if key_event.key() == QtCore.Qt.Key_Control:
            self.setDragMode(self.ScrollHandDrag)
        if key_event.key() == QtCore.Qt.Key_Shift:
            self.shift_pressed = False

    def focusInEvent(self, focus_event):
        super(GBaseModelView, self).focusInEvent(focus_event)
        if QApplication.queryKeyboardModifiers() & QtCore.Qt.ControlModifier:
            self.setDragMode(self.RubberBandDrag)
        else:
            self.setDragMode(self.ScrollHandDrag)

        if QApplication.queryKeyboardModifiers() & QtCore.Qt.ShiftModifier:
            self.shift_pressed = True
        else:
            self.shift_pressed = False



