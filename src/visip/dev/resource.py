import multiprocessing
import queue
from abc import ABC, abstractmethod

import attrs

from ..eval.cache import ResultCache
from .task import _TaskBase
from . import base
from multiprocessing import Process, Pipe

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

    # def assign_task(self, task, i_thread=None):
    #     """
    #     Just evaluate tthe task immediately.
    #     :param task:
    #     :param i_thread:
    #     :return:
    #     """
    #     task.evaluate()
    #
    # def assign_mpi_task(self, task, n_mpi_procs=None):
    #     pass

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
            res_value = task.evaluate_fn(*args, **kwargs)
            # print(task.action)
            # print(task.inputs)
            # print(task_hash, res_value)
            self.cache.insert(task.result_hash, res_value)

        self._finished.append(task)


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


    def __init__(self, config: dict, cache:ResultCache):
        self._cfg = self.Config(**config)
        self.cache = cache
        self.pool = multiprocessing.Pool(self._cfg.np)
        self.finished = queue.Queue()
        self.action_kind_list = [base.ActionKind.Regular, base.ActionKind.Generic]

    def get_finished(self):
        out = []
        try:
            while True:
                out.append(self.finished.get_nowait())
        except queue.Empty:
            return out

    def add_finished(self, res_task):
        result, task = res_task
        self.cache.insert(task.result_hash, result)
        self.queue.put(task)

    class action_eval_wrapper:
        def __init__(self, task):
            self.task = task
        def __call__(self, *args, **kwargs):
            res = self.task.evaluate_fn(*args, **kwargs)
            return (res, self.task)

    def submit(self, task: _TaskBase):
        print("multiproc submit")
        res_value = self.cache.value(task.result_hash)
        if res_value is self.cache.NoValue:
            #assert task.is_ready()
            data_inputs = [self.cache.value(ih) for ih in task.input_hashes]
            #if any([i is self.cache.NoValue for i in data_inputs]):
            #    print(task.action, data_inputs)
            assert not any([i is self.cache.NoValue for i in data_inputs])
            args, kwargs = task.inputs_to_args(data_inputs)
            self.pool.apply_async(self.action_eval_wrapper(task), *args, **kwargs, callback=self.add_finished)
        else:
            self.finished.put(task)


    # def process_task(task):
    #     self.cache.insert(task.result_hash, res_value)


_resource_classes = [
    Multiprocess
]
_resources_dict = {r.__name__: r for r in _resource_classes}
def create(conf: dict, cache: ResultCache):
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
    return [res_class(conf, cache) for i in range(n_instances)]
