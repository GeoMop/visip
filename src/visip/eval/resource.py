from visip.dev.module import Module
from abc import ABC, abstractmethod
from typing import *
import attrs

from visip.eval.cache import ResultCache
from visip.dev.task import _TaskBase
from ..dev import base, tools
from visip.eval.process_worker import WorkerProxy

class ResourceBase(ABC):
    """
    Interface of a resource for the scheduler.
    Constructor should take care of starting the resource's task executing script (pool)
    and connection to it.
    """

    @abstractmethod
    def get_finished(self):
        """
        Return list of finished tasks (_TaskBase).
        """
        pass

    @abstractmethod
    def submit(self, task: _TaskBase):
        """
        Pass the task to be processed (asynchronously).
        """
        pass

    def estimate_time(self, task:'TaskSchedule') -> float:
        """
        Return estimated time of completition of the task on the resource.
        Time is given as number of seconds from the evaluation start, using resource synchronisation
        time and time from last synchronisation.
        """

class Resource:
    """
    Model for a computational resource.
    Resource can provide various kind of feautres specified by dictionary of tags with values None, int or string.
    A task (resp. its action) can specify requested tags, such task can be assigned only to the resource that
    have these tags and have value of an integer tag greater then value of the task.

    We shall start with fixed number of resources, dynamic creation of executing PBS jobs can later be done.

    """
    def __init__(self, cache: ResultCache):
        """
        Initialize time scaling and other features of the resource.
        """
        self.start_latency = 0.0
        # Average time from assignment to actual execution of the task. [seconds]
        self.stop_latency = 0.0
        # Average time from finished task till assignment to actual execution of the task. [seconds]
        self.ref_time = 1.0
        # Average run time for a reference task with respect to the execution on the reference resource.
        self.n_threads = 1
        # Number of threads we can assign to the resource.
        self.n_mpi_proces = 0
        # Maximal number of MPI processes one can assign.
        self._finished = []


        self.cache = cache

        self.action_kind_list = [base.ActionKind.Regular, base.ActionKind.Meta, base.ActionKind.Generic]
        # list of action kind that this resource is capable run

    def estimate_time(self, task):
        return 2


    def get_finished(self):
        """
        Return list of the tasks finished since the last call.
        :return:
        """
        finished = self._finished
        self._finished = []
        return finished

    def submit(self, task: _TaskBase):
        """
        Basic resource implementation with immediate evaluation of the task during submit.
        :param task:
        :return:
        """

        # TODO: move skipping of finished tasks to the scheduler before submit
        # Do not test again in the Resource, possibly only for longer tasks
        res_value = self.cache.value(task.result_hash)
        if res_value is self.cache.NoValue:
            #assert task.is_ready()
            data_inputs = [self.cache.value(ih) for ih in task.input_hashes]
            #if any([i is self.cache.NoValue for i in data_inputs]):
            #    print(task.action, data_inputs)
            assert not any([i is self.cache.NoValue for i in data_inputs])
            args, kwargs = task.inputs_to_args(data_inputs)
            res_value = task.action.evaluate(*args, **kwargs)
            # print(task.action)
            # print(task.inputs)
            # print(task_hash, res_value)
            self.cache.insert(task.result_hash, res_value, (0,0))

        self._finished.append(task)

    def close(self):
        pass

@attrs.define
class Payload:
    module: str
    name: str
    args: List[Any]
    kwargs: Dict[str, Any]

class _ActionWorker:
    """
    Worker with action resolution from the main maodule.
    """
    def __init__(self, main_module_path:str):
        self.module = Module.load_module(main_module_path)
        pass

    def eval(self, payload: Payload):
        print("eval ", payload)
        evaluate = Module.resolve_function(payload.module, payload.name)
        value = evaluate(*(payload.args), **(payload.kwargs))
        print("    .. don: ", value)
        return value


class Multiprocess:
    """
    - can have this , but looks as a single resource to the Scheduler.
    - rather implemnt MPI Pool:
      - responsible for passing the task
      - passing workspace
      - passing function through mpi4py
    """
    @attrs.define
    class Config:
        type: str
        multiplicity: int = attrs.field(converter=int, default=1)
        np: int = attrs.field(converter=int, default=1)


    def __init__(self, config: dict, cache:ResultCache, main_module_path):
        self._cfg = self.Config(**config)
        self.cache = cache
        self.process = WorkerProxy(_ActionWorker, setup_args=(main_module_path,))
        self.action_kind_list = [base.ActionKind.Regular, base.ActionKind.Generic]

        self.time_assigned = 0
        self.time_completed = 0
        self.finished = []

        self._module = Module.load_module(main_module_path)

    def __del__(self):
        self.close()

    @property
    def n_assigned(self):
        return self.process.n_assigned

    @property
    def n_finished(self):
        return self.process.n_finished

    def estimate_time(self, task):
        return self.n_assigned - self.n_finished

    def get_finished(self):
        all_finished = self.finished
        self.finished = []

        while True:
            r = self.process.get()
            if r is None:
                return all_finished
            # print("GET ", r)
            if r.error is None:
                self.cache.insert(r.request.result_hash, r.value, (r.start_time, r.end_time))
                all_finished.append(r.request)
            else:
                raise r.error

    def submit(self, task: _TaskBase):
        #print("multiproc submit")
        res_value = self.cache.value(task.result_hash)
        if res_value is self.cache.NoValue:
            data_inputs = [self.cache.value(ih) for ih in task.input_hashes]
            assert not any([i is self.cache.NoValue for i in data_inputs])
            args, kwargs = task.inputs_to_args(data_inputs)
            mod, name = tools.mod_name(task.action)

            #action = self._module.get_module(mod).get_action(name)
            # TODO: check action serialization before submitting

            payload = Payload(mod, name, args, kwargs)

            # print("PUT:", payload)
            self.process.put(payload, ref=task)
        else:
            self.finished.put(task)

    def close(self):
        if self.process is not None:
            self.process.close()

_resource_classes = [
    Multiprocess
]
_resources_dict = {r.__name__: r for r in _resource_classes}
def create(conf: dict, cache: ResultCache, main_module_path):
    """
    Create particular resource instance from a dict.
    """
    resource_type = conf.get('type', None)
    if resource_type is None:
        raise ValueError("Missing key 'type', resource type.")
    res_class = _resources_dict.get(resource_type, None)
    if res_class is None:
        raise ValueError(f"Wrong resource type: {resource_type}. Possible values: {_resources_dict.keys()}.")
    n_instances = conf.get('multiplicity', 1)
    return [res_class(conf, cache, main_module_path) for i in range(n_instances)]
