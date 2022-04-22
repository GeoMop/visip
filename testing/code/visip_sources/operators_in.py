import visip as wf

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

@wf.workflow
def complex_expr(self, a, b):
    return 2*(a + b) - b
