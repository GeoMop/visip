from frontend.analysis.graphical_items.g_action import GAction


class GOutputAction(GAction):
    def __init__(self, graphics_data_item, parent=None):
        super(GOutputAction, self).__init__(graphics_data_item, parent)
        #self.add_port(True, "Input Port")
