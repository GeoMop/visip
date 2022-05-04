#!/bin/python
"""
Usage:
    python3 visip.py env.yaml visip_script.py
"""
import sys
import ruamel.yaml

def default_env():
    return {}

if len(sys.argv) == 1:
    env = default_env()
else:
    with open(sys.argv[0], 'r') as f:
        content = f.readlines()
    env = ruamel.yaml.load(content)

