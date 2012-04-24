# Copyright (c) 2012 Jon Coppeard
# See the file LICENSE for copying permission.

"""
Top-down operator precendence parser library.

This is based on code from:
http://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing/

Concepts:

 - token type: an object representing the type of the token.
   Paser.END_TOKEN is a special token type representing the end of the
   input stream.

 - token: a tuple of (token_type, token_content, token_line,
   token_column).  token_conent is the text content of the token.

 - expression spec: an object used to map token types to handler
   functions called when the token is encountered.
"""

import re
from StringIO import StringIO

class Assoc:
    """
    Defines constants for left/right associative binary oprators, used
    by ExprSpec.add_binary_op().

    The values are added to the operator precedence value to obtain the
    final right binding power - do not change the values.
    """
    LEFT = 0
    RIGHT = -1

class Token:
    """
    Represents a token in the input stream.  It has the following
    attributes:

    type -- the type of token.  This can be any object including an
    constant integer or string.

    content -- the text content of the token

    filename -- optional, the name of the input file where the token was
    found

    line_pos -- optional, the line number in the input file where the
    token was found

    column_pos -- optional, the column number in the input file where
    the token was found
    """

    """Token type representing the end of the token stream"""
    END_TOKEN = -1

    def __init__(self, type, content, filename = None, line_pos = None, column_pos = None):
        self.type = type
        self.content = content
        self.filename = filename
        self.line_pos = line_pos
        self.column_pos = column_pos

    def __repr__(self):
        if self.type == Token.END_TOKEN:
            tt = "Token.END_TOKEN"
        else:
            tt = repr(self.type)
        return "Token(%s, %s)" % (tt, repr(self.content))

class ParseError(Exception):
    """
    Raised when an error occurs in tokenizing or parsing.  The exception has two
    attributes:

    token -- the token that was being parsed when the error occured

    value -- a descriptive message
    """
    def __init__(self, token, message):
        self.token = token
        self.value = message

    def __str__(self):
        m = self.value
        t = self.token
        if t.filename:
            m += " in " + t.filename
        if t.line_pos:
            m += " at line " + str(t.line_pos)
            if t.column_pos != None:
                m += " column " + str(t.column_pos)
        return m

class Tokenizer:
    """
    A customisable tokenizer class which uses regular expressions to match
    tokens.
    """

    whitespace_pattern = "\s*"

    def __init__(self, *token_defs):
        """
        Create a tokenizer object passing a list of (regexp_pattern,
        token_type) tuples.

        token_type is passed back from the tokenize generator to
        indicate the token type found, and regexp_pattern is the regular
        expression string used to match that token type.

        The regexp patterns may not contain any capturing groups (there
        would be no point in using them as the match object is never
        made available anywhere).

        There must be at least one token definition.

        If token_type is None, the matched string is passed as the token
        type - this is useful for operators.
        """

        assert len(token_defs) > 0, "No token definitions supplied"
        token_patterns = ["(%s)" % token_def[0] for token_def in token_defs]
        pattern = "(%s)(?:%s)?" % (Tokenizer.whitespace_pattern,
                                   "|".join(token_patterns))
        self.token_regexp = re.compile(pattern)
        assert self.token_regexp.groups == len(token_defs) + 1
        self.blank_line_regexp = re.compile("^%s$" % Tokenizer.whitespace_pattern)
        self.token_types = [token_def[1] for token_def in token_defs]

    def tokenize(self, text):
        """
        Takes an input string and returns a generator which yields a
        sequence of Token objects.
        """

        return self.tokenize_file(StringIO(text))

    def tokenize_file(self, file_object):
        """
        Takes an open file object and returns a generator which yields a
        sequence of Token objects.
        """

        filename = getattr(file_object, 'name', None)
        line_number = 0
        for line in file_object:
            line_number += 1

            if self.blank_line_regexp.match(line):
                continue

            pos = 0
            length = len(line)
            while pos < length:

                m = self.token_regexp.match(line, pos)
                assert m

                # skip whitespace and check for end
                pos += len(m.group(1))
                if pos == length:
                    break

                # check to see if we matched a token
                group = m.lastindex
                if group < 2:
                    dummy_token = Token(None, None, filename, line_number, pos)
                    raise ParseError(dummy_token, "Can't tokenize input")
                match = m.group(group)
                pos += len(match)
                token_type = self.token_types[group - 2]
                if token_type == None:
                    token_type = match
                yield Token(token_type, match, filename, line_number, pos)

        yield Token(Token.END_TOKEN, "", filename, line_number + 1, 0)

