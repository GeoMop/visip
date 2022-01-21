from visip.code.unwrap import into_action, action_wrap
from visip.dev.action_instance import ActionCall
from visip.action.constructor import Value
from visip.code.dummy import Dummy, DummyAction
from visip.action.action_factory import ActionFactory
from visip.action.constructor import A_dict, A_list, A_tuple
from visip.dev import exceptions
import visip as wf

@wf.Class
class Point:
    x:float
    y: float

def check_val(val, ref):
    assert isinstance(val, ActionCall)
    assert isinstance(val.action, Value), f"type: {type(val)}, value: {val} "
    assert val.action.value == ref

def check_val_actions(val, ref):
    assert isinstance(val, ActionCall)
    assert isinstance(val.action, Value), f"type: {type(val)}, value: {val} "
    assert val.action.value == ref

def test_into_action():
    check_val(into_action(1), 1)
    check_val(action_wrap(1), 1)
    check_val(into_action("a"), "a")
    check_val(action_wrap("a"), "a")
    check_val(into_action(1.1), 1.1)
    check_val(action_wrap(1.1), 1.1)
    check_val(into_action(None), None)
    check_val(action_wrap(None), None)
    check_val(into_action(True), True)
    check_val(action_wrap(False), False)

    # dataclasses are not unwrapped directly by into_action
    # but when their construction is turned into an action call
    p = Point.evaluate(x=1, y=2)
    res = into_action(p)
    assert isinstance(res.action, Value)
    assert res.action.value.x == 1
    assert res.action.value.y == 2

    # Dummies
    af = ActionFactory.instance()
    check_val(into_action(Dummy(af, action_wrap(1))), 1)

    #check_val(into_action(DummyAction(af, Value(5))), Value(5))
    # TODO: should we wrap action into action call as well ?

    check_val(into_action([1,2]), [1,2])
    assert isinstance(into_action([1, action_wrap(2)]).action, A_list)
    check_val(into_action((1,2)), (1,2))
    t = (1, action_wrap(2))
    res = into_action(t)
    assert isinstance(res.action, A_tuple)
    check_val(into_action({1: 2}), {1: 2})
    d = {1: action_wrap(2), 2: 3}
    res = into_action(d)
    assert isinstance(res.action, A_dict)
    assert isinstance(res.arguments[1].value, ActionCall)

    try:
        d = {action_wrap(1): 2}
        res = into_action(d)
    except exceptions.ExcConstantKey:
        pass
    else:
        assert False
