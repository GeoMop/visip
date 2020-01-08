import ruamel.yaml

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


# @Class
def load_yaml(path):
    yml = get_yaml_serializer()
    with open(path, 'r') as stream:
        data = yml.load(stream)
    return data


# @Class
def write_yaml(data, path):
    yml = get_yaml_serializer()
    with open(path, 'w')as stream:
        yml.dump(data, stream)


# yaml = ruamel.yaml.YAML()
# yaml.constructor.add_multi_constructor("!", construct_any_tag)
# data = yaml.load(yaml_str)
# yaml.dump(data, sys.stdout)

# path = "D:\\Git\\visip_fork\\visip\\testing\\action\\test_yamls\\flow_input.yaml"
# data = load_yaml(path)
# print(data)

# print(data['problem'].get_tag)
# print(data['problem'].get_module)
# print(data['problem'].get_class_name)

# write_yaml(data, "pokus.yaml")
