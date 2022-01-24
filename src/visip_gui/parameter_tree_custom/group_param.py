from pyqtgraph import parametertree



class GroupParam(parametertree.parameterTypes.GroupParameter):

    def __init__(self, name, data):
        super(GroupParam, self).__init__(name=name, type="group", readonly=True)
        self.tree_item = None
        self.data = data
        self.opts["expanded"] = False

    def makeTreeItem(self, depth):

        self.tree_item = self.itemClass(self, depth, self.on_expand)
        return self.tree_item

    def on_expand(self):
        pass