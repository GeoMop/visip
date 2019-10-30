from typing import *
from visip.dev import base


class GetAttribute(base._ActionBase):
    """
    Return a class attribute for given fixed key.
    TODO: Do we really need the "configuration" data?
    """
    def __init__(self, key):
        super().__init__()
        self.key = key

    def format(self, representer, action_name, arg_names):
        assert len(arg_names) == 1
        return representer.format([representer.token(arg_names[0]), ".{}".format(self.key)])

    def _evaluate(self, data_class: Any) -> Any:
        return data_class.__getattribute__(self.key)


class GetItem(base._ActionBase):
    """
    Return item of a list given by index.
    """
    def __init__(self):
        super().__init__()

    def format(self, representer, action_name, arg_names):
        assert len(arg_names) == 2
        return representer.format([representer.token(arg_names[0]), "[", representer.token(arg_names[1]), "]"])

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

    KeyType = TypeVar('Key')
    ValType = TypeVar('Value')
    def _evaluate(self, data_dict: Dict[KeyType, ValType], key: KeyType) -> ValType:
        return data_dict[key]


