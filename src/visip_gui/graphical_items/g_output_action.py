from visip_gui.graphical_items.g_action import GAction
from visip_gui.graphical_items.g_workflow_sr_port import GWorkflowSRPort


class GOutputAction(GAction):
    def __init__(self, g_data_item, w_data_item, parent=None, eval=None, appending_ports=True):
        super(GOutputAction, self).__init__(g_data_item, w_data_item, parent, eval, appending_ports)

    def _add_ports(self, n_ports, appending=False):
        for i in range(n_ports):
            self.add_g_port(True, "Input Port" + str(i))
        if appending and self.appending_ports:
            self.add_g_port(True, "Appending port")
            self.in_ports[-1].appending_port = True

        self.out_ports.append(GWorkflowSRPort(False, parent=self))
