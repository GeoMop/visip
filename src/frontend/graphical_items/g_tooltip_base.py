from PyQt5.QtCore import QTimer, QPoint, QObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QWidget

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
        self.__widget_proxy = QGraphicsProxyWidget(self)
        self.__widget_proxy.setVisible(False)
        self.__widget_proxy.hide()
        self.widget = CompositeTypeView()
        self.widget.hide()


    @property
    def widget(self):
        return self.__widget

    @widget.setter
    def widget(self, widget):
        self.__widget = widget
        self.__widget_proxy.setWidget(widget)

    def show_tooltip(self):
        self.__widget_proxy.show()
        print(QCursor.pos())
        self.__position = self.scene().views()[0].mapFromGlobal(QCursor.pos())
        print(self.__position)
        self.__widget_proxy.setPos(self.__position)
        self.scene().addItem(self.__widget_proxy)

        self.__widget_proxy.ensureVisible()

    def hoverEnterEvent(self, event):
        super(GTooltipBase, self).hoverEnterEvent(event)
        self.__timer.start()

    def hoverLeaveEvent(self, event):
        super(GTooltipBase, self).hoverLeaveEvent(event)
        self.__timer.stop()
        self.__widget_proxy.hide()

    def wheelEvent(self, event):
        super(GTooltipBase, self).wheelEvent(event)
        i=1