class ExprSpec:
    """
    Specifies the expressions that can be parsed.  It is used to
    determine what action to take when a token is encountered in the
    input stream.

    name -- optional, the name of the the context

    include -- optional, if specified then initialise the new object by
    by including all the actions defined by this one

    Initialised by the client by calling the add_* methods.
    """

    def __init__(self, name = "this", include = None):
        self.name = name
        if include:
            self.prefix_actions = dict(include.prefix_actions)
            self.infix_actions = dict(include.infix_actions)
        else:
            self.prefix_actions = {}
            self.infix_actions = {}

    ##################################################################
    # Internal implementation
    ##################################################################

    def prefix(self, parser, token):
        """
        Internal - called by the parser when a token is encountered in
        prefix position.  This either calls the appropriate handler, or
        raises an exception if no handler is registered for the token
        type.
        """
        token_type = token.type
        if token_type not in self.prefix_actions:
            raise ParseError(token, "Unexpected '%s' in %s context" % (str(token_type), self.name))
        handler = self.prefix_actions[token_type]
        return handler(parser, self, token)

    def get_bind_left(self, token):
        """
        Internal - called by the parser to get the left binding power
        for a token type.  Returns the binding power, or zero if the
        token type is not registered.
        """
        token_type = token.type
        if token_type not in self.infix_actions:
            return 0
        return self.infix_actions[token_type][0]

    def infix(self, parser, token, left_value):
        """
        Internal - called by the parser when a token is encountered in
        infix position.  This either calls the appropriate handler, or
        raises an exception if no handler is registered for the token
        type.
        """
        token_type = token.type
        if token_type not in self.infix_actions:
            raise ParseError(token, "Unexpected '%s' in %s context" % (str(token_type), self.name))
        handler_func = self.infix_actions[token_type][1]
        return handler_func(parser, self, token, left_value)

    ##################################################################
    # Low level initialisation methods for use by client
    ##################################################################

    def add_prefix_handler(self, token_type, handler_func):
        """
        Add a handler to be called when a specified token type is found
        in prefix position.

        token_type -- the token type to be handled

        handler_func -- a function called when the token is found, with
        the following arguments: parser, expression spec, token.
        """
        assert token_type not in self.prefix_actions
        self.prefix_actions[token_type] = handler_func

    def add_infix_handler(self, token_type, bind_left, handler_func):
        """
        Add a handler to be called when a specified token type is found
        in infix position.

        token_type -- the token type to be handled

        bind_left -- the left binding power of the token, must be a
        multiple of two

        handler_func -- a function called when the token is found,with
        the following arguments: parser, expression spec, token, value of the
        left hand side of the expression.
        """
        assert token_type not in self.infix_actions
        assert bind_left % 2 == 0
        self.infix_actions[token_type] = (bind_left, handler_func)

    ##################################################################
    # More convenient initialisation methods for use by client
    ##################################################################

    def add_word(self, token_type, handler_func):
        """
        Add a handler for tokens that represent words of the grammar,
        for example literal tokens or identifiers.

        token_type -- the token type to be handled

        handler_func -- a function which is called with token object,
        and that returns the literal value.
        """
        def word_handler(parser, expr_spec, token):
            return handler_func(token)
        self.add_prefix_handler(token_type, word_handler)

    def add_binary_op(self, token_type, bind_left, assoc, handler_func):
        """
        Add a handler for a binary operator.

        token_type -- the token type to be handled

        bind_left -- the left binding power of the token, must be a
        multiple of two

        assoc -- the associativity of the opeator, one of Assoc.LEFT or
        Assoc.RIGHT

        handler_func -- a function that returns the value of the whole
        expression.  It is called with the following arguments: token,
        value of left subexpression, value of right subexpression.
        """
        # calculate right binding power by addng left binding power and
        # associativity, hence why left binding power must be a multiple
        # of two
        bind_right = bind_left + assoc
        def binary_handler(parser, expr_spec, token, left_value):
            right_value = parser.expression(expr_spec, bind_right)
            return handler_func(token, left_value, right_value)
        self.add_infix_handler(token_type, bind_left, binary_handler)

    def add_unary_op(self, token_type, handler_func):
        """
        Add a handler for a unary prefix operator.

        token_type -- the token type to be handled

        handler_func -- a function that returns the value of the whole
        expression.  It is called with the following arguments: token,
        value of right subexpression.
        """
        def unary_handler(parser, expr_spec, token):
            right_value = parser.expression(expr_spec, 100)
            return handler_func(token, right_value)
        self.add_prefix_handler(token_type, unary_handler)

