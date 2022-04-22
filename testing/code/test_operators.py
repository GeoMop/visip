import visip as wf
from visip.dev import evaluation

@wf.workflow
def arithmetic_ops(self, a, b):
    self.a = a + b
    self.b = a - b
    self.c = a * b
    self.d = a / b
    self.e = b % 1
    self.f = a ** 3
    return [self.a, self.b, self.c, self.d, self.e, self.f]

def test_operators():
    result = evaluation.run(arithmetic_ops, 1, 2)
    assert result == [3, -1, 2, 0.5, 0, 1]
