from typing import *
import attr
import os

@attr.define
class PBS:
    queue: str
    memory: int



@attr.define
class Environment:
    workspace: str = "~/_visip_workspace"
    resources: list = []
    pbs: PBS = None
    container: str = None

    @staticmethod
    def load(config:Dict[str, Any]):
        if 'pbs' in config:
            config['pbs'] = PBS(config['pbs'])
        env = Environment(**config)

        # full workspace path
        env.workspace = os.path.abspath(os.path.expanduser(env.workspace))
        return env
