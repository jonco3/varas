#!/usr/bin/python

# Top down operator precedence parser from:
#   http://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing/
# itself based on: 
#   http://javascript.crockford.com/tdop/tdop.html

import re
import sys

################################################################################
# Library code
################################################################################

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

    def parse(self, program):
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

################################################################################
# Example parser
################################################################################

token_pat = re.compile("\s*(?:(\d+)|(.))")

def tokenize(program):
    literal = LiteralToken()
    operators = {
        "+": OperatorAddToken(),
        "-": OperatorSubToken(),
        "*": OperatorMulToken(),
        "/": OperatorDivToken(),
        "^": OperatorPowToken(),
        "(": OperatorLParenToken(),
        ")": OperatorRParenToken(),
        "[": OperatorLSquareToken(),
        "]": OperatorRSquareToken(),
        ",": OperatorCommaToken()
        }

    for number, operator in token_pat.findall(program):
        if number:
            yield literal, number
        elif operator in operators:
            yield operators[operator], operator
        else:
            raise SyntaxError('unknown operator: %s', operator)

    yield EndToken(), None

class LiteralToken():
    def prefix(self, parser, content):
        return int(content)

class OperatorAddToken(Token):
    bind_left = 10
    def prefix(self, parser, content):
        return parser.expression(100)
    def infix(self, parser, left, content):
        right = parser.expression(10)
        return left + right

class OperatorSubToken(Token):
    bind_left = 10
    def prefix(self, parser, content):
        return -parser.expression(100)
    def infix(self, parser, left, content):
        return left - parser.expression(10)

class OperatorMulToken(Token):
    bind_left = 20
    def infix(self, parser, left, content):
        return left * parser.expression(20)

class OperatorDivToken(Token):
    bind_left = 20
    def infix(self, parser, left, content):
        return left / parser.expression(20)

class OperatorPowToken(Token):
    bind_left = 30
    def infix(self, parser, left, content):
        return left ** parser.expression(30 - 1)

class OperatorLParenToken(Token):
    def prefix(self, parser, content):
        expr = parser.expression()
        parser.match(OperatorRParenToken)
        return expr

class OperatorRParenToken(Token):
    pass

class OperatorLSquareToken(Token):
    def prefix(self, parser, content):
        result = []
        while not parser.opt(OperatorRSquareToken):
            if result != []:
                parser.match(OperatorCommaToken)
            result.append(parser.expression())
        return result

class OperatorRSquareToken(Token):
    pass

class OperatorCommaToken(Token):
    pass

# while True:
#    program = raw_input("> ")
#    print repr(parser().parse(program))

import unittest

class TestBlah(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual(expected, Parser().parse(input))

    def checkError(self, input):
        self.assertRaises(Exception, lambda: Parser().parse(input))

    def test_number(self):
        self.check(1, "1")
        self.check(2, " 2")
        self.check(123, "123")
        self.check(-234, "-234")
        self.check(-456, " - 456")

    def test_exprs(self):
        self.check(14, " 2 + 3 * 4")
        self.check(1, " (1)")
        self.check(20, " (2 + 3) * 4")
        self.check(16, " (2 + (3 - 1)) * 4")
        self.check(1, " 15 / 3 - 4")
        self.check(8, " 2 ^ 3")
        self.check(2, " 2 ^ 1 ^ 2")

    def test_list(self):
        self.check([], "[]")
        self.check([1], "[1]")
        self.check([1,2,3], "[1, 2, 3]")
        self.check([2,2,[4,5,6]], "[1 + 1, 2 * 3 - 4, [4, 5, (6)]]")
        self.checkError("[")
        self.checkError("]")
        self.checkError(",")
        self.checkError("[1")
        self.checkError("[1,")
        self.checkError("1]")
        self.checkError(",1]")
        self.checkError(",1")
        self.checkError("1,")
        self.checkError("1,1")

    def test_error(self):
        self.checkError(" ^ 3")
        self.checkError("2 ^")
        self.checkError("1 * * 2")
        self.checkError("1 * * 2")
        self.checkError("1 1")
        self.checkError("( 1")
        self.checkError(") 1")
        self.checkError("1 (")
        self.checkError("1 )")
        self.checkError("1 +")

unittest.main()
