import attr
from typing import List, Union

@attr.s(auto_attribs=True, frozen=True)
class Placeholder:
    name: str

    def __str__(self):
        return self.name

    def __len__(self):
        return len(self.name)

class Format:
    """
    Code formatting helper.
    Store a line as  a list of strings and placeholders. Supports substitution of other formats.
    """
    @staticmethod
    def action_call(name, arguments):
        """
        Make function call representation.
        :param name: function name
        :param arguments: arguments ... used for placeholder names.
        :return:
        """
        tokens = []
        tokens.append(name)
        tokens.append("(")
        for param_name, arg_name in arguments:
            if param_name is not None:
                tokens.append(param_name + "=")
            tokens.append(Placeholder(arg_name))
            tokens.append(", ")
        tokens.pop(-1)
        tokens.append(")")
        return Format(tokens)

    @staticmethod
    def list(prefix, postfix, arguments):
        """
        Make list creation representation.
        Prefix and postfix strings - opening and closing bracket.
        :param arguments: arguments ... used for placeholder names.
        :return:
        """
        tokens = []
        tokens.append(prefix)
        for param_name, arg_name in arguments:
            assert param_name is None
            tokens.append(Placeholder(arg_name))
            tokens.append(", ")
        tokens.pop(-1)
        tokens.append(postfix)
        return Format(tokens)

    def __init__(self, token_list: List[Union[str, Placeholder]]):
        """
        List of tokens: strings and 'Placeholders'.
        Placeholders are named and can be substituted via. 'substitute' method.
        :param token_list:
        """
        assert all([isinstance(t, (str, Placeholder)) for t in token_list]), token_list
        self.tokens = token_list


    @property
    def placeholders(self):
        return {t.name for t in self.tokens if type(t) is Placeholder}

    def len_est(self):
        """ Relative measure of the length of the representation."""
        return sum([len(t) for t in self.tokens])

    def substitute(self, id_name:str, arg_format: 'Format'):
        """
        Substitute placeholder by other format, by inserting its token list.
        :param id_name: Placeholder's name.
        :param arg_format: Inserted format.
        :return:
        """
        tokens = []
        for token in self.tokens:
            if type(token) is Placeholder and token.name == id_name:
                tokens.extend(arg_format.tokens)
            else:
                tokens.append(token)

        return Format(tokens)

    def final_string(self):
        """Produce final representation, using placeholder names as variable names. """
        tokens = [str(token) for token in self.tokens]
        return "".join(tokens)