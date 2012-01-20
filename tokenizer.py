
class TokenType:
    LITERAL = 1
    OPERATOR = 2

class Tokenizer:
    """
    Customisable tokenizer implemented using regular expressions.

    Intended for ease of use rather than efficiency.
    """

    END_TOKEN = 0
    """Token type passed back from tokenize() signifying end of input stream"""

    whitespace_pattern = re.compile("\s*")

    def __init__(*token_defs):
        """
        Create a tokenizer object passing a list of (regexp_pattern, token_type) tuples.

        token_type is passed back from the tokenize generator to indicate the token type found, and
        regexp_pattern is the regular expression string used to match that token type.

        """

        self.token_types = []
        for regexp_pattern, token_type in token_defs:
            self.token_types.append( (re.compile(regexp_pattern), token_type) )
    
    def tokenize(text):
        """
        Generator function taking input text and returning a sequence of (token_type, token_text)
        tuples.
        """
        pos = 0
        length = len(text)
        while pos < length:

            # skip any whitespace
            m = Tokenizer.whitespace_pattern.match(self.text, self.pos)
            if m:
                self.pos += len(m.group(0))

            # attempt to match token types
            matched = False
            for regexp, token_type in self.token_types:
                m = pattern.match(self.text, self.pos)
                if m:
                    self.pos += len(m.group(0))
                    yield token_type, m.group(0)
                    break

            if not matched:
                raise SyntaxError("Can't tokenize input")
            
        yield END_TOKEN, ""    
