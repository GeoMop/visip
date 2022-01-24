"""
Representation of ports to which a connection can be attached.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QApplication

#from visip.dev.action_instance import ActionArgument
from visip_gui.graphical_items.g_tooltip_item import GTooltipItem
#from visip_gui.graphical_items.g_tooltip_base import GTooltipBase


class GPort(QtWidgets.QGraphicsPathItem):
    """Base class for ports."""
    RADIUS = 6
    BORDER = 2
    SIZE = RADIUS * 2 + BORDER * 2

    def __init__(self, index, argument, pos=QPoint(0,0), name="", parent=None):
        """Initializes class.
        :param pos: Position of this action inside parent action.
        :param parent: This port will be part of parent action.
        """
        super(GPort, self).__init__(parent)
        self.argument = argument
        self.name = name
        self.constant = False
        if pos is not None:
            self.setPos(pos)
        self.connections = []
        self.default = False

        self._appending_port = False
        self.setPath(self.draw_port_path())
        self.setPen(QtCore.Qt.black)
        self.setBrush(QtCore.Qt.white)
        self.connections = []
        self.setAcceptHoverEvents(True)
        self.setZValue(1.0)
        self.setFlag(self.ItemSendsGeometryChanges)

        self.tool_tip = GTooltipItem(self)

        self.index = index
        self.setCursor(QtCore.Qt.ArrowCursor)



    @property
    def appending_port(self):
        return self._appending_port

    @appending_port.setter
    def appending_port(self, value):
        if value != self._appending_port:
            self._appending_port = value
            self.setPath(self.draw_port_path())

    def set_default(self, b):
        self.default = b
        self.setPath(self.draw_port_path())

    def set_constant(self, b):
        self.constant = b

    def draw_port_path(self):
        p = QtGui.QPainterPath()
        if self.appending_port:
            p.addEllipse(QtCore.QRectF(0, 0, self.RADIUS * 2, self.RADIUS * 2))
            p.moveTo(self.RADIUS - 3, self.RADIUS)
            p.lineTo(self.RADIUS + 3, self.RADIUS)
            p.moveTo(self.RADIUS, self.RADIUS - 3)
            p.lineTo(self.RADIUS, self.RADIUS + 3)
        else:
            p.addEllipse(QtCore.QRectF(0, 0, self.RADIUS * 2, self.RADIUS * 2))
        return p

    def __repr__(self):
        return "Action: '" + self.parentItem().name + "' Port: '" + self.name + "'"

    def itemChange(self, change_type, value):
        if change_type == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            for conn in self.connections:
                conn.update_gfx()
        return super(GPort, self).itemChange(change_type, value)

    def setEnabled(self, bool):
        super(GPort, self).setEnabled(bool)
        self.setBrush(QtCore.Qt.white if bool else QtCore.Qt.gray)

    def mousePressEvent(self, event):
        """If the port is pressed create a connection."""
        if event.button() == QtCore.Qt.LeftButton:
            if self.constant:
                self.tool_tip.set_text("Cannot connect to constant parameter!")
                self.tool_tip.tooltip_request(self.boundingRect().center(), Qt.red, 0)
                #self.tool_tip.show_tooltip(Qt.red)

            else:
                self.scene().add_connection(self)

    def hoverLeaveEvent(self, event):
        super(GPort, self).hoverLeaveEvent(event)

    def get_connection_point(self):
        """Return scene coordinates to draw connection."""
        return self.mapToScene(QtCore.QPoint(self.RADIUS, self.RADIUS))

    def paint(self, painter, style, widget=None):
        super(GPort, self).paint(painter, style, widget)
        if self.default:
            p = QtGui.QPainterPath()
            p.addEllipse(QPoint(self.RADIUS, self.RADIUS), self.RADIUS*0.6, self.RADIUS*0.6)
            painter.fillPath(p, QtCore.Qt.darkGray)

class GInputPort(GPort):
    """Class for input data."""
    def __init__(self, index, argument, pos=QPoint(0,0), name="", parent=None):
        """Initializes class.
        :param pos: Position of this action inside parent action.
        :param parent: This port will be part of parent action.
        """
        super(GInputPort, self).__init__(index, argument, pos, name, parent)

    def mousePressEvent(self, event):
        if not self.connections:
            super(GInputPort, self).mousePressEvent(event)
        else:
            self.scene().detach_connection(self, QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier)

class GOutputPort(GPort):
    """Class for output data."""
    def __init__(self, index, pos=QPoint(0,0), name="", parent=None):
        """Initializes class.
        :param pos: Position of this action inside parent action.
        :param parent: This port will be part of parent action.
        """
        super(GOutputPort, self).__init__(index, None, pos, name, parent)
