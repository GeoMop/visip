class classproperty(object):
    """
    Decorator to define a class property getter, i.e. a function that
    returns value of class property.
    """
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)

