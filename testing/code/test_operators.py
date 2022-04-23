import visip as wf
from visip.dev import evaluation

@wf.workflow
def arithmetic_ops(self, a, b):
    self.A = a + b
    self.B = a - b
    self.c = a * b
    self.d = a / b
    self.e = b % 1
    self.f = a ** 3
    return [self.A, self.B, self.c, self.d, self.e, self.f]

@wf.workflow
def comparison_ops(self, a, b):
    self.A = a > 0
    self.B = a == 1
    self.c = a >= 2
    self.d = b < 2
    self.e = b <= 2
    self.f = b != 2
    return [self.A, self.B, self.c, self.d, self.e, self.f]

def test_operators():
    result = evaluation.run(arithmetic_ops, 1, 2)
    assert result == [3, -1, 2, 0.5, 0, 1]

    result = evaluation.run(comparison_ops, 1, 2)
    assert result == [True, True, False, False, True, False]
