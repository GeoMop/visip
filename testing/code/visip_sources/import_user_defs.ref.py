import visip as wf
import action_defs


@wf.workflow
def te(self, slot, slot1):
    A_tuple_1 = (slot, action_defs.add(a=slot, b=slot1))
    return A_tuple_1


@wf.analysis
def er(self):
    system_1 = wf.system(arguments=['cd'], stdout=None, stderr=None, workdir='')
    return system_1