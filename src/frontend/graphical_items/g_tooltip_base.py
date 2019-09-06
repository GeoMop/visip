from PyQt5.QtCore import QTimer, QPoint, QObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QWidget

from frontend.graphical_items.graphics_proxy_widget import GraphicsProxyWidget
from frontend.widgets.composite_type_view import CompositeTypeView


class GTooltipBase(QGraphicsItem):
    def __init__(self, parent=None):
        super(GTooltipBase, self).__init__(parent)
        self.setAcceptHoverEvents(True)
        self.__timer = QTimer()
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.show_tooltip)
        self.__timer.setInterval(500)
        self.__position = QPoint()
        self.__widget_proxy = GraphicsProxyWidget(self)
        self.__widget_proxy.setVisible(False)
        self.__widget_proxy.hide()
        self.widget = None

    @property
    def widget(self):
        return self.__widget

    @widget.setter
    def widget(self, widget):
        self.__widget = widget
        self.__widget_proxy.setWidget(widget)
        if widget is not None:
            self.__widget.hide()

    def show_tooltip(self):
        if self.__widget is not None:
            self.__widget_proxy.show()
            self.__position = self.scene().views()[0].mapFromGlobal(QCursor.pos())
            self.__position = self.scene().views()[0].mapToScene(self.__position)
            self.__widget_proxy.setPos(self.__position)

            if self.__widget_proxy.scene() is None:
                self.scene().addItem(self.__widget_proxy)


    def hoverEnterEvent(self, event):
        super(GTooltipBase, self).hoverEnterEvent(event)
        if not self.__widget_proxy.isVisible():
            self.__timer.start()

    def hoverLeaveEvent(self, event):
        super(GTooltipBase, self).hoverLeaveEvent(event)
        self.__timer.stop()
        if not self.__widget_proxy.boundingRect().contains(self.mapToItem(self.__widget_proxy, event.pos())):
            self.__widget_proxy.hide()


    def wheelEvent(self, event):
        super(GTooltipBase, self).wheelEvent(event)
        i=1

