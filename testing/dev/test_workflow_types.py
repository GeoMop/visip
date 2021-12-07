import visip as wf
from visip.dev import dtype_new, dtype

import typing


def wf_check_type_error(fun):
    try:
        wf.workflow(fun)
    except TypeError:
        pass
    else:
        assert False


def wf_in_types(wf):
    return [slot.actual_output_type for slot in wf.action.slots]


def wf_out_type(wf):
    return wf.action.result.arguments[0].actual_type


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

    @wf.workflow
    def wf_add2(a, b):
        return add(a, b)
    assert dtype_new.is_equaltype(wf_in_types(wf_add2)[0], dtype_new.Int())
    assert dtype_new.is_equaltype(wf_in_types(wf_add2)[1], dtype_new.Int())
    assert dtype_new.is_equaltype(wf_out_type(wf_add2), dtype_new.Int())

    @wf.workflow
    def wf_add_inc(a: int, b: int) -> int:
        return add(a, inc(b))

    @wf.workflow
    def wf_add_pipe(a: int, b: int) -> int:
        return add(a, pipe(b))

    @wf.workflow
    def wf_pipe(a):
        return pipe(a)
    assert wf_in_types(wf_pipe)[0] is wf_out_type(wf_pipe)

    @wf.workflow
    def wf_first(a):
        return first(a)
    assert dtype_new.is_equaltype(wf_in_types(wf_first)[0], dtype_new.List(wf_out_type(wf_first)))

    @wf.workflow
    def wf_to_list(a):
        return to_list(a)
    assert dtype_new.is_equaltype(dtype_new.List(wf_in_types(wf_to_list)[0]), wf_out_type(wf_to_list))

    @wf.workflow
    def wf_first_inc(a):
        return inc(first(a))
    assert dtype_new.is_equaltype(wf_in_types(wf_first_inc)[0], dtype_new.List(dtype_new.Int()))

    @wf.workflow
    def wf_first_to_list(a):
        return to_list(first(a))
    assert isinstance(wf_in_types(wf_first_to_list)[0], dtype_new.List)
    assert dtype_new.is_equaltype(wf_in_types(wf_first_to_list)[0], wf_out_type(wf_first_to_list))

    @wf.workflow
    def wf_first_inc_to_list(a):
        return to_list(inc(first(a)))
    assert dtype_new.is_equaltype(wf_in_types(wf_first_inc_to_list)[0], dtype_new.List(dtype_new.Int()))
    assert dtype_new.is_equaltype(wf_out_type(wf_first_inc_to_list), dtype_new.List(dtype_new.Int()))


    # workflows, typing error
    @wf_check_type_error
    def wf_int_srt(a):
        return inc(str_con(a))

    return


    # workflows, typing not supported
    @wf.workflow
    def wf_union_two_type_var(a, b):
        return two_to_list(a, b)
    # in algorithm occurs union of two type_var
