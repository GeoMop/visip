from visip.dev import dtype as dtype

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