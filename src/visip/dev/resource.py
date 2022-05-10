import multiprocessing
import dill
import queue
import time
import collections
from abc import ABC, abstractmethod

import attrs

from ..eval.cache import ResultCache
from .task import _TaskBase
from . import base
from multiprocessing import Process, Pipe

class Time:
    """
    See: https://peps.python.org/pep-0418
    Starting with use of monotonic, try high resolution timers if neccessry.
    """

    def __init__(self, sync_time):
        self._own_sync_time = self.time()
        self._global_sync_time = sync_time
        self._time_correction = self._global_sync_time - self._own_sync_time
        self.clock_res = time.get_clock_info("monotonic").resolution

    def time(self):
        return time.monotonic()

    def sync_time(self):
        return self.time_correction + self.time()


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
            self.cache.insert(task.result_hash, res_value)

        self._finished.append(task)

    def close(self):
        pass



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
        self.pool = multiprocessing.get_context("spawn").Pool(processes=self._cfg.np)
        self.finished = collections.deque()
        self.action_kind_list = [base.ActionKind.Regular, base.ActionKind.Generic]

        self.n_assigned = 0
        self.time_assigned = 0
        self.n_finished = 0
        self.time_completed = 0

    def estimate_time(self, task):
        return self.n_assigned - self.n_finished

    def get_finished(self):
        n = len(self.finished)
        out = []
        for i in range(n):
            out.append(self.finished.popleft())
        return out

    def add_finished(self, result_blob, err, task):
        if result_blob is None:
            result = None
        else:
            result = dill.loads(result_blob)
        task.error = err
        self.cache.insert(task.result_hash, result)
        self.finished.append(task)
        self.n_finished += 1

    # class action_eval_wrapper:
    #     def __init__(self, task):
    #         self.task = task
    #     def __call__(self, *args, **kwargs):
    #         res = self.task.evaluate_fn(*args, **kwargs)
    #         return (res, self.task)
    #
    #

    @staticmethod
    def do_work(dill_blob):
        fn, args, kwargs = dill.loads(dill_blob)
        return dill.dumps(fn(*args, **kwargs))

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

            def finished(res):
                print("Finished.")
                self.add_finished(res, None, task)

            def error(err):
                print("Error: ", err)
                self.add_finished(None, err, task)


            self.n_assigned += 1
            #self.pool.apply_async(task.evaluate_fn, args, kwargs, callback=finished)
            print("apply_async: ", self.do_work, args, kwargs)
            dill_blob = dill.dumps( (task.action.evaluate, args, kwargs), byref=True )
            self.pool.apply_async(self.do_work, (dill_blob,), {}, callback=finished, error_callback=error)
        else:
            self.finished.put(task)

    def close(self):
        if self.pool is not None:
            self.pool.close()
            self.pool = None
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
