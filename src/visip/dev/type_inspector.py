import typing
import typing_inspect
import enum
from .dtype import DataClassBase
from . import base
from . import tools

class TypeInspector_36:
    """
    Dropback solution for python < 3.7.4.
    """
    map_origin = {typing.List: list, typing.Dict: dict, typing.Tuple: tuple, typing.Union: typing.Union}
    origin_typing = {list: typing.List, dict: typing.Dict, tuple: typing.Tuple, typing.Union: typing.Union}

    def is_any(self, xtype):
        return xtype is typing.Any

    def is_base_type(self, xtype):
        """ True for basic, i.e. scalar types."""
        valid_base_types = (bool, int, float, complex, str)
        return xtype in valid_base_types

    def is_enum(self, xtype):
        try:
            return issubclass(xtype, enum.IntEnum)
        except:
            return False

    def is_newtype(self, xtype):
        try:
            self.newtype_detail(xtype)
            return True
        except AttributeError:
            return False

    def newtype_detail(self, xtype):
        return (xtype.__name__, xtype.__supertype__)

    def get_origin(self, xtype):
        """
        Returns: list, dict, tuple, typing.Union (also for typing.Optional),
        None for: scalar types, None, and typing.Any
        Compatible with Python 3.8.
        :param xtype: a typehint.
        :return:
        """
        origin = typing_inspect.get_origin(xtype)
        return self.map_origin.get(origin, None)

    def get_typing_origin(self, xtype):
        return self.origin_typing[self.get_origin(xtype)]

    def get_args(self, xtype):
        return typing_inspect.get_last_args(xtype)

    def is_dataclass(self, xtype):
        try:
            return issubclass(xtype, DataClassBase)
        except:
            return False

    # def is_constant(self, xtype):
    #     return self.get_origin(xtype) is Constant

    def constant_type(self, xtype):
        return self.get_args(xtype)[0]

    def is_dict(self, xtype):
        return self.get_origin(xtype) == dict

    def have_attributes(self, xtype):
        return self.is_any(xtype) or self.is_dataclass(xtype) or self.is_dict(xtype)

    def is_callable(self, xtype):
        try:
            return issubclass(xtype, dtype._ActionBase)
        except:
            return False

    def is_subtype(self, xtype, type_spec):
        """
        pytypes works only for 3.6
        TODO!!! implement
        :param xtype:
        :param type_spec:
        :return:
        """
        return False


class TypeInspector_37(TypeInspector_36):
    """
    Solution for 3.7.4 <= python < 3.8.
    """
    def get_origin(self, xtype):
        """
        Returns: list, dict, tuple, typing.Union (also for typing.Optional),
        None for: scalar types, None, and typing.Any
        Compatible with Python 3.8.
        :param xtype: a typehint.
        :return:
        """
        return typing_inspect.get_origin(xtype)

    def get_args(self, xtype):
        return typing_inspect.get_args(xtype)


@tools.fallback(TypeInspector_36, before_version=(3, 7, 4))
@tools.fallback(TypeInspector_37, before_version=(3, 8, 0))
class TypeInspector(TypeInspector_37):
    """
    Based typing inspection, which is supported for python >= 3.8
    """

    # def is_any(self, xtype):
    #     return xtype is typing.Any
    #
    # def is_base_type(self, xtype):
    #     """ True for basic, i.e. scalar types."""
    #     return self.isinstance(xtype, valid_base_types)

    def get_origin(self, xtype):
        """
        Returns: list, dict, tuple, typing.Union (also for typing.Optional),
        None for: scalar types, None, and typing.Any
        Compatible with Python 3.8.
        :param xtype: a typehint.
        :return:
        """
        return typing.get_origin(xtype)


    def get_args(self, xtype):
        return typing.get_args(xtype)




