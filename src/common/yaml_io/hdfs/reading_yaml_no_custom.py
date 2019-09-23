from dataclasses import dataclass
from typing import List, Dict

import attr
import yaml


# with open("no_custom.yaml", 'r')as stream:
#     data = yaml.safe_load(stream)
#     print(data)


# for i in data.values():
#     for x in i:
#         for y in x.values():
#             if isinstance(y, list):
#                 print(*y)
#             else:
#                 print(y)
@dataclass
class data_type:
    time: float
    region: str
    area: float
    average: List[float]
    minimum: List[float]
    maximum: List[float]

    def __iter__(self):
        pass


def data_constructor():
    vysledek = []
    with open("no_custom.yaml", 'r')as stream:
        data = yaml.safe_load(stream)
        # print(data['data'][1])
        for i in data['data']:
            # print(i)
            # print(type(data))
            DData = data_type(i['time'], i['region'], i['area'], i['average'], i['min'], i['max'])
            # print(DData)
            # Heat_AdvectionDiffusion_region_stat.append(dato=DData)
            vysledek.append(DData)

    # print(vysledek)
    # print('____')
    for i in vysledek:
        print(i.time)
    # print(Heat_AdvectionDiffusion_region_stat)
    # print(type(Heat_AdvectionDiffusion_region_stat))


data_constructor()
