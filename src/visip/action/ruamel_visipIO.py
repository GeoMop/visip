import collections
import re
import sys
# from collections import Iterable

import ruamel.yaml
from ruamel.yaml.compat import ordereddict
from ruamel.yaml.scalarstring import walk_tree, preserve_literal, SingleQuotedScalarString

from src.visip.code.decorators import Class, action_def

yaml = ruamel.yaml.YAML(typ='rt')


@yaml.register_class
class MyMap(ruamel.yaml.comments.CommentedMap):
    def __init__(self, tag):
        ruamel.yaml.comments.CommentedMap.__init__(self)
        self._tag = tag

    @property
    def get_tag(self):
        return self._tag

    @property
    def get_module(self):
        full_tag = self._tag.split('.')
        module = ".".join(full_tag[:len(full_tag) - 1])
        return module.lstrip('!')  # strip '!'

    @property
    def get_class_name(self):
        class_name = self._tag.split('.')
        return class_name[-1:][0].lstrip('!')  # always last and single

    @classmethod
    def to_yaml(cls, representer, data):
        return representer.represent_mapping(data._tag, data)


def construct_any_tag(self, tag_suffix, node):
    if tag_suffix is None:
        orig_tag = None
    else:
        orig_tag = "!" + tag_suffix
    if isinstance(node, ruamel.yaml.nodes.MappingNode):
        data = MyMap(orig_tag)
        yield data
        state = ruamel.yaml.constructor.SafeConstructor.construct_mapping(self, node, deep=True)
        data.update(state)
    else:
        raise NotImplementedError


def get_yaml_serializer():
    """
    Get YAML serialization/deserialization object with proper
    configuration for conversion.
    :return: Confugured instance of ruamel.yaml.YAML.
    """
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 120
    yaml.constructor.add_multi_constructor("!", construct_any_tag)
    return yaml


# @action_def
def load_yaml(path) -> MyMap:
    yml = get_yaml_serializer()
    with open(path, 'r') as stream:
        data = yml.load(stream)

    return data


@action_def
def write_yaml(data, path) -> str:
    yml = get_yaml_serializer()
    with open(path, 'w')as stream:
        yml.dump(data, stream)

    return 'zapsano'


# yaml = ruamel.yaml.YAML()
# yaml.constructor.add_multi_constructor("!", construct_any_tag)
# data = yaml.load(yaml_str)
# yaml.dump(data, sys.stdout)

path = "D:\\Git\\visip_fork\\visip\\testing\\action\\test_yamls\\flow_input.yaml"
data = load_yaml(path)


# print(type(data))

# print(data.get('problem').get_tag)


def deep_convert_dict(layer):
    to_ret = layer
    if isinstance(layer, collections.OrderedDict):
        if isinstance(layer, MyMap):
            # print(layer.get_tag)
            to_ret.update({'_class_': layer.get_class_name})
            to_ret.update({'_module_': layer.get_module})
        # elif isinstance(layer, ruamel.yaml.comments.CommentedMap):
        #     print(layer)
        #     print('_')
        to_ret = dict(layer)
        try:
            for key, value in to_ret.items():
                to_ret[key] = deep_convert_dict(value)
        except AttributeError:
            pass
    elif isinstance(layer, ruamel.yaml.comments.CommentedSeq):
        to_ret = list(layer)
        try:
            to_ret = deep_convert_dict(to_ret)
        except AttributeError:
            pass

    return to_ret


trans = deep_convert_dict(data)
print(trans)
print(list(trans))
# print(type(trans['problem']['flow_equation']['input_fields']))
# print(type(trans))

# pokus = dict(data)
#
# print(pokus)
#
#
# def dfs(node, ndict):
#     for idx, values in node.items():
#         ndict[idx] = values
#         ndict['children'] = []
#         if isinstance(values, MyMap) or isinstance(values, ruamel.yaml.comments.CommentedMap):
#             for idx, child in enumerate(values.items()):
#                 child_dict = {}
#                 dfs(child, child_dict)
#                 ndict['children'].append(child_dict)
#         else:
#             pass

# my_dict = {}
# dfs(pokus, my_dict)
# print(data['problem'].get_tag)
# print(data['problem'].get_module)
# print(data['problem'].get_class_name)

# write_yaml(data, "pokus.yaml")
