from typing import *
import inspect
from . import dtype
from . import data


class ActionParameter:
    """
    Description of a single parameter of a function (action).
    Simple wrapper around inspect.Parameter
    At least we have to use our own types.
    """
    no_default = inspect.Parameter.empty
    POSITIONAL_ONLY         = inspect.Parameter.POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD   = inspect.Parameter.POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL          = inspect.Parameter.VAR_POSITIONAL
    KEYWORD_ONLY            = inspect.Parameter.KEYWORD_ONLY
    VAR_KEYWORD             = inspect.Parameter.VAR_KEYWORD

    # Class attribute. Single instance object representing no default value.
    def __init__(self, name:str, p_type: dtype.TypeBase, default: object = no_default, kind=POSITIONAL_OR_KEYWORD):
        self._name : str = name
        # Name of the parameter, None for positional only.
        self._default = default
        # Default value of the parameter.
        # NoDefault
        # Indicates that the parameter must be constant wrapped into Value action.
        self._kind = kind
        # Kind of the parameter to be consistent with Python implementation
        if p_type == ActionParameter.no_default:
            p_type = None
        self._type = p_type
        # Type annotation of the parameter, None means missing annotation, but interpreted as Any.

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        if self._type is None:
            return Any
        else:
            return self._type

    @property
    def type_defined(self):
        return self._type

    @property
    def default(self):
        return self._default

    @property
    def kind(self):
        return self._kind

    def get_default(self) -> Tuple[bool, Any]:
        if self.default == ActionParameter.no_default:
            return False, None
        else:
            return True, self.default

    def hash(self):
        p_hash = data.hash(self.name)
        p_hash = data.hash(str(self.type), previous=p_hash)
        p_hash = data.hash(self.default, previous=p_hash)
        p_hash = data.hash(self.kind, previous=p_hash)
        return p_hash

    def __str__(self):
        return f"Parameter: {self.name}: {self.type} = {self.default}"

class Parameters:
    no_default = ActionParameter.no_default
    # For convenience when operating on the Parameters instance.

    def __init__(self, params, return_type=None, had_self=False):
        if return_type == ActionParameter.no_default:
            return_type = None
        self._return_type = return_type
        self._signature = {p.name: p for p in params}
        self.had_self = had_self
        # True if we have removed the special parameter self (in case fo workflow)

    @property
    def return_type(self):
        rt = self._return_type
        if rt is None:
            return Any
        else:
            return rt

    @property
    def return_type_defined(self):
        return self._return_type

    @property
    def var_positional(self):
        for p in self:
            if p.kind == ActionParameter.VAR_POSITIONAL:
                return p
        return None

    @property
    def var_keyword(self):
        for p in self:
            if p.kind == ActionParameter.VAR_KEYWORD:
                return p
        return None

    def __len__(self):
        return len(self._signature)

    def __getitem__(self, name):
        return self._signature.get(name, None)

    _positional_kinds = [ActionParameter.POSITIONAL_ONLY, ActionParameter.POSITIONAL_OR_KEYWORD]

    def at(self, idx):
        """
        Returns positional parameter at index `idx`,
        if VAR_POSITIONAL exists the indices over POSITIONAL
        result to the single VAR_POSITIONAL parameter.
        Otherwise IndexError is rised.
        TODO: possibly remove after changes in GUI
        :param idx:
        :return:
        """
        for p in self:
            if p.kind in self._positional_kinds:
                if idx == 0:
                    return p
                else:
                    idx -= 1
            else:
                if p.kind == ActionParameter.VAR_POSITIONAL:
                    return p
                else: # all parameters after VAR_POSITIONAL are KEYWORD_ONLY
                    raise IndexError
        raise IndexError

    @property
    def parameters(self):
        """
        Generator of parameter values (names are part of the parameters itself).
        """
        return self._signature.values()

    def positional(self):
        """
        Generator of positional parameters.
        :return:
        """
        return (p for p in self.parameters if p.kind in self._positional_kinds)


    def __iter__(self):
        """
        For backward compatibility.
        :return:
        """
        return iter(self._signature.values())