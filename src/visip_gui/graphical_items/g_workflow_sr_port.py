from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QLinearGradient

from .g_port import GPort


class GWorkflowSRPort(GPort):

    def __init__(self, is_slot_port=True, index=0, pos=QPoint(0,0), name="", parent=None):
        self.is_slot_port = is_slot_port
        super(GWorkflowSRPort, self).__init__(index, None, pos, name, parent)
        if is_slot_port:
            gradient = QLinearGradient(QPoint(GPort.RADIUS, -6 * GPort.RADIUS), QPoint(GPort.RADIUS, GPort.RADIUS))
        else:
            gradient = QLinearGradient(QPoint(GPort.RADIUS, 6 * GPort.RADIUS), QPoint(GPort.RADIUS, GPort.RADIUS))
        gradient.setColorAt(1.0, QtCore.Qt.black)
        gradient.setColorAt(0.0, QtCore.Qt.transparent)
        self.setPen(QtGui.QPen(gradient, 1.2, QtCore.Qt.DashLine))
        self.setBrush(Qt.gray)
        self.setEnabled(False)
        self.setPath(self.draw_port_path())

    def setEnabled(self, bool):
        super(GWorkflowSRPort, self).setEnabled(False)

    def draw_port_path(self):
        self.prepareGeometryChange()
        p = QtGui.QPainterPath()
        p.addEllipse(QtCore.QRectF(0, 0, self.RADIUS * 2, self.RADIUS * 2))

        if self.is_slot_port:
            p.moveTo(QPoint(GPort.RADIUS, -6 * GPort.RADIUS))
            p.lineTo(QPoint(GPort.RADIUS, GPort.RADIUS))
        else:
            p.moveTo(QPoint(GPort.RADIUS, GPort.RADIUS))
            p.lineTo(QPoint(GPort.RADIUS, 6 * GPort.RADIUS))

        return p


