import visip as wf


@wf.workflow
def comparison_ops(self, a, b):
    self.A = a > 0
    self.B = a == 1
    self.c = a >= 2
    self.d = b < 2
    self.e = b <= 2
    self.f = b != 2
    A_list_1 = [self.A, self.B, self.c, self.d, self.e, self.f]
    return A_list_1


@wf.workflow
def arithmetic_ops(self, a, b):
    self.A = a + b
    self.B = a - b
    self.c = a * b
    self.d = a / b
    self.e = b % 1
    self.f = a ** 3
    self.g = (a + b) // 2
    A_list_1 = [self.A, self.B, self.c, self.d, self.e, self.f, self.g]
    return A_list_1


@wf.workflow
def unary_and_other_ops(self, a, b):
    self.A = wf.abs(- a)
    self.B = wf.abs(+ b)
    self.c = wf.round(number=a + 0.1, ndigits=None)
    self.d = wf.round(number=b - 2.5, ndigits=None)
    self.e = wf.pow(base=a, exp=wf.abs(b), mod=2)
    self.f = wf.divmod(a, b)
    A_list_1 = [self.A, self.B, self.c, self.d, self.e, self.f]
    return A_list_1


@wf.workflow
def complex_expr(self, a, b):
    sub_1 = 2 * (a + b) - b
    return sub_1