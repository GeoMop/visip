from ..dev import base
from .constructor import Value
from ..dev import dtype
from ..dev.extract_signature import _extract_signature
from ..dev.parameters import Parameters, ActionParameter


class GetAttribute(base.ActionBase):
    """
    Return a class attribute for given fixed key.
    TODO: Do we really need the "configuration" data?
    """
    def __init__(self):
        signature = _extract_signature(self._evaluate)
        signature.check_no_empty()
        super().__init__(signature=signature)
        self.action_kind = base.ActionKind.Generic

    def call_format(self, representer, action_name, arg_names, arg_values):
        assert len(arg_names) == 2
        assert len(arg_values) == 2
        key_action_call = arg_values[0]
        assert isinstance(key_action_call.action, Value)
        key_name = key_action_call.action.value
        data_class_token = representer.token(arg_names[1])
        return representer.format(data_class_token, ".{}".format(key_name))

    def _evaluate(self, key: dtype.Const(dtype.Str), data_class: dtype.DataClassBase) -> dtype.Any:
        return data_class.__getattribute__(key)


class GetItem(base.ActionBase):
    """
    Return item of a list or dict given by index or key.
    Note: Possibly we can distinguish GetItem and GetKey and have better typechecking for the index.
    """
    def __init__(self):
        var_type_t = dtype.TypeVar(name="T")
        params = (
            ActionParameter('data_list', dtype.List(var_type_t)),
            ActionParameter('idx', dtype.Int))
        signature = Parameters(params, var_type_t)
        super().__init__(signature=signature)
        self.action_kind = base.ActionKind.Generic

    def call_format(self, representer, action_name, arg_names, arg_values):
        assert len(arg_names) == 2
        return representer.format(representer.token(arg_names[0]), "[", representer.token(arg_names[1]), "]")

    def _evaluate(self, data_list, idx):
        return data_list[idx]


# class GetKey(base._ActionBase):
#     """
#     Return item of a dict for given key.
#     """
#     def __init__(self):
#         super().__init__()
#
#     def format(self, action_name, arg_names):
#         a_dict, a_key = arg_names
#         return format.Format([format.Token(a_dict), "[", format.Token(a_key), "]"])
#
#     KeyType = TypeVar('Key')
#     ValType = TypeVar('Value')
#     def _evaluate(self, data_dict: Dict[KeyType, ValType], key: KeyType) -> ValType:
#         return data_dict[key]
#

