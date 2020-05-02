from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QPixmap, QBitmap, QPainter

from visip_gui.graphical_items.g_action import GAction

def make_ref_texture():
    ref_texture = QPixmap(32, 32)
    ref_texture.fill(Qt.gray)
    painter = QPainter(ref_texture)
    pen = QPen(Qt.darkGray)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.drawLine(0, 16, 16, 0)
    painter.drawLine(16, 32, 32, 16)
    painter.drawLine(0, 32, 32, 0)
    return ref_texture

class GActionRef(GAction):
    REF_TEXTURE = None
    def __init__(self, g_data_item, w_data_item, parent=None, eval_gui=None, appending_ports=True):
        if self.REF_TEXTURE is None:
            self.REF_TEXTURE = make_ref_texture()
        super(GActionRef, self).__init__(g_data_item, w_data_item, parent, eval_gui, appending_ports)
        pen = QPen(Qt.black)
        self.setPen(pen)
        brush = QBrush(Qt.darkGray)
        brush.setTexture(self.REF_TEXTURE)
        self.setBrush(brush)

        self.type_name.setText("Ref: " + w_data_item.action.value.name)
        self.width = self.width
