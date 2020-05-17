"""
Representation of connection between two ports.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from visip.dev.action_instance import ActionInputStatus
from visip_gui.graphical_items.g_tooltip_item import GTooltipItem
from visip_gui.graphical_items.g_tooltip_base import GTooltipBase
from visip_gui.graphical_items.glow import Glow
import visip_gui.graphical_items.g_status_mapping as mapping

from .g_port import GPort, GOutputPort


class GConnection(QtWidgets.QGraphicsPathItem):
    """Representation of connection between two ports."""
    color = mapping.color
    text = mapping.text

    LINE_THICKNESS = 3

    def __init__(self, port1, port2=None, state=None, parent=None):
        """Initializes connection.
        :param port1: OutputPort or any port if port2 is None.
        :param port2: InputPort.
        :param parent: Action which holds this connection: this connection is inside parent action.
        """
        super(GConnection, self).__init__(parent)
        self.glow = Glow(self)
        self.glow.hide()
        self._shape = QtGui.QPainterPath()
        self.connection_set = False if port2 is None else True
        self.port1 = port1  # either first port when creating connection or always OutputPort if connection is set
        self.port2 = port2 if self.connection_set else GPort(-1, None, self.port1.get_connection_point())  # usually InputPort
        # drawing options
        color = self.color.get(state, Qt.black)
        self.full_pen = QtGui.QPen(color, self.LINE_THICKNESS)
        self.dash_pen = QtGui.QPen(color, self.LINE_THICKNESS, QtCore.Qt.DashLine)
        self.setPen(self.full_pen)
        self.setZValue(10.0)
        self.setFlag(self.ItemIsSelectable)
        self.update_gfx()
        self.setCursor(Qt.ArrowCursor)
        self.setAcceptHoverEvents(True)
        self.tool_tip = GTooltipItem(self, color)
        self.tool_tip.set_text(self.text.get(state, "(Unknown state)"))

    @property
    def name(self):
        if self.connection_set:
            return "Connection from: (" + str(self.port1) + ") to: (" + str(self.port2) + ")"
        else:
            return "Connection from: (" + str(self.port1) + ")"

    def hoverEnterEvent(self, event):
        super(GConnection, self).hoverEnterEvent(event)
        if self.connection_set:
            if (    not self.port1.mapToScene(self.port1.boundingRect()).boundingRect()
                    .contains(self.mapToScene(event.pos())) and
                    not self.port2.mapToScene(self.port2.boundingRect()).boundingRect()
                            .contains(self.mapToScene(event.pos()))):
                self.tool_tip.tooltip_request(event.pos())

    def hoverMoveEvent(self, event):
        if not self.tool_tip.timer.isActive():
            if (not self.port1.mapToScene(self.port1.boundingRect()).boundingRect()
                    .contains(self.mapToScene(event.pos())) and
                    not self.port2.mapToScene(self.port2.boundingRect()).boundingRect()
                            .contains(self.mapToScene(event.pos()))):
                self.tool_tip.tooltip_request(event.pos())
        self.tool_tip.update_pos(event.pos())

    def hoverLeaveEvent(self, event):
        super(GConnection, self).hoverLeaveEvent(event)
        self.tool_tip.timer.stop()

    def is_connected(self, port):
        """Returns True if this connection is attached to specified port."""
        if port == self.port1 or port == self.port2:
            return True
        else:
            return False

    def __repr__(self):
        return self.name



    def mousePressEvent(self, event):
        """Mouse press is ignored by this connection if it is inside port."""
        super(GConnection, self).mousePressEvent(event)
        if self.port1.contains(self.mapToItem(self.port1, event.pos())) or \
                self.port2.contains(self.mapToItem(self.port2, event.pos())):
            event.ignore()
            self.setSelected(False)

    def itemChange(self, change_type, value):
        if change_type == QtWidgets.QGraphicsItem.ItemSelectedHasChanged:
            if self.isSelected():
                self.glow.show()
            else:
                self.glow.hide()
        return super(GConnection, self).itemChange(change_type, value)

    def paint(self, painter, style, widget=None):
        """If connection is selected, draw it as dash line."""
        style.state &= ~QtWidgets.QStyle.State_Selected     # remove selection box
        super(GConnection, self).paint(painter, style, widget)

    def update_gfx(self):
        """Updates model of the connection."""
        self.prepareGeometryChange()
        self.setPath(self.update_path())

    def boundingRect(self):
        return self._shape.boundingRect()

    def update_path(self):
        path = QtGui.QPainterPath()
        p1 = self.port1.get_connection_point()
        p2 = self.port2.get_connection_point() if self.connection_set else self.port2.pos()
        c1 = QtCore.QPointF(p1.x(), (p2.y() + p1.y()) / 2)
        c2 = QtCore.QPointF(p2.x(), (p2.y() + p1.y()) / 2)
        path.moveTo(p1)
        path.cubicTo(c1, c2, p2)

        direction = (p1 - p2)
        direction = direction/direction.manhattanLength()
        direction.setY(-direction.y())
        margin = self.LINE_THICKNESS * QtCore.QPointF(direction.y(),direction.x())

        self._shape = QtGui.QPainterPath()
        self._shape.moveTo(p1 - margin)
        left_curve = path.translated(-margin)
        self._shape.connectPath(left_curve)

        trans = QtGui.QTransform()
        trans.rotate(180)
        right_curve = trans.map(path)
        right_curve.translate(p1 + p2 + margin)

        self._shape.connectPath(right_curve)
        self._shape.closeSubpath()

        self.glow.update_path(path)

        return path

    def shape(self):
        return self._shape

    def set_port2_pos(self, pos):
        """Sets port2's position to allow tracking mouse movement before connection is set."""
        if not self.connection_set:
            self.port2.setPos(self.mapFromScene(pos))
            self.update_gfx()

    def set_port2(self, port):
        """Set port2 to finish creation of connection."""
        if not self.connection_set:
            self.connection_set = True
            if type(port) is GOutputPort:
                self.port2 = self.port1
                self.port1 = port
            else:
                self.port2 = port
            self.update_gfx()
