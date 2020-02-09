from visip import dev
from visip.dev import dtype, evaluation
import visip.action as action
from visip.code import wrap
import typing
import typing_inspect as ti
import visip as wf

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
    assert dtype.get_generic_args(dtype.Constant[dtype.List[int]]) == (dtype.List[int], )


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
    x:float
    y:float

class Point3d(Point2d):
    z:float


def test_is_subtype():
    #assert dtype.is_subtype(Point2d, dtype.DataType)
    assert dtype.is_subtype(Point2d, dtype.DataClassBase)
    assert dtype.is_subtype(Point3d, Point2d)

@wf.Class
class Point:
    x:float
    y: float

@wf.Class
class Complex:
    p_dict: typing.Dict[int, Point]

def test_type_hint_unwrapping():
    res = evaluation.run(Complex, [{1:Point(2,3)}])



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
    print("\nType Hint:")
    print(type_hint)

    print("\nElement test:")
    class Element:
        nodes:typing.List[int] = []

    for name, ann in Element.__annotations__.items():
        attr_type = wrap.unwrap_type(ann)
        print(name, ann, attr_type)


def test_type_inspect():
    ty = typing
    basic_type = int
    list_type = ty.List[int]
    dict_type = ty.Dict[int, str]
    tuple_type = ty.Tuple[ ty.Dict[int, str], str, ty.List[str]]
    union_type = ty.Union[list_type, dict_type, None]

    type_a = ty.TypeVar('TA')
    type_b = ty.TypeVar('TB')
    gen_list_type = ty.List[type_a]
    gen_dict_type = ty.Dict[type_a, type_b]
    gen_tuple_type = ty.Tuple[type_a, type_b]
    test_types = [basic_type, list_type, dict_type, tuple_type, union_type, gen_list_type, gen_dict_type, gen_tuple_type]

    print("ti.get_origin:\n")
    for t in test_types:
        print("    ", ti.get_origin(t))


    print("ti.get_last_origin:\n")
    for t in test_types:
        print("    ", ti.get_last_origin(t))

    print("ti.get_parameters:\n")
    for t in test_types:
        print("    ", ti.get_parameters(t))

    print("ti.get_args:\n")
    for t in test_types:
        print("    ", ti.get_args(t))

    print("ti.get_last_args:\n")
    for t in test_types:
        print("    ", ti.get_last_args(t))

    print("ti.get_generic_type:\n")
    for t in test_types:
        print("    ", ti.get_generic_type(t))

    print("ti.get_generic_bases:\n")
    for t in test_types:
        print("    ", ti.get_generic_bases(t))

    print("ti.typed_dict_keys:\n")
    for t in test_types:
        print("    ", ti.get_generic_bases(t))
