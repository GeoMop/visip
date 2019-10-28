
import indexed
from typing import *

from common import action_base as base
from common.code import format






class GetAttribute(base._ActionBase):
    """
    Return a class attribute for given fixed key.
    TODO: Do we really need the "configuration" data?
    """
    def __init__(self, key):
        super().__init__()
        self.key = key

    def format(self, action_name, arg_names):
        assert len(arg_names) == 1
        return format.Format([format.Token(arg_names[0]), ".{}".format(self.key)])

    def _evaluate(self, data_class: Any) -> Any:
        return data_class.__getattribute__(self.key)




class GetItem(base._ActionBase):
    """
    Return item of a list given by index.
    """
    def __init__(self):
        super().__init__()

    def format(self, action_name, arg_names):
        assert len(arg_names) == 2
        return format.Format([format.Token(arg_names[0]), "[", format.Token(arg_names[1]), "]"])

    def _evaluate(self, data_list: List[Any], idx: int) -> Any:
        return data_list[idx]


class GetKey(base._ActionBase):
    """
    Return item of a dict for given key.
    """
    def __init__(self):
        super().__init__()

    def format(self, action_name, arg_names):
        a_dict, a_key = arg_names
        return format.Format([format.Token(a_dict), "[", format.Token(a_key), "]"])

    def _evaluate(self, data_dict: Dict[Any], key: Any) -> Any:
        return data_dict[key]


