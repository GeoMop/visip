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
    def __init__(self, data="No Data", title="Data", parent = None):
        super(CompositeTypeView, self).__init__(parent)
        self.setHeaderHidden(True)
        self.data = data
        self.title = title
        title_item = QTreeWidgetItem([title])
        font = QFont()
        font.setBold(True)
        title_item.setFont(0, font)
        self.invisibleRootItem().addChild(title_item)

        self.fill_item(self.invisibleRootItem(), self.data)

    def set_data(self, data):
        if data != self.data:
            self.data = data
            self.clear()
            title_item = QTreeWidgetItem([self.title])
            font = QFont()
            font.setBold(True)
            title_item.setFont(0, font)
            self.invisibleRootItem().addChild(title_item)
            self.fill_item(self.invisibleRootItem(), self.data)

    def fill_item(self, item, data):
        def new_item(parent, text):
            child = QTreeWidgetItem([str(text)])
            if text not in ("[dict]", "[list]", "[tuple]"):
                pass
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
