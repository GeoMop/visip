import collections
import re
from collections import abc
import sys
from typing import Any, Dict

import yaml


def load_yaml(path: str, types=None) -> Dict[Any, Any]:
    def default_ctor(loader, tag_suffix, node):
        dictionary = {}

        if tag_suffix:
            dictionary.update({'__tag__': tag_suffix})

        dictionary.update(loader.construct_mapping(node, deep=True))

        return dictionary

    yaml.add_multi_constructor('!', default_ctor, Loader=yaml.SafeLoader)

    with open(path, 'r') as stream:
        data = yaml.safe_load(stream)
        # vys = yaml.dump(data, sys.stdout)

    return data


def write_yaml(data: Dict, path: str, types=None):  # -> file

    def pruchod(d):
        print(d.get('__tag__'))
        for key, val in d.items():
            if isinstance(val, dict):
                # print(key, val)
                pruchod(val)
            elif isinstance(val, list):
                # print(key, val)
                pass
            else:
                # print(key, val)
                pass

    # print(pruchod(data))
    print('_____')
    print('_____')
    print(pruchod(data))

    with open(path, 'w')as output:
        yaml.dump(data, output, default_flow_style=False)


