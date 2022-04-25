import visip as wf
from visip.dev import evaluation


@wf.workflow
def comparison_ops(self, a, b):
    self.A = a > 0
    self.B = a == 1
    self.c = a >= 2
    self.d = b < 2
    self.e = b <= 2
    self.f = b != 2
    return [self.A, self.B, self.c, self.d, self.e, self.f]


@wf.workflow
def arithmetic_ops(self, a, b):
    self.A = a + b
    self.B = a - b
    self.c = a * b
    self.d = a / b
    self.e = b % 1
    self.f = a ** 3
    self.g = (a+b) // 2
    return [self.A, self.B, self.c, self.d, self.e, self.f, self.g]


@wf.workflow
def unary_and_other_ops(self, a, b):
    self.A = wf.abs(-a)
    self.B = wf.abs(+b)
    self.c = wf.round(a + 0.1)
    self.d = wf.round(b - 2.5)
    self.e = wf.pow(a, wf.abs(b), 2)
    self.f = wf.divmod(a, b)
    return [self.A, self.B, self.c, self.d, self.e,self.f]


def test_operators():
    result = evaluation.run(arithmetic_ops, 1, 2)
    assert result == [3, -1, 2, 0.5, 0, 1, 1]

    result = evaluation.run(comparison_ops, 1, 2)
    assert result == [True, True, False, False, True, False]

    result = evaluation.run(unary_and_other_ops, 1, -2)
    assert result == [1, 2, 1, -4, 1, (-1, -1)]
