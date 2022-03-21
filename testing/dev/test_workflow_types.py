import visip as wf
from visip.dev import dtype

import typing


def wf_check_type_error(fun):
    try:
        wf.workflow(fun)
    except TypeError:
        pass
    else:
        assert False


def wf_in_types(wf):
    return [slot.actual_output_type for slot in wf.workflow.slots]


def wf_out_type(wf):
    return wf.workflow.result_call.arguments[0].actual_type


def test_workflow_types():
    t = typing.TypeVar("T")

    # actions
    @wf.action_def
    def inc(a: int) -> int:
        return a + 1

    @wf.action_def
    def add(a: int, b: int) -> int:
        return a + b

    @wf.action_def
    def str_con(a: str, b: str) -> str:
        return a + b

    @wf.action_def
    def pipe(a: t) -> t:
        return a

    @wf.action_def
    def first(a: typing.List[t]) -> t:
        return a[0]

    @wf.action_def
    def to_list(a: t) -> typing.List[t]:
        return [a]

    @wf.action_def
    def two_to_list(a: t, b: t) -> typing.List[t]:
        return [a, b]

    @wf.action_def
    def list_append(a: typing.List[t], b: t) -> typing.List[t]:
        return a.append(b)

    @wf.action_def
    def list_con(a: typing.List[t], b: typing.List[t]) -> typing.List[t]:
        return a + b


    # workflows, typing OK
    @wf.workflow
    def wf_add(a: int, b: int) -> int:
        return add(a, b)
    assert not wf_add.workflow._type_error_list

    @wf.workflow
    def wf_add2(a, b):
        return add(a, b)
    assert not wf_add2.workflow._type_error_list
    assert dtype.is_equaltype(wf_in_types(wf_add2)[0], dtype.Int())
    assert dtype.is_equaltype(wf_in_types(wf_add2)[1], dtype.Int())
    assert dtype.is_equaltype(wf_out_type(wf_add2), dtype.Int())

    @wf.workflow
    def wf_add_inc(a: int, b: int) -> int:
        return add(a, inc(b))
    assert not wf_add_inc.workflow._type_error_list

    @wf.workflow
    def wf_add_pipe(a: int, b: int) -> int:
        return add(a, pipe(b))
    assert not wf_add_pipe.workflow._type_error_list

    @wf.workflow
    def wf_pipe(a):
        return pipe(a)
    assert not wf_pipe.workflow._type_error_list
    assert wf_in_types(wf_pipe)[0] is wf_out_type(wf_pipe)

    @wf.workflow
    def wf_first(a):
        return first(a)
    assert not wf_first.workflow._type_error_list
    assert dtype.is_equaltype(wf_in_types(wf_first)[0], dtype.List(wf_out_type(wf_first)))

    @wf.workflow
    def wf_to_list(a):
        return to_list(a)
    assert not wf_to_list.workflow._type_error_list
    assert dtype.is_equaltype(dtype.List(wf_in_types(wf_to_list)[0]), wf_out_type(wf_to_list))

    @wf.workflow
    def wf_first_inc(a):
        return inc(first(a))
    assert not wf_first_inc.workflow._type_error_list
    assert dtype.is_equaltype(wf_in_types(wf_first_inc)[0], dtype.List(dtype.Int()))

    @wf.workflow
    def wf_first_to_list(a):
        return to_list(first(a))
    assert not wf_first_to_list.workflow._type_error_list
    assert isinstance(wf_in_types(wf_first_to_list)[0], dtype.List)
    assert dtype.is_equaltype(wf_in_types(wf_first_to_list)[0], wf_out_type(wf_first_to_list))

    @wf.workflow
    def wf_first_inc_to_list(a):
        return to_list(inc(first(a)))
    assert not wf_first_inc_to_list.workflow._type_error_list
    assert dtype.is_equaltype(wf_in_types(wf_first_inc_to_list)[0], dtype.List(dtype.Int()))
    assert dtype.is_equaltype(wf_out_type(wf_first_inc_to_list), dtype.List(dtype.Int()))


    # workflows, typing error
    #@wf_check_type_error
    @wf.workflow
    def wf_int_srt(a):
        return inc(str_con(a, a))
    assert wf_int_srt.workflow._type_error_list


    # workflows, typing not supported
    @wf.workflow
    def wf_union_two_type_var(a, b):
        return two_to_list(a, b)
    # in algorithm occurs union of two type_var
    assert wf_union_two_type_var.workflow._unable_check_types
