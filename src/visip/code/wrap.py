"""
Wrap an action instance construction in order to return the constructec ActionInstance be
wrapped into Dummy object.
"""
import typing
import typing_inspect as ti


from ..dev import dtype as dtype
from ..dev import base
from ..action import constructor
from ..dev import action_instance as instance
from . import dummy





# def separate_underscored_keys(arg_dict: typing.Dict[str, typing.Any]):
#     underscored = {}
#     regular = {}
#     for key, value in arg_dict.items():
#         if dummy.is_underscored(key):
#             underscored[key] = value
#         else:
#             regular[key] = value
#     return (regular, underscored)



# class ActionWrapper:
#     def __init__(self, action):
#         assert isinstance(action, base._ActionBase), f"{action}"
#         self.__name__ = action.__name__
#         self.__module__ = action.__module__
#         self.action = action
#         self.is_analysis = False
#
#
#     def __call__(self, *args, **kwargs):
#         """
#         Catch all arguments.
#         Separate private params beginning with underscores.
#         (Undummy action inputs, wrap non-action inputs)
#         Create under laying action, connect to inputs.
#         Return action wrapped into the Dummy.
#         """
#         #regular_inputs, private_args = separate_underscored_keys(kwargs)
#         # print("Instance: ", self.action.name, args, regular_inputs)
#         result_call = instance.ActionCall.create(self.action, *ac_args, **ac_kwargs)
#         # TODO: check that inputs are connected.
#         # result_call.set_metadata(private_args)
#         return dummy.Dummy.wrap(result_call)
#
#     # def call(self,  *args, **kwargs):
#     #     """
#     #     Call an action from an action_def, i.e. regular Python function.
#     #     :param args:
#     #     :param kwargs:
#     #     :return:
#     #     """
#     #     # TODO: assert for arguments types
#     #     return self.action.evaluate(args, kwargs)
#
