import sys

import yaml


def load_yaml(path):
    # tags = ['!Coupling_Sequential', '!Flow_Darcy_MH', '!Petsc', '!vtk', '!Coupling_OperatorSplitting',
    #         '!Solute_Advection_FV', '!DualPorosity',
    #         '!SorptionMobile', '!FirstOrderReaction', '!SorptionImmobile']

    def default_ctor(loader, tag_suffix, node):
        # print(loader.construct_mapping(node, deep=True))

        ## zakomentovaný slovník je bez vytvoření tříd
        # slovnik = {tag_suffix: loader.construct_mapping(node, deep=True)}
        ##tento slovník vytváří třídy pro všechny parametry s '!'
        slovnik = {tag_suffix: type(tag_suffix, (object,), loader.construct_mapping(node, deep=True))}
        # print(slovnik)
        # print(type(tag_suffix, (object,), loader.construct_mapping(node, deep=True)))
        return slovnik

    yaml.add_multi_constructor('', default_ctor, Loader=yaml.SafeLoader)

    with open(path, 'r')as stream:
        data = yaml.safe_load(stream)
        # print(data)
        # print(data['problem']['!Coupling_Sequential']['mesh'])

        # print(yaml.dump(data, sys.stdout, default_flow_style=False))
    return data


print(load_yaml('flow_input.yaml'))
data = load_yaml('flow_input.yaml')
print('_nic$')
# class Struct:
#     def __init__(self, **entries):
#         self.__dict__.update(entries)


# def create_objs(data):
#     for key, value in data.items():
#         print(key)
#         if '!' in str(value):
#             print(value)
#             print('neco')
#             obj = type(key, (object,), value)
#             print(obj)


# obj = type('Data', (object,), load_yaml('flow_input.yaml'))
# print(obj.problem['Coupling_Sequential'])

# create_objs(load_yaml('flow_input.yaml'))

# s = Struct(**data)
# print(s.problem['!Coupling_Sequential']['description'])
# print(s.problem['!Coupling_Sequential']['flow_equation'])
