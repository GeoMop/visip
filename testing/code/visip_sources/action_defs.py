from typing import Union, Any

from visip.code import decorators



@decorators.action_def
def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b

@decorators.action_def
def square(a: Union[int, float]) -> Union[int, float]:
    return a * a

@decorators.action_def
def sqrt(a: Union[int, float]) -> Union[int, float]:
    import math
    return math.sqrt(a)

@decorators.action_def
def delay_data(data: Any, delay: float) -> Any:
    import time
    time.sleep(delay)
    return data