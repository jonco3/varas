#!/usr/bin/python

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

 - action map: used to map token types to handler functions called when
   the token is encountered.
"""

class Assoc:
    """
    Defines constants for left/right associative binary oprators, used
    by ActionMap.add_binary_op().

    The values are added to the operator precedence value to obtain the
    final right binding power - do not change the values.
    """
    LEFT = 0
    RIGHT = -1
        
class ActionMap:
    """
    Determines what action to take when a token is encountered in the
    input stream.  This determines the expressions that can be parsed.

    Initialised by the client by calling the add_* methods.
    """

    def __init__(self):
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
        token_type = token[0]
        if token_type not in self.prefix_actions:
            raise ParseException(token, "Bad prefix operator %s in this context" % repr(token_type))
        handler = self.prefix_actions[token_type]
        return handler(parser, self, token)

    def get_bind_left(self, token):
        """
        Internal - called by the parser to get the left binding power
        for a token type.  Returns the binding power, or zero if the
        token type is not registered.
        """
        token_type = token[0]
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
        token_type = token[0]
        if token_type not in self.infix_actions:
            raise ParseException(token, "Bad infix operator %s in this context" % repr(token_type))
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
        the following arguments: parser, action map, token content.
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
        the following arguments: parser, action map, token content,
        value of the left hand side of the expression.
        """
        assert token_type not in self.infix_actions
        assert bind_left % 2 == 0
        self.infix_actions[token_type] = (bind_left, handler_func)

    ##################################################################
    # More convenient initialisation methods for use by client
    ##################################################################

    def add_literal(self, token_type, handler_func):
        """
        Add a handler for literal tokens.

        token_type -- the token type to be handled

        handler_func -- a function to called with content of the token
        that returns the literal value.
        """
        def literal_handler(parser, actions, token):
            return handler_func(token[1])
        self.add_prefix_handler(token_type, literal_handler)

    def add_binary_op(self, token_type, bind_left, assoc, handler_func):
        """
        Add a handler for a binary operator.

        token_type -- the token type to be handled

        bind_left -- the left binding power of the token, must be a
        multiple of two

        assoc -- the associativity of the opeator, one of Assoc.LEFT or
        Assoc.RIGHT

        handler_func -- a function that is called with the values of the
        left and right subexpressions that returns the value of the
        whole expression.
        """
        # calculate right binding power by addng left binding power and
        # associativity, hence why left binding power must be a multiple
        # of two
        bind_right = bind_left + assoc
        def binary_handler(parser, actions, token, left_value):
            right_value = parser.expression(actions, bind_right)
            return handler_func(left_value, right_value)
        self.add_infix_handler(token_type, bind_left, binary_handler)
    
    def add_unary_op(self, token_type, handler_func):
        """
        Add a handler for a unary operator.

        token_type -- the token type to be handled

        handler_func -- a function that is called with the values of the
        right hand side of the expression that returns the value of the
        whole expression.
        """
        def unary_handler(parser, actions, token):
            right_value = parser.expression(actions, 100)
            return handler_func(right_value)
        self.add_prefix_handler(token_type, unary_handler)

class ParseException(Exception):
    def __init__(self, token, message):
        self.token = token
        self.message = message

    def __str__(self):
        return "%s at line %d column %d" % (self.message, self.token[2], self.token[3])

class Parser:
    """
    Top down operator precedence parser.
    """
    
    ##################################################################
    # Internal implementation
    ##################################################################

    token = None
    token_generator = None
    token_stack = []

    def next_token(self):
        """Interal - consume a token from the input stream"""
        try:
            if self.token_stack:
                self.token = self.token_stack.pop(-1)
            else:
                self.token = self.token_generator.next()
        except StopIteration:
            raise ParseException(None, "Unexpected end of input")

    ##################################################################
    # Public interface
    ##################################################################

    """Token type representing the end of the token stream"""
    END_TOKEN = -1

    def __init__(self, token_generator):
        """
        Create a parser object.

        token_generator -- a generator yielding tokens, i.e. (token_type,
        token_content, token_line, token_column) tuples.
        """
        self.token_generator = token_generator
        self.next_token()

    def at_end(self):
        """
        Return whether the parser is at the end of the input stream
        """
        return self.token[0] == Parser.END_TOKEN

    def parse(self, actions):
        """
        A generator that parse a stream of tokens
        according to a set of actions and yields the results.  Multiple
        expressions are parsed until all tokens are consumed.

        actions -- an ActionMap used to determine what action to take
        when encountering each token.
        """
        while not self.at_end():
            yield self.expression(actions)

    ##################################################################
    # Token handler interface
    ##################################################################

    def opt(self, tok):
        """
        Call from token handlers to optionally consume one token from the input stream.

        tok -- the token type to match

        Return the token content or None if it was not matched.
        """
        if self.token[0] != tok:
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
        if self.token[0] != tok1:
            return None
        token1 = self.token
        self.next_token()
        if self.token[0] != tok2:
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
            raise ParseException(self.token, 'Expected token %s but found %s' % (repr(tok), repr(self.token[0])))
        return result

    def expression(self, actions, bind_right = 0):
        """
        Call from token handlers to parse an expression from the input stream.

        actions - the action map to use

        bind_right -- right binding power used to resolve operator precedence

        Returns the value of the expression.
        """
        t = self.token
        self.next_token()
        left = actions.prefix(self, t)
        while bind_right < actions.get_bind_left(self.token):
            t = self.token
            self.next_token()
            left = actions.infix(self, t, left)
        return left
