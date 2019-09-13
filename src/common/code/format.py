from typing import Optional
import attr

@attr.s(auto_attribs=True, frozen=True)
class Token:
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
        tokens = []
        tokens.append(name)
        tokens.append("(")
        for param_name, arg_name in arguments:
            if param_name is not None:
                tokens.append(param_name + "=")
            tokens.append(Token(arg_name))
            tokens.append(", ")
        tokens.pop(-1)
        tokens.append(")")
        return Format(tokens)

    @staticmethod
    def list(prefix, postfix, arguments):
        tokens = []
        tokens.append(prefix)
        for param_name, arg_name in arguments:
            assert param_name is None
            tokens.append(Token(arg_name))
            tokens.append(", ")
        tokens.pop(-1)
        tokens.append(postfix)
        return Format(tokens)

    def __init__(self, token_list):
        """
        :param token_list:
        """
        self.tokens = token_list


    @property
    def placeholders(self):
        return {t.name for t in self.tokens if type(t) is Token}

    def len_est(self):
        return sum([len(t) for t in self.tokens])

    def substitute(self, id_name:str, format: 'Format'):
        tokens = []
        for token in self.tokens:
            if type(token) is Token and token.name == id_name:
                tokens.extend(format.tokens)
            else:
                tokens.append(token)

        return Format(tokens)

    def final_string(self):
        tokens = [str(token) for token in self.tokens]
        return "".join(tokens)