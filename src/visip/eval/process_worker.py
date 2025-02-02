from typing import *
import multiprocessing as mp
import queue
import attrs
import time
import sys
import traceback
import threading
from enum import IntEnum
from .eval_time import Time
from ..dev.exceptions import InterpreterError
from ..dev import dtype
from visip.eval.redis_queue import RedisQueue
# Important multiprocessing tips:
# https://www.cloudcity.io/blog/2019/02/27/things-i-wish-they-told-me-about-multiprocessing-in-python/


@attrs.define
class Result:
    id: int
    request: Any
    value: Any
    error: Optional[Exception]
    start_time: float
    end_time: float


class MessageType(IntEnum):
    none = 0
    request = 1
    result = 2
    ping = 3
    elapsed_time = 4


class QueueWrapper:
    def __init__(self, queue):
        self.queue = queue
        self.local_queue = []

    def get(self, type, timeout=None):
        # check if desired type is in local queue
        for i in range(len(self.local_queue)):
            if self.local_queue[i][0] == type:
                return self.local_queue.pop(i)[1]

        start_time = time.monotonic()
        while True:
            elapsed_time = time.monotonic() - start_time
            if timeout is None:
                item = self.queue.get()
            elif elapsed_time < timeout:
                item = self.queue.get(timeout=timeout - elapsed_time)
            else:
                item = self.queue.get_nowait()

            if item[0] == type:
                return item[1]
            else:
                self.local_queue.append(item)

    def get_nowait(self, type):
        return self.get(type, timeout=0.0)


def _close_queue(q):
    q.close()   # indicate no more put items
    try:
        while q.get_nowait():
            pass
    except queue.Empty:
        pass
    except (ValueError, OSError):
        pass
    q.join_thread()


class _ProcessWorker:
    """
    Actual worker class instantiated and processing the requests in separate process.
    """
    def __init__(self, sync_time, queues, worker_cls, *args):
        self.time = Time(sync_time)
        self._requests = RedisQueue(queues[0])
        self._results = RedisQueue(queues[1])
        self._requests_wrapper = QueueWrapper(self._requests)
        print(f"Spawn {worker_cls} {args}")
        try:
            self.worker = worker_cls(*args)
        except Exception as e:
            print(args)
            self._results.put((MessageType.result, Result(-1, None, None, e, 0, 0)))
            raise e

        #self._results.put("TEST")

        self._thread = None
        self._thread_result = None

    def __del__(self):
        self.close()

    def close(self):
        self._results.put((MessageType.request, None))
        #_close_queue(self._results)
        #_close_queue(self._results)

    def loop(self):
        while True:
            try:
                payload = self._requests_wrapper.get(MessageType.request, timeout=1)
            except queue.Empty:
                self._results.put((MessageType.ping, "PING"))
                time.sleep(1)
                replay = self._requests_wrapper.get_nowait(MessageType.ping)
                if replay == "PING":
                    raise Exception("Dead master.")
                print("No payload to process.")

                continue
            except (ValueError, OSError):
                # possibly closed queue, stop processing
                raise Exception("Closed queue")
            else:
                if payload is None:
                    # stop processing
                    return
                self._thread = threading.Thread(target=self.process, args=payload, daemon=True)
                self._thread_result = None
                self._thread.start()
                start_time = self.time.sync_time()
                while self._thread.is_alive():
                    self._thread.join(timeout=1)
                    elapsed_time = self.time.sync_time() - start_time
                    self._results.put((MessageType.elapsed_time, elapsed_time))
                self._thread = None
                print("put: ", self._thread_result)
                self._results.put((MessageType.result, self._thread_result))


    def process(self, id, args):
        start_time = self.time.sync_time()
        value = dtype.EmptyType
        error = None
        try:
            value = self.worker.eval(args)
        except Exception as err:
            error_class = err.__class__.__name__
            detail = err.args[0] if err.args else None
            etype, exc, tb = sys.exc_info()
            line_number = traceback.extract_tb(tb)[-1][1]

            traceback.print_exception(etype, exc, tb)
            InterpreterError(f"{error_class} at line {line_number} of {'NO FILE'} : {detail}")

        print("process ", value, error)
        end_time = self.time.sync_time()
        self._thread_result = Result(id, None, value, error, start_time, end_time)



class WorkerProxy:

    @staticmethod
    def run(sync_time, queues, worker_cls, args):
        """
        Creates the _ProcessWorker in separate process, starts the processing loop.
        """
        proc = _ProcessWorker(sync_time, queues, worker_cls, *args)
        proc.loop()

    def __init__(self, worker_class, setup_args):
        self.time = Time()
        # Reference time at the master process.
        self.n_assigned: int = 0
        # total number of assigned jobs.

        self.n_finished: int = 0
        # total number of finished (completed/error) jobs.
            #self.close()

        # creates queues , start process
        self._ctx = mp.get_context('spawn')
        self._queue_send = RedisQueue()
        self._queue_recv = RedisQueue()
        self._queue_recv_wrapper = QueueWrapper(self._queue_recv)
        #self._ping = self._ctx.Queue() # If worker has no work check regularly that main process is live.

        self._job_map = {}
        assert isinstance(setup_args, tuple)
        args = (self.time.sync_time(),
                (self._queue_send.id, self._queue_recv.id),
                worker_class, setup_args)
        self._proc = self._ctx.Process(target=self.run, args=args)
        self._proc.start()
        #tst = self._queue_recv.get(timeout=0.1)
        #print("GET :", tst)

    def __del__(self):
        self.close()

    def ping_pong(self):
        try:
            m = self._queue_recv_wrapper.get_nowait(MessageType.ping)
        except queue.Empty:
            return
        else:
            self._queue_send.put((MessageType.ping, "PONG"))
        return

    def get_elapsed_time(self):
        try:
            m = self._queue_recv_wrapper.get_nowait(MessageType.elapsed_time)
        except queue.Empty:
            return
        else:
            print("elapsed_time: ", m)

    def put(self, payload, ref=None):
        """
        # put to processing queue
        """
        if ref is None:
            ref = payload
        id = self.n_assigned
        self.n_assigned += 1
        assert id not in self._job_map
        self._job_map[id] = ref
        p = (id, payload)
        print("put: ", p)
        self._queue_send.put((MessageType.request, p))
        self.ping_pong()


    def get(self) -> Optional[Result]:
        # first obtained result
        self.ping_pong()
        self.get_elapsed_time()
        try:
            result = self._queue_recv_wrapper.get_nowait(MessageType.result)
        except queue.Empty:
            return None
        except (ValueError, OSError):
            pass
        else:
            print("get: ", result)
            if result is not None:
                self.n_finished += 1
                assert isinstance(result, Result)
                result.request = self._job_map[result.id]
                del self._job_map[result.id]
                return result
        print("Preliminary closed _queue_recv")
        self.close()
        assert False

    def n_unprocessed(self):
        return self.n_assigned - self.n_finished

    def close(self):
        try:
            self._queue_send.put((MessageType.request, None))
        except ValueError:
            pass
        time.sleep(0.1)
        #_close_queue(self._queue_send)
        #_close_queue(self._queue_recv)
        self._proc.join()

