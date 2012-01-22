#!/usr/bin/python

"""
Top-down operator precendence parser library.

This is based on code from:
http://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing/

Concepts:

 - token type: an object representing the type of the token.
   Paser.END_TOKEN is a special token type representing the end of the
   input stream.

 - token content: the text content of the token.  Passed to prefix
   handlers so they can parse literal tokens.

 - action map: used to map token types to handler functions called when
   the token is encountered.
"""

class Assoc:
    """
    Defines constants for left/right associative binary oprators, used
    by ActionMap.add_binary_op().

    The values are added to double the operator precedence value to
    obtain the final right binding power - do not change the values.
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

    def prefix(self, parser, token_type, token_content):
        """
        Internal - called by the parser when a token is encountered in
        prefix position.  This either calls the appropriate handler, or
        raises an exception if no handler is registered for the token
        type.
        """
        if token_type not in self.prefix_actions:
            raise Exception("%s not allowed as prefix in this context" % token_type)
        handler = self.prefix_actions[token_type]
        return handler(parser, self, token_content)

    def get_bind_left(self, token_type):
        """
        Internal - called by the parser to get the left binding power
        for a token type.  Returns the binding power, or zero if the
        token type is not registered.
        """
        if token_type not in self.infix_actions:
            return 0
        return self.infix_actions[token_type][0]

    def infix(self, parser, token_type, token_content, left_value):
        """
        Internal - called by the parser when a token is encountered in
        infix position.  This either calls the appropriate handler, or
        raises an exception if no handler is registered for the token
        type.
        """
        if token_type not in self.infix_actions:
            raise Exception("%s not defined as infix in this context" % token_type)
        handler_func = self.infix_actions[token_type][1]
        return handler_func(parser, self, left_value)

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
        if token_type in self.prefix_actions:
            raise Exception("Prefix operator already registered for %s" % token_type)
        self.prefix_actions[token_type] = handler_func

    def add_infix_handler(self, token_type, bind_left, handler_func):
        """
        Add a handler to be called when a specified token type is found
        in infix position.

        token_type -- the token type to be handled

        bind_left -- the left binding power of the token

        handler_func -- a function called when the token is found,with
        the following arguments: parser, action map, value of the left
        hand side of the expression.

        Note bind_left is doubled by this method before it is stored.
        """
        if token_type in self.infix_actions:
            raise Exception("Infix operator already registered for %s" % token_type)
        self.infix_actions[token_type] = (bind_left * 2, handler_func)

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
        self.add_prefix_handler(token_type, lambda p, a, c: handler_func(c))

    def add_binary_op(self, token_type, bind_left, assoc, handler_func):
        """
        Add a handler for a binary operator.

        token_type -- the token type to be handled

        handler_func -- a function that is called with the values of the
        left and right subexpressions that returns the value of the
        whole expression.
        """
        # calculate right binding power from left and associativity
        # bind_left is doubled by add_infix_handler()
        bind_right = bind_left * 2 + assoc
        def binary_handler(parser, actions, left_value):
            right_value = parser.expression(self, bind_right)
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
        def unary_handler(parser, actions, token_content):
            right_value = parser.expression(self, 100)
            return handler_func(right_value)
        self.add_prefix_handler(token_type, unary_handler)

class Parser():
    """
    Top down operator precedence parser.
    """
    
    ##################################################################
    # Internal implementation
    ##################################################################

    token, content = None, None
    token_generator = None

    def next_token(self):
        """Interal - consume a token from the input stream"""
        self.token, self.content = self.token_generator.next()

    ##################################################################
    # Public interface
    ##################################################################

    """Token type representing the end of the token stream"""
    END_TOKEN = -1

    # tokenize generates 
    def parse(self, token_generator, actions):
        """
        Main interface. Parse a stream of tokens according to a set of
        actions and return the result.  An exception is raised if not
        all tokens are consumed.

        token_generator -- a generator yielding (token_type,
        token_content) tuples.

        actions -- an ActionMap used to determine what action to take
        when encountering each token.
        """
        self.token_generator = token_generator
        self.next_token()
        result = self.expression(actions)
        if self.token != Parser.END_TOKEN:
            raise SyntaxError("Trailing input")
        return result

    ##################################################################
    # Token handler interface
    ##################################################################

    def opt(self, tok):
        """
        Call from token handlers to optionally consume one token from the input stream.

        tok -- the token type to match

        Return the token content or None if it was not matched.
        """
        if self.token != tok:
            return None
        result = self.content
        self.next_token()
        return result

    def match(self, tok):
        """
        Call from token handlers to consume a token from the input stream.

        tok -- the token type to match

        Returns the token conent or raises an exception if the token was not matched.
        """
        result = self.opt(tok)
        if not result:
            raise SyntaxError('Expected %s' % tok)
        return result

    def expression(self, actions, bind_right = 0):
        """
        Call from token handlers to parse an expression from the input stream.

        actions -- action map to use

        bind_right -- right binding power used to resolve operator precedence

        Returns the value of the expression.
        """
        t, c = self.token, self.content
        self.next_token()
        left = actions.prefix(self, t, c)
        while bind_right < actions.get_bind_left(self.token):
            t, c = self.token, self.content
            self.next_token()
            left = actions.infix(self, t, c, left)
        return left
