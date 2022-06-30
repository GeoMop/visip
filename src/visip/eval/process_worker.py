from typing import *
import multiprocessing as mp
import queue
import attrs
import time
import sys
import traceback
from .eval_time import Time
from ..dev.exceptions import InterpreterError
from ..dev import dtype
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
        self._requests, self._results, self._ping = queues
        print(f"Spawn {worker_cls} {args}")
        try:
            self.worker = worker_cls(*args)
        except Exception as e:
            print(args)
            self._results.put(Result(-1, None, None, e, 0, 0))
            raise e

        #self._results.put("TEST")

    def __del__(self):
        self.close()

    def close(self):
        self._results.put(None)
        _close_queue(self._results)
        _close_queue(self._results)

    def loop(self):
        while True:
            try:
                payload = self._requests.get(timeout=1)
            except queue.Empty:
                self._ping.put("PING")
                time.sleep(1)
                replay = self._ping.get_nowait()
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
                result = self.process(*payload)# process
                print("put: ", result)
                self._results.put(result)


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
        return Result(id, None, value, error, start_time, end_time)



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
        self._queue_send = self._ctx.Queue()
        self._queue_recv = self._ctx.Queue()
        self._ping = self._ctx.Queue() # If worker has no work check regularly that main process is live.

        self._job_map = {}
        assert isinstance(setup_args, tuple)
        args = (self.time.sync_time(),
                (self._queue_send, self._queue_recv, self._ping),
                worker_class, setup_args)
        self._proc = self._ctx.Process(target=self.run, args=args)
        self._proc.start()
        #tst = self._queue_recv.get(timeout=0.1)
        #print("GET :", tst)

    def __del__(self):
        self.close()

    def ping_pong(self):
        try:
            m = self._ping.get_nowait()
        except queue.Empty:
            return
        else:
            self._ping.put("PONG")
        return

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
        self._queue_send.put(p)
        self.ping_pong()


    def get(self) -> Optional[Result]:
        # first obtained result
        self.ping_pong()
        try:
            result = self._queue_recv.get_nowait()
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
            self._queue_send.put(None)
        except ValueError:
            pass
        time.sleep(0.1)
        _close_queue(self._queue_send)
        _close_queue(self._queue_recv)
        self._proc.join()

