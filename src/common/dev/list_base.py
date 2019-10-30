import typing
from . import base
from . import parameters

class _ListBase(base._ActionBase):
    """
    Base action class for actions accepting any number of unnamed parameters.
    """
    # We assume that parameters are used only in reinit, which do not use it
    # in this case. After reinit one should use only self.arguments.

    def __init__(self):
        super().__init__()
        self.parameters = parameters.Parameters()
        self.parameters.append(
            parameters.ActionParameter(name=None, type=typing.Any,
                            default=self.parameters.no_default))
