import math

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPen, QLinearGradient, QRadialGradient
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsBlurEffect


class Glow(QGraphicsPathItem):
    WIDTH = 5

    def __init__(self, parent):
        super(Glow, self).__init__(parent)
        self.setFlag(self.ItemStacksBehindParent, True)
        self.blur = QGraphicsBlurEffect()
        self.blur.setBlurRadius(8)
        self.setGraphicsEffect(self.blur)

    def update_path(self, path):
        self.setPen(QPen(Qt.darkBlue, self.WIDTH * 2))
        self.setPath(path)



