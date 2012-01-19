#!/usr/bin/python

# Top down operator precedence parser library
#
# Based on:
#   http://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing/
# Which is itself based on: 
#   http://javascript.crockford.com/tdop/tdop.html

import sys

class Parser:
    token, content = None, None
    _tokenizer = None

    def _next_token(self):
        self.token, self.content = self._tokenizer()

    def match(self, tok = None):
        if tok and tok != type(self.token):
            raise SyntaxError('Expected %s' % tok)
        self._next_token()

    def opt(self, tok):
        if tok == type(self.token):
            self._next_token()
            return True
        else:
            return False

    def parse(self, tokenize, program):
        self._tokenizer = tokenize(program).next
        self._next_token()
        result = self.expression()
        if type(self.token) != EndToken:
            raise SyntaxError("Trailing input")
        return result

    def expression(self, bind_right = 0):
        t, c = self.token, self.content
        self._next_token()
        left = t.prefix(self, c)
        while bind_right < self.token.bind_left:
            t, c = self.token, self.content
            self._next_token()
            left = t.infix(self, left, c)
        return left

class Token(object):
    bind_left = 0
    def prefix(self, parser, content):
        raise Exception("Bad prefix")
    def infix(self, parser, left, content):
        raise Exception("Bad infix")

class EndToken(Token):
    pass
