from ..dev.action_instance  import ActionCall
from ..dev import dtype
from ..dev.action_workflow import _Workflow
from typing import *
from ..code.unwrap import into_action
from .constructor import Value, A_list, A_dict, A_tuple, _Operator
from .converter import GetAttribute, GetItem
from ..dev.meta import DynamicCall
from .slots import actioncalls_from_function




class ActionFactory:
    """
    Auxiliary class for dependency injection of action call creation into Dummy classes.
    """
    af = None

    @classmethod
    def instance(cls):
        """
        Singleton instance.
        """
        actions = [A_list, A_dict, A_tuple, GetAttribute, GetItem]
        if cls.af is None:
            cls.af = ActionFactory(actions)
        return cls.af

    def __init__(self, actions: List[dtype._ActionBase]):
        # actions are instances of the classes
        self._actions = {a.__name__: a() for a in actions}
        pass

    def __getattr__(self, action_name:str):
        """
        Return function for creating instance of `action_name`.
        Usage: action_call = af.A_list(*attrs)
               action_call = af.GetAttr(dict, key)
        :return: function returning action call
        """
        action = self._actions[action_name]
        return self._lazy_action(action)

    # def make_class(self):
    #     action = ...
    #     return lambda *args, **kwargs : self._create(action, *args, **kwargs)

    def _lazy_action(self, action):
        return lambda *args, **kwargs: self.create(action, *args, **kwargs)

    def create(self, action, *args, **kwargs):
        """
        Recursively unwrap arguments,
        create action_call for action and given arguments.
        """
        assert isinstance(action, dtype._ActionBase)
        ac_args = [into_action(arg) for arg in args]
        ac_kwargs = { key: into_action(val) for key, val in kwargs.items() }
        return ActionCall.create(action, *ac_args, **ac_kwargs)

    def create_value(self, value):
        return into_action(value)

    def create_dynamic_call(self, value, *args, **kwargs):
        assert isinstance(value, ActionCall)
        # dynamic call
        assert True #ti.is_callable(value.return_type):
        dynamic_action = value
        return self.create(DynamicCall(), dynamic_action, *args, **kwargs)

    def create_workflow_from_source(self, func):
        return _Workflow.from_source(func)

    _operator_actions = {}
    def create_operator(self, op_fn, *args):
        op_action = self._operator_actions.setdefault(id(op_fn), _Operator(op_fn))
        return self.create(op_action, *args)

    def actioncalls_from_function(self, func, params):
        return actioncalls_from_function(self, func, params)