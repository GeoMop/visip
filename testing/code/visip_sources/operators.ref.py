import visip as wf


@wf.workflow
def arithmetic_ops(self, a, b):
    self.A = a + b
    self.B = a - b
    self.c = a * b
    self.d = a / b
    self.e = b % 1
    self.f = a ** 3
    list_1 = [self.A, self.B, self.c, self.d, self.e, self.f]
    return list_1


@wf.workflow
def comparison_ops(self, a, b):
    self.A = a > 0
    self.B = a == 1
    self.c = a >= 2
    self.d = b < 2
    self.e = b <= 2
    self.f = b != 2
    list_1 = [self.A, self.B, self.c, self.d, self.e, self.f]
    return list_1


@wf.workflow
def complex_expr(self, a, b):
    sub_1 = 2 * (a + b) - b
    return sub_1