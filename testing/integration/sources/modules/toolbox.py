import visip as wf
import time

@wf.action_def
def sleep(t: float):
    """
    Python sleep wrapper.
    """
    time.sleep(t)

