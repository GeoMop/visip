from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainterPath, QPen, QCursor
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsItem, QGraphicsTextItem, QStyle


class GTooltip(QGraphicsTextItem):
    ARROW_HEIGHT = 10
    MARGIN = 3

    def __init__(self, g_item, color=None):
        super(GTooltip, self).__init__()
        self.g_item = g_item
        self.background = QGraphicsPathItem(self)
        self.background.setBrush(Qt.white)
        self.background.setFlag(self.ItemStacksBehindParent, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(10.0)
        self.setFlag(self.ItemIgnoresTransformations, True)
        self.hide()
        self.setCursor(Qt.ArrowCursor)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setTextCursor(self.textCursor())
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._show_tooltip)
        self.timer.setInterval(500)
        self.color = color
        self.tooltip_pos = None

    def tooltip_request(self, tooltip_pos, color=None, interval=500):
        self.timer.setInterval(interval)
        self.timer.start()
        if color is None:
            if self.color is not None:
                self.color = self.color
            else:
                self.color = Qt.black
        self.tooltip_pos = tooltip_pos

    def contextMenuEvent(self, event):
        event.accept()

    def set_text(self, text):
        if text != self.toPlainText():
            super(GTooltip, self).setPlainText(text)
            self.update_gfx()

    def update_gfx(self):
        path = QPainterPath()
        rect = super(GTooltip, self).boundingRect()
        rect.adjust(-2, -2, 2, 2)
        path.addRoundedRect(rect, 3, 3)
        self.background.setPath(path)
        return path

    def shape(self):
        shape = QPainterPath()
        shape.addRect(self.boundingRect())
        return shape

    def boundingRect(self):
        return super(GTooltip, self).boundingRect().united(self.g_item.mapRectToItem(self, self.g_item.boundingRect()))

    def _show_tooltip(self):
        color = self.color

        self.background.setPen(QPen(color))
        if not self.isVisible() and self.toPlainText():

            self.setFocus(Qt.MouseFocusReason)
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)
            view = self.g_item.scene().views()[0]
            tooltip_pos = view.transform().map(self.mapToScene(self.tooltip_pos))


            this_rect = view.mapFromScene(super(GTooltip, self).boundingRect()).boundingRect()


            pos = QPoint(tooltip_pos.x() - this_rect.width() / 2, tooltip_pos.y() + self.ARROW_HEIGHT)



            scene_rect = view.mapToScene(view.viewport().geometry()).boundingRect()
            this_rect.moveTo(pos)
            pos.setX(max(scene_rect.left() + self.MARGIN,
                         min(pos.x(), scene_rect.right() - this_rect.width() - self.MARGIN)))

            tooltip_pos = self.mapFromParent(self.tooltip_pos)
            if scene_rect.height() < this_rect.bottom() + self.ARROW_HEIGHT:
                pos = QPoint(pos.x(),
                             self.tooltip_pos.y() - this_rect.height() - self.ARROW_HEIGHT)
                self.setPos(pos)
                path = self.update_gfx()
                rect = path.boundingRect()
                item_rect = self.g_item.mapRectToItem(self, self.g_item.boundingRect())
                path.moveTo(item_rect.center().x() - self.ARROW_HEIGHT, rect.bottom())
                path.lineTo(item_rect.center().x(), item_rect.top())
                path.lineTo(item_rect.center().x() + self.ARROW_HEIGHT, rect.bottom())
            else:
                self.setPos(pos)
                path = self.update_gfx()
                rect = path.boundingRect()
                item_rect = self.g_item.mapRectToItem(self, self.g_item.boundingRect())
                tooltip_pos = self.mapFromParent(self.tooltip_pos)
                path.moveTo(tooltip_pos.x() - self.ARROW_HEIGHT, rect.top())
                path.lineTo(tooltip_pos.x(), tooltip_pos.y())
                path.lineTo(tooltip_pos.x() + self.ARROW_HEIGHT, rect.top())

            tooltip_pos = self.mapFromScene(self.mapFromItem(self.g_item, self.tooltip_pos))
            print(tooltip_pos)
            path.addEllipse(tooltip_pos, 5,5)
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

    def hoverLeaveEvent(self, *args, **kwargs):
        self.g_item.scene().removeItem(self)
        self.hide()
