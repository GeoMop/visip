import pytest
import visip as wf
from visip.dev import action_instance as instance
from visip.dev import action_workflow as awf
from visip.dev import dtype
from visip.action import constructor
from visip.dev import evaluation
from visip.dev.parameters import ActionParameter

def test_workflow_modification():
    w = awf._Workflow("tst_wf")

    ## Slot modifications
    # insert_slotg_data_item
    w.insert_slot(0, "a_slot", dtype.Int)
    w.insert_slot(1, "b_slot", dtype.Int)
    assert len(w.parameters) == 2
    assert w.parameters.at(0).name == 'a_slot'
    assert w.parameters.at(1).name == 'b_slot'

    # move_slot
    w.insert_slot(2, "c_slot", dtype.Int)
    # A B C
    w.move_slot(1, 2)
    # A C B
    assert w.parameters.at(2).name == 'b_slot'
    assert w.parameters.at(1).name == 'c_slot'
    w.move_slot(2, 0)
    # B A C
    assert w.parameters.at(0).name == 'b_slot'
    assert w.parameters.at(1).name == 'a_slot'
    assert w.parameters.at(2).name == 'c_slot'

    # remove_slot
    w.remove_slot(2)
    assert len(w.parameters) == 2
    assert len(w._slots) == 2
    # TODO: remove connected slot
    # TODO: mark action invalid, generalize to remove_action

    ## ActionCall modifications
    result = w.result_call
    slots = w.slots
    list_action = constructor.A_list()
    list_1 = instance.ActionCall.create(list_action)
    res = w.set_action_input(list_1, 0, slots[0])
    assert res == True
    res = w.set_action_input(list_1, 1, slots[1])
    assert res == True
    res = w.set_action_input(result, 0, list_1)
    assert res == True
    #assert slots[0]._output_actions[0][0] == list_1

    #assert slots[1]._output_actions[0][0] == list_1
    #assert list_1._output_actions[0][0] == result
    assert list_1.name == 'list_1'
    assert len(w._action_calls) == 4
    # w:  (slot0 (B), slot2 (A)) -> List1 -> result

    ## ActionCall rename
    list_1.name ='list_2'
    assert list_1.name == 'list_2'
    assert sorted(list(w.action_call_dict.keys())) == ['__result__', 'a_slot', 'b_slot', 'list_2']


    # unlink
    w.set_action_input(list_1, 0, None)
    assert len(list_1.arguments) == 1
    assert list_1.arguments[0].value is slots[1]
    #assert not slots[0]._output_actions

    # shifted 2. argument, setting the 2. do nothing
    w.set_action_input(list_1, 1, None)
    assert len(list_1.arguments) == 1
    # removing the remaining argument
    w.set_action_input(list_1, 0, None)
    assert len(list_1.arguments) == 0
    # w:  (slot0 (B), slot2 (A))  List1 -> result


    # Test cycle
    w.set_action_input(list_1, 0, slots[0])
    list_2 = instance.ActionCall.create(constructor.A_list())
    w.set_action_input(list_1, 1, list_2)
    # w:  (slot0 (B), List2) -> List1 -> result
    res = w.set_action_input(list_2, 0, list_1)     # Cycle
    assert not res
    assert len(list_2.arguments) == 0

def test_signature():
    w = awf._Workflow("wf_signature")

    # insert_slotg_data_item
    w.insert_slot(0, "a_slot", dtype.Int)
    w.insert_slot(1, "b_slot", dtype.Int)
    assert len(w.parameters) == 2
    assert w.parameters.at(0).name == 'a_slot'
    assert w.parameters.at(1).name == 'b_slot'

    # move_slot
    w.insert_slot(2, "c_slot", dtype.Int)
    # A B C
    w.move_slot(1, 2)
    # A C B
    assert w.parameters.at(2).name == 'b_slot'
    assert w.parameters.at(1).name == 'c_slot'


@wf.workflow
def var_args(self, *args):
    return wf.tuple(self.args[0], self.args[1])

@pytest.mark.skip
def test_workflow_parameters():
    """
    Can not implement workflow with variadic parameters until we interpret code through AST.
    :return:
    """
    res = evaluation.run(var_args, 1, 2, 3)
    assert res == [1,2,3]