# import collections
import keyword
# import os
# import re
# from collections import abc
# import sys
from typing import Any, Dict

import yaml
# import ruamel.yaml as ruml
# from ruamel.yaml.comments import CommentedMap

# from ruamel.yaml import YAML, yaml_object

# from visip.action.constructor import dict
from ..dev.parameters import Parameters, ActionParameter
from ..code.decorators import action_def
from ..action.constructor import ClassActionBase
from ..dev.dtype import DataClassBase


# from visip.action.constructor import ClassActionBase
# from visip.dev.dtype import DataClassBase
# from visip.dev.parameters import Parameters, ActionParameter, NoDefault


def is_valid_identifier(s):
    return s.isidentifier() and not keyword.iskeyword(s)


@action_def
def load_yaml(path: str):
    def default_ctor(loader, tag_suffix, node):
        dictionary = {}

        if '.' in tag_suffix:
            complete_tag = tag_suffix.split('.')
            dictionary.update({'__module__': '.'.join(complete_tag[:len(complete_tag) - 1])})
            # může být více modulů
            # fungovat i když tam tečka nebude.... module je vždy poslední string za tečkou.
            if is_valid_identifier(complete_tag[-1]):
                dictionary.update({'__class_name__': complete_tag[-1]})
            else:
                dictionary.update({'__class_name__': 'Not valid identifier'})
            # kontrolovat zda má python valid class name fci nebo ošetření ... popřípadě assert

            # vytvořit issue na případy které nejsou jasné
        else:
            dictionary.update({'__class_name__': tag_suffix})
            # dictionary.update({'__module__': None})

        # rozparsovat a volat dataclass_from_params
        # name = __class_name__
        # params = všechny klíče
        # module = __module__

        # ord_dict = CommentedMap()
        # loader.construct_mapping(node, ord_dict, deep=True)
        # # print('____')
        # dictionary.update(ord_dict)
        dictionary.update(loader.construct_mapping(node, deep=True))

        parameters = Parameters()
        for param in dictionary.keys():
            if param == '__module__' or param == '__class_name__':
                pass
            else:
                parameters.append(ActionParameter(param))
        try:
            class_obj = ClassActionBase.dataclass_from_params(name=dictionary['__class_name__'], params=parameters,
                                                              module=dictionary['__module__'])
        except KeyError:
            class_obj = ClassActionBase.dataclass_from_params(name=dictionary['__class_name__'], params=parameters)

        # print(dictionary)
        for drop in ['__class_name__', '__module__']:
            dictionary.pop(drop, None)

        return class_obj(**dictionary)  # dictionary
        # return vytvořených instancí.. přes dataclass_from_params.

    yaml.add_multi_constructor('!', default_ctor, Loader=yaml.SafeLoader)

    with open(path, 'r') as stream:
        data = yaml.safe_load(stream)
        # data = yml.load(stream)
        # vys = yaml.dump(data, sys.stdout)
    # parameters = Parameters()
    # for param in data.keys():
    #     if param == '__module__' or param == '__class_name__':
    #         pass
    #     parameters.append(ActionParameter(param))
    #
    # whole_obj = ClassActionBase.dataclass_from_params(name='flow_input', params=parameters)
    return data  # whole_obj(**data)


@action_def
def write_yaml(data: Dict, path: str):  # -> file
    yaml.SafeDumper.add_multi_representer(DataClassBase, DataClassBase.to_yaml)
    # yaml.representer.add_representer(DataClassBase, DataClassBase.to_yaml)

    with open(path, 'w')as output:
        yaml.safe_dump(data, output, default_flow_style=False)
        # yml.dump(data, output)


# path_to_yaml = 'D:\\Git\\visip_fork\\visip\\testing\\action\\test_yamls\\flow_input.yaml'
#
# vysledek = load_yaml(path_to_yaml)
# print(vysledek)
# print(load_yaml(path_to_yaml))
# print('__')
# print(vysledek.problem)
# print(vysledek['problem'].description)

# write_yaml(vysledek, 'D:\\Git\\muj_visip\\visip\\testing\\action\\test_yamls\\write_yaml.yaml')
# print('_')

# yaml.add_multi_constructor()
# yaml.register_class() <-- pouze ruamel


# rozdíl mezi loaded a written
# https://www.diffchecker.com/hFQNpkfj <-- psaný file má rozdíly
#
#
# https://www.diffchecker.com/RXZCa8Ck <-- python object je identický
#
#
# když loadnu file, který byl zapsán dostanu to samé.
#
# jak ostatní soubory, třeba write_yaml_observe?

# representer.py -- represent_mapping -- zakomentováno sortování aby file byl opravdu stejný.

# proč potřebujeme přednost pro registrované třídy? Nejsem si 100% jistý, ale sám nedokážu napsat kód, který by využil
# yaml.register_class a zároveň yaml.add_multi_contructor.