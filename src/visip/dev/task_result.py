
class TaskResult:
    """
    Wrapper to traverse the evaluation tree.
    """
    def __init__(self, task, cache):
        self._cache = cache
        self._task: 'task.TaskSchedule' = task
        try:
            self._childs = self._task.childs
        except:
            # Atomic
            # self._childs = None
            self._childs = {}
            self._result_task = self._task
        else:
            # Composed
            self._result_task = self._childs['__result__']



    @property
    def result(self):
        return self._cache.value(self._result_task.result_hash)

    def child(self, key):
        return TaskResult(self._childs[key], self._cache)
