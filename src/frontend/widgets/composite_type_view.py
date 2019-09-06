from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem

test_data = { 'key1': 'value1',
              'key2': 'value2',
              'key3': [1,2,3, { 1: 3, 7 : 9}],
              'key4': object(),
              'key5': { 'another key1' : 'another value1',
              'another key2' : 'another value2'} }

class CompositeTypeView(QTreeWidget):
    def __init__(self, data=test_data, title="Data", parent = None):
        super(CompositeTypeView, self).__init__(parent)
        self.setHeaderHidden(True)
        self.data = data

        self.title = QTreeWidgetItem([title])
        font = QFont()
        font.setBold(True)
        self.title.setFont(0, font)
        self.invisibleRootItem().addChild(self.title)

        self.fill_item(self.invisibleRootItem(), self.data)

    def set_data(self, data):
        self.data = data

    def fill_item(self, item, data):
        def new_item(parent, text):
            child = QTreeWidgetItem([str(text)])
            if text not in ("[dict]", "[list]", "[tuple]"):
                pass
                #child.setFlags(child.flags() | Qt.ItemIsEditable)
            parent.addChild(child)

            return child

        if isinstance(data, dict):
            new_parent = new_item(item, f"[{data.__class__.__name__}]")
            for key, value in data.items():
                sub_parent = new_item(new_parent, key)
                self.fill_item(sub_parent, value)

        elif isinstance(data, (tuple, list)):
            new_parent = new_item(item, f"[{data.__class__.__name__}]")
            for val in data:
                self.fill_item(new_parent, val)

        else:
            new_item(item, f"{data}")
