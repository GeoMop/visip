import typing

from visip import dev, wrap
from visip.dev import dtype
import visip.action as action

import ruamel.yaml as yaml


def test_type_inspection():
    """
    Test own methods that use undocumented features of the testing module.
    """

    class X:
        pass

    # get_generic_args
    assert dtype.get_generic_args(bool) is None
    assert dtype.get_generic_args(X) is None
    assert dtype.get_generic_args(dtype.List[bool]) == (bool,)
    assert dtype.get_generic_args(dtype.Dict[int, float]) == (int, float)
    assert dtype.get_generic_args(dtype.Constant[dtype.List[int]]) == (dtype.List[int],)


def test_data_class_base():
    parameters = dev.Parameters()
    parameters.append(dev.ActionParameter('x'))
    parameters.append(dev.ActionParameter('y'))
    dclass = action.ClassActionBase.dataclass_from_params("my_class", parameters, module="my_module")
    assert dclass.yaml_tag == '!my_class'
    my_instance = dclass(x=3, y=7)
    assert my_instance.x == 3
    assert my_instance.y == 7

    # class serialization
    serialized = yaml.dump(my_instance)
    # assert serialized == "!my_module.my_class {x: 3, y: 7}"


def test_config_generic():
    def get_attr(
            key: dtype.Constant[str],
            dataclass: dtype.Any) -> dtype.Any:
        return dataclass.__getattribute__(key)

    params, result_type = dev.extract_func_signature(get_attr)
    key_type = params.get_name('key').type
    dc_type = params.get_name('dataclass').type
    assert dtype.is_constant(key_type) is True
    assert dtype.is_constant(dc_type) is False
    assert key_type.inner_type() is str


def test_is_base_type():
    assert dtype.is_base_type(int)
    assert dtype.is_base_type(float)
    assert dtype.is_base_type(bool)
    assert dtype.is_base_type(str)
    assert not dtype.is_base_type(dtype.List)
    assert not dtype.is_base_type(dtype.DataClassBase)


class Point2d(dtype.DataClassBase):
    x: float
    y: float


class Point3d(Point2d):
    z: float


def test_is_subtype():
    # assert dtype.is_subtype(Point2d, dtype.DataType)
    assert dtype.is_subtype(Point2d, dtype.DataClassBase)
    assert dtype.is_subtype(Point3d, Point2d)


class A:
    pass


class B(A):
    pass


class C(A):
    pass


class D(B):
    pass


class E(B):
    pass


def test_closest_common_ancestor():
    cca = dtype.closest_common_ancestor
    assert cca(D, E) is B
    assert cca(C, D) is A
    assert cca(A, B) is A
    assert cca(A, int) is object


def test_unwrap_type():
    type_hint = wrap.unwrap_type(typing.List[int])
    print(type_hint)
