import visip as wf
from typing import Union, Any




@wf.action_def
def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b

@wf.action_def
def square(a: Union[int, float]) -> Union[int, float]:
    return a * a

@wf.action_def
def sqrt(a: Union[int, float]) -> Union[int, float]:
    import math
    return math.sqrt(a)

@wf.action_def
def delay_data(data: Any, delay: float) -> Any:
    import time
    time.sleep(delay)
    return data