from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainterPath, QPen, QCursor, QTransform, QKeySequence
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsItem, QGraphicsTextItem, QStyle


class GTooltip(QGraphicsTextItem):
    ARROW_HEIGHT = 10
    MARGIN = 3
    LINE_WIDTH = 2

    def __init__(self, g_item, color=Qt.red):

        super(GTooltip, self).__init__()
        self.g_item = g_item
        self.background = QGraphicsPathItem(self)
        self.background.setBrush(Qt.white)
        self.background.setFlag(self.ItemStacksBehindParent, True)
        self.background.setPen(QPen(color, self.LINE_WIDTH))
        self.setAcceptHoverEvents(True)
        self.setZValue(10.0)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.hide()
        self.setCursor(Qt.ArrowCursor)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._show_tooltip)
        self.timer.setInterval(500)
        self.color = color
        self.tooltip_pos = None
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
        self.close_after = 0
        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)

    def disable(self):
        self.timer.timeout.disconnect(self._show_tooltip)

    def enable(self):
        self.timer.timeout.connect(self._show_tooltip())

    def tooltip_request(self, tooltip_pos, color=None, delay=500, close_after=0):
        self.close_after = close_after
        self.timer.setInterval(delay)
        self.timer.start()
        if color is None:
            if self.color is not None:
                self.color = self.color
            else:
                self.color = Qt.black
        else:
            self.color = color
        self.tooltip_pos = tooltip_pos

    def update_pos(self, pos):
        self.tooltip_pos = pos

    def contextMenuEvent(self, event):
        event.accept()

    def set_text(self, text):
        if text != self.toPlainText():
            super(GTooltip, self).setPlainText(text)
            self.update_gfx()

    def update_gfx(self):
        path = QPainterPath()
        rect = super(GTooltip, self).boundingRect()
        rect.adjust(-self.MARGIN + 1, -self.MARGIN + 1, self.MARGIN - 1, self.MARGIN - 1)
        path.addRoundedRect(rect, 3, 3)
        self.background.setPath(path)
        return path

    def shape(self):
        shape = QPainterPath()
        shape.addRect(self.boundingRect())
        return shape

    def boundingRect(self):
        return self.background.boundingRect().adjusted(0, -5, 0, 5)

    def _show_tooltip(self):
        color = self.color

        self.background.setPen(QPen(color, self.LINE_WIDTH))
        if not self.isVisible() and self.toPlainText():
            if self.close_after > 0:
                self.close_timer.setInterval(self.close_after)
                self.close_timer.start()
                self.close_timer.timeout.connect(self.close)
            self.setFocus(Qt.MouseFocusReason)
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)
            view = self.g_item.scene().views()[0]
            view.scroll_changed.connect(self.close)
            view.zoom_changed.connect(self.close)

            tooltip_pos = self.g_item.mapToScene(self.tooltip_pos)
            this_rect = super(GTooltip, self).boundingRect()
            transform = QTransform()
            transform = transform.scale(1/view.zoom, 1/view.zoom)
            this_rect = transform.mapRect(this_rect)
            d_pos = QPoint((-this_rect.width() / 2), (self.ARROW_HEIGHT + self.MARGIN)/view.zoom)

            pos = tooltip_pos + d_pos

            scene_rect = view.mapToScene(view.viewport().geometry()).boundingRect()

            this_rect.moveTo(pos)
            pos.setX(max(scene_rect.left() + self.MARGIN,
                         min(pos.x(), scene_rect.right() - this_rect.width() - self.MARGIN)))
            if scene_rect.bottom() < pos.y() + this_rect.height() + self.ARROW_HEIGHT:
                pos = QPoint(pos.x(), self.tooltip_pos.y() - this_rect.height() - self.ARROW_HEIGHT/view.zoom)
                self.setPos(pos)
                path = self.update_gfx()
                rect = path.boundingRect()
                tooltip_pos = (tooltip_pos - pos) * view.zoom
                path.moveTo(tooltip_pos.x() - self.ARROW_HEIGHT, rect.bottom())
                path.lineTo(tooltip_pos.x(), tooltip_pos.y())
                path.lineTo(tooltip_pos.x() + self.ARROW_HEIGHT, rect.bottom())

            else:
                self.setPos(pos)
                path = self.update_gfx()
                rect = path.boundingRect()
                tooltip_pos = (tooltip_pos - pos) * view.zoom
                path.moveTo(tooltip_pos.x() - self.ARROW_HEIGHT, rect.top())
                path.lineTo(tooltip_pos.x(), tooltip_pos.y())
                path.lineTo(tooltip_pos.x() + self.ARROW_HEIGHT, rect.top())
            self.background.prepareGeometryChange()
            self.background.setPath(path)
            self.g_item.scene().addItem(self)
            self.show()
            self.textCursor().clearSelection()

    def paint(self, painter, style, widget=None):
        style.state &= ~QtWidgets.QStyle.State_Selected
        style.state &= ~QtWidgets.QStyle.State_HasFocus

        super(GTooltip, self).paint(painter, style, widget)

    def setPos(self, *__args):
        super(GTooltip, self).setPos(*__args)

    def setVisible(self, b):
        pass

    def mousePressEvent(self, event):
        super(GTooltip, self).mousePressEvent(event)
        pass

    def hoverEnterEvent(self, event):
        super(GTooltip, self).hoverEnterEvent(event)
        self.close_timer.stop()


    def hoverLeaveEvent(self, event):
        super(GTooltip, self).hoverLeaveEvent(event)
        self.close()

    def close(self):
        if self.isVisible():
            self.g_item.scene().removeItem(self)
            self.hide()