class Parser:
    """
    Top down operator precedence parser.
    """

    ##################################################################
    # Internal implementation
    ##################################################################

    def next_token(self):
        """Interal - consume a token from the input stream"""
        if self.at_end():
            raise ParseError(self.token, "Unexpected end of input")
        if self.token_stack:
            self.token = self.token_stack.pop(-1)
        else:
            self.token = next(self.token_generator)

    ##################################################################
    # Public interface
    ##################################################################

    def __init__(self, expr_spec, token_generator):
        """
        Create a parser object.

        expr_spec -- an ExprSpec used to determine what action to take
        when encountering each token.

        token_generator -- a generator yielding tokens, i.e. (token_type,
        token_content, token_line, token_column) tuples.
        """
        self.main_expr_spec = expr_spec
        self.token_generator = token_generator
        self.token_stack = []
        self.token = next(token_generator)

    def at_end(self):
        """
        Return whether the parser is at the end of the input stream
        """
        return self.token.type == Token.END_TOKEN

    def parse(self):
        """
        Parse and return a single expression from the token stream.
        """
        return self.expression(self.main_expr_spec)

    def parse_all(self):
        """
        Return a generator that parses the stream of tokens
        according to an expression spec and yields the results.  Multiple
        expressions are parsed until all tokens are consumed.
        """
        while not self.at_end():
            yield self.parse()

    ##################################################################
    # Token handler interface
    ##################################################################

    def not_followed_by(self, tok):
        """
        Call from token handlers to determine whether the next token is not of a specified type.

        tok -- the token type to test

        Return whether the next token is not of the specified type.
        """
        return self.token.type != tok

    def opt(self, tok):
        """
        Call from token handlers to optionally consume one token from the input stream.

        tok -- the token type to match

        Return the token content or None if it was not matched.
        """
        if self.not_followed_by(tok):
            return None
        result = self.token
        self.next_token()
        return result

    def opt2(self, tok1, tok2):
        """
        Call from token handlers to optionally consume two tokens from
        the input stream.

        tok1 -- the token type of the first token to match
        tok2 -- the token type of the second token to match

        Return a tuple of the content of the two tokens matched, or None
        if they were not matched.
        """
        if self.token.type != tok1:
            return None
        token1 = self.token
        self.next_token()
        if self.token.type != tok2:
            self.token_stack.append(self.token)
            self.token = token1
            return None
        token2 = self.token
        self.next_token()
        return (token1, token2)

    def match(self, tok):
        """
        Call from token handlers to consume a token from the input stream.

        tok -- the token type to match

        Returns the token conent or raises an exception if the token was not matched.
        """
        result = self.opt(tok)
        if not result:
            raise ParseError(self.token, 'Expected %s but found %s' % (str(tok), str(self.token.type)))
        return result

    def expression(self, expr_spec, bind_right = 0):
        """
        Call from token handlers to parse an expression from the input stream.

        expr_spec - the expression spec to use

        bind_right -- right binding power used to resolve operator precedence

        Returns the value of the expression.
        """
        t = self.token
        self.next_token()
        left = expr_spec.prefix(self, t)
        while bind_right < expr_spec.get_bind_left(self.token):
            t = self.token
            self.next_token()
            left = expr_spec.infix(self, t, left)
        return left
