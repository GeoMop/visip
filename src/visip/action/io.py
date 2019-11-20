import collections
import os
import re
from collections import abc
import sys
from typing import Any, Dict

import yaml

from ..code.decorators import action
from visip.action.constructor import dict


@action
def load_yaml(path: str, types=None) -> Dict[Any, Any]:
    def default_ctor(loader, tag_suffix, node):
        dictionary = {}

        if '.' in tag_suffix:
            dictionary.update({'__class_name__': tag_suffix.split('.')[0]})
            # může být více modulů
            # fungovat i když tam tečka nebude.... module je vždy poslední string za tečkou.
            dictionary.update({'__module__': tag_suffix.split('.')[1]})
            # vytvořit issue na případy které nejsou jasné
        else:
            dictionary.update({'__module__': tag_suffix})
        # else:
        #     dictionary.update(
        #         {'__tag__': tag_suffix})  # vím, že tag je špatně. Bude vždy rozdělení na class_name a module
        #     nebo může být pouze module, či pouze class_name?

        # rozparsovat a volat dataclass_from_params
        # name = __class_name__
        # params = všechny klíče
        # module = __module__

        dictionary.update(loader.construct_mapping(node, deep=True))

        return dictionary
        # return vytvořených instancí.. přes dataclass_from_params.

    yaml.add_multi_constructor('!', default_ctor, Loader=yaml.SafeLoader)
    # jak funguje register class a add_multi_contructor... který jde jako první? jsou potřeba oba?... zjistit / vyzkoušet

    with open(path, 'r') as stream:
        data = yaml.safe_load(stream)
        vys = yaml.dump(data, sys.stdout)

    return data


def write_yaml(data: Dict, path: str, types=None):  # -> file

    with open(path, 'w')as output:
        yaml.dump(data, output, default_flow_style=False)


path_to_yaml = 'D:\\Git\\muj_visip\\visip\\testing\\action\\test_yamls\\flow_input.yaml'
print(load_yaml(path_to_yaml))

'''
TO ASK:
relativní importy - co dělám špatně?
kam zavést třídu Dict(dict):
Jak jí mám vracet v konstruktoru? --- vracet ji v konstruktoru action/constuctor.py/dict_constr ---
Jak má vypadat Dict.to_yaml k čemu bude sloužit?

Jak správně odekorovat test_io.py? test_evaluation.py by nebyl moc nápomocen, většině testu nerozumím.

instalace mlmc přes pip proběhla v pořádku
test se povedlo spustit ( byla zakomentována změna path )

procházel jsem si i zápis Fields do GMSH - nevím na co přesně koukat nebo na co se zaměřit?
'''
