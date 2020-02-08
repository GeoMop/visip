import collections
from typing import Dict

import ruamel.yaml

import visip
from ..code.decorators import Class, action_def

yaml = ruamel.yaml.YAML(typ='rt')


@yaml.register_class
class CustomTag(ruamel.yaml.comments.CommentedMap):
    """
    class for !Tag representation to yaml
    """
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
        return module.lstrip('!')

    @property
    def get_class_name(self):
        class_name = self._tag.split('.')
        return class_name[-1:][0].lstrip('!')  # always last and single

    @classmethod
    def to_yaml(cls, representer, data):
        return representer.represent_mapping(data._tag, data)


def construct_any_tag(self, tag_suffix, node):
    """
    !tag contructor
    :param self:
    :param tag_suffix:
    :param node:
    :return:
    """
    if tag_suffix is None:
        orig_tag = None
    else:
        orig_tag = "!" + tag_suffix
    if isinstance(node, ruamel.yaml.nodes.MappingNode):
        data = CustomTag(orig_tag)
        yield data
        state = ruamel.yaml.constructor.SafeConstructor.construct_mapping(self, node, deep=True)
        data.update(state)
    else:
        raise NotImplementedError


def get_yaml_serializer():
    """
    Get YAML serialization/deserialization object with proper
    configuration for conversion.
    :return: Configured instance of ruamel.yaml.YAML.
    """
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 120
    yaml.constructor.add_multi_constructor("!", construct_any_tag)
    return yaml


def deep_convert_dict(layer):
    """
    recursive tranform of a CustomTag class to Dict
    :param layer:
    :return: Dict
    """
    to_ret = layer
    if isinstance(layer, collections.OrderedDict):
        if isinstance(layer, CustomTag):
            to_ret.update({'_class_': layer.get_class_name})
            to_ret.update({'_module_': layer.get_module})

        to_ret = dict(layer)
        try:
            for key, value in to_ret.items():
                to_ret[key] = deep_convert_dict(value)
        except AttributeError:
            pass
    elif isinstance(layer, ruamel.yaml.comments.CommentedSeq):
        to_ret = []
        try:
            for elem in layer:
                to_ret.append(deep_convert_dict(elem))
        except AttributeError:
            pass

    return to_ret


@action_def
def load_yaml(path: str) -> dict:
    """
    action that loads yaml file to dictionary
    :param path: file path
    :return: Dict
    """
    yml = get_yaml_serializer()
    with open(path, 'r') as stream:
        data = yml.load(stream)
    data_dict = deep_convert_dict(data)
    return data_dict


@action_def
def write_yaml(data: Dict, path: str) -> FileIn:
    """
    action for writting to yaml
    :param data: Dict to be written
    :param path: file path
    :return: FileIn
    """
    yml = get_yaml_serializer()
    with open(path, 'w')as stream:
        yml.dump(data, stream)

    return visip.file_in.call(path)
