
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
            self._childs = None
        if self._childs is None:
            self._childs = {}

    @property
    def result(self):
        return self._cache.value(self._task.result_hash)

    def child(self, key):
        return TaskResult(self._childs[key], self._cache)
