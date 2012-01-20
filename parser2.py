#!/usr/bin/python

class Parser():

    END_TOKEN = -1

    token, content = None, None
    token_generator = None

    def _next_token(self):
        self.token, self.content = self.token_generator.next()

    def opt(self, tok):
        if self.token != tok:
            return False
        self._next_token()
        return True

    def match(self, tok):
        if not self.opt(tok):
            raise SyntaxError('Expected %s' % tok)

    # tokenize generates (token_type, token_content) tuples
    def parse(self, token_generator, actions):
        self.token_generator = token_generator
        self._next_token()
        result = self.expression(actions)
        if self.token != Parser.END_TOKEN:
            raise SyntaxError("Trailing input")
        return result

    def expression(self, actions, bind_right = 0):
        t, c = self.token, self.content
        self._next_token()
        left = actions.prefix(self, t, c)
        while bind_right < actions.get_bind_left(self.token):
            t, c = self.token, self.content
            self._next_token()
            left = actions.infix(self, t, c, left)
        return left
        
class ActionMap:

    def __init__(self):
        self.prefix_actions = {}
        self.infix_actions = {}

    # for use by Parser

    def prefix(self, parser, token_type, token_content):
        if token_type not in self.prefix_actions:
            raise Exception("%s not allowed as prefix in this context" % token_type)
        handler = self.prefix_actions[token_type]
        return handler(parser, self, token_content)

    def get_bind_left(self, token_type):
        if token_type not in self.infix_actions:
            return 0
        return self.infix_actions[token_type][0]

    def infix(self, parser, token_type, token_content, left_value):
        if token_type not in self.infix_actions:
            raise Exception("%s not defined as infix in this context" % token_type)
        handler_func = self.infix_actions[token_type][1]
        return handler_func(parser, self, left_value)

    # low level initialisation methods for use by client

    def add_prefix_handler(self, token_type, handler_func):
        if token_type in self.prefix_actions:
            raise Exception("Prefix operator already registered for %s" % token_type)
        self.prefix_actions[token_type] = handler_func

    def add_infix_handler(self, token_type, bind_left, handler_func):
        if token_type in self.infix_actions:
            raise Exception("Infix operator already registered for %s" % token_type)
        self.infix_actions[token_type] = (bind_left, handler_func)

    # more convenient initialisation methods for use by client

    def add_literal(self, token_type, handler_func):
        self.add_prefix_handler(token_type, lambda p, a, c: handler_func(c))

    def add_binary_op(self, token_type, bind_left, bind_right, handler_func):
        def binary_handler(parser, actions, left_value):
            right_value = parser.expression(self, bind_right)
            return handler_func(left_value, right_value)
        self.add_infix_handler(token_type, bind_left, binary_handler)
    
    def add_unary_op(self, token_type, handler_func):
        def unary_handler(parser, actions, token_content):
            right_value = parser.expression(self, 100)
            return handler_func(right_value)
        self.add_prefix_handler(token_type, unary_handler)
