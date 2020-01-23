"""
This file contains design concepts for the JobPanel - VISIP interaction through
the Resource API. That is the MultiJob pass list of available resources to
an orchestration function (Scheduler), we think about VISIP scheduler, running in a separate thread.
The Scheduler can use the Resource API to create a worker and assign some work to it, monitor the execution etc.
"""
import attr
import enum
from typing import *


class ExecutionModel:
    """
    A model of execution time (or memory) as function of the problem size, run_config, task parameters and resource parameters.
    We shall start with simple linear model, but that can be extended e.g. to a neural network.

    Amdahl's law:

    wall_time = task_cost * ((1-p) + p / n_cores)

    Task cost depends on program (complexity, operations per unit size) and resource.
    In fact this is kind of model that predict number of various kind of operations
    for given program input. Operations should be defined implicitly through
    reference programs running on different resources.

    task_cost = task_size ** complexity * computing_constant

    For the simplest case we assume same complexity for CPU and MEM operations
    and just a single task parameter. Then the multiplicative constant only depends on the resource.

    computing_constant = (program_cpu * resource_cpu_time + program_mem * resource_mem_time) * resource_sharing

    Further some parameters are uncertain:
    - p - parallel fraction of the code, Normal distr. assume small variance
    - complexity - Log normal distr, assume small variance
    - program_cpu, program_mem - poisson
    - resource_XY_time - log normal
    - resource sharing - discrete (1, 2, 3)
    """

    def predict(self, n_cores, task_params, program_params, resource_params):
        pass

@attr.s(auto_attribs=True)
class Resource:
    """
    Represents a logical computational resource with given capabilities.
    In the context of PBS, one resource can be a queue, or particular set of PBS
    tags. Resource provides two kind of functions:
    - information about status of the resource to process a work
    - means to execute some work
    """

    ############################ Constant resource properties
    name: str
    """ Unique name of the resource. """
    execution_model_parameters: List[float]
    """ Resource parameters to the execution model. """
    n_cores: int
    """ Number of available cores. """
    mpi_size: int
    """ 
    Maximum MPI size for single task.
    Sum of MPI sizes for all tasks must be smaller then 'n_cores'.
    mpi_size <= 1    =>  MPI not supported        
    """
    core_memory: int
    """ Memory available per core [bytes]. """
    tags: List[str]
    """ PBS tags."""
    queue_name: str
    """ PBS queue."""

    start_latency: float
    # Average time from assignment to actual execution of the worker. [seconds]
    stop_latency: float
    # Average time from finishing a task till the scheduler is aware of it. [seconds]

    ######################### Resource status

    n_free_cores: int
    workers: Dict[str, "WorkerProxy"]
    """
    Dictionary of active workers.
    """

    def start_worker(self, n_cores, wall_time, memory, init_task_list, **kwargs):
        """
        Start a new worker with given configuration.
        :param n_cores: Number of reserved cores.
        :param wall_time: Total wall time of the worker.
        :param kwargs: Dictionary with future optional parameters.
        :return: WorkerProxy
        """
        pass

    def update_workers(self):
        """ """

class WorkerStatus(enum.IntEnum):
    queued = 0
    running = 1
    finishing = 2
    done = 3



@attr.s(auto_attribs=True)
class WorkerProxy:
    """
    Reserved part of resource with fixed number of cores, reseerved memory and wall time.
    One can assign the work to worker at construction, or add it dynamically through a queue.

    Have instance in master and in the slave job.
    Question: The WorkerProxy should be the proxy interface, the Worker is interface for the remote executing code, but
    the code need not to use it.
    """
    # Constant parameters.
    start_time: float
    end_time: float
    mpi_size: int

    # Current state
    status: WorkerStatus
    """ 
    Status of the worker. Use appropriate Enum from JobPanel."""

    # Communication queues.
    queue: Dict[int, 'TaskProxy']

    inbox_queue: List[Any]

    def assign(self, task: 'TaskProtocol'):
        """
        Assign the task to the (remote) worker.
        :param task: The task object, satisfying a protocol:
        - infiles, indata, outfiles, outdata, code TODO: precise specification
        returns TaskProxy
        """
        pass

    def stop(self, timeout:float=30):
        """
        Stop the worker, retrieve completed tasks. Kill after given timeout.
        :param timeout: [second]
        """
        pass

    def update(self):
        """
        Update status:
         - process incomming messages
         - send new tasks
         - update state informationsaccording to the message queue.
        """
        pass



class TaskProxy:
    """
    Task wrapper that allows to move it to the remote worker.
    Needs:
    - input_files / input_data
    - output_files / output data
    - code to execute

    Currently we allow text messages to be passed from the remote Task to the proxy.
    This can be stdout, or other progress info.
    """

    def __init__(self, task_func, files_in:List[str], data_in, files_out:List[Pattern]):
        """
        :param task_func: A function that will be called. It has to accept 'data_in'  and return 'data_out'.
        task_func(data_in, message_queue = None)
        :param files_in: List of files to move to the remote workspace.
        :param data_in: Data combining dicts, lists and base types. These has to be send.
        :param files_out: Patterns of files to download.
        """
        pass

    @property
    def progress_messages(self):
        """ Return list of recieved messages (progress info). """
        pass

    def is_finished(self):
        """ True when all result data and files are available locally."""
        pass







