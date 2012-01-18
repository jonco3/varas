#!/usr/bin/python

# Top down operator precedence parser from
# http://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing/

import re
import sys
import readline

token_pat = re.compile("\s*(?:(\d+)|(.))")

def tokenize(program):
    for number, operator in token_pat.findall(program):
        if number:
            yield literal_token(number)
        elif operator == "+":
            yield operator_add_token()
        elif operator == "-":
            yield operator_sub_token()
        elif operator == "*":
            yield operator_mul_token()
        elif operator == "/":
            yield operator_div_token()
        elif operator == "^":
            yield operator_pow_token()
        elif operator == '(':
            yield operator_lparen_token()
        elif operator == ')':
            yield operator_rparen_token()
        elif operator == '[':
            yield operator_lsquare_token()
        elif operator == ']':
            yield operator_rsquare_token()
        elif operator == ',':
            yield operator_comma_token()
        else:
            raise SyntaxError('unknown operator: %s', operator)
    yield end_token()

class parser:
    token, next = None, None

    def match(self, tok = None):
        if tok and tok != type(self.token):
            raise SyntaxError('Expected %s' % tok)
        self.token = self.next()

    def opt(self, tok):
        if tok == type(self.token):
            self.token = self.next()
            return True
        else:
            return False

    def parse(self, program):
        self.next = tokenize(program).next
        self.token = self.next()
        result = self.expression()
        if type(self.token) != end_token:
            raise SyntaxError("Trailing input")
        return result

    def expression(self, bind_right = 0):
        t = self.token
        self.token = self.next()
        left = t.prefix(self)
        while bind_right < self.token.bind_left:
            t = self.token
            self.token = self.next()
            left = t.infix(self, left)
        return left

#class parse_error(Exception):
#    BAD_PREFIX_OP = 1
#    BAD_INFIX_OP = 2
#    def __init__(self, code):
#        super(self).__init__("Parse error")
#        self.code = code

class token(object):
    bind_left = 0
    def prefix(self, parser):
        raise Exception("Bad prefix")
    def infix(self, parser, left):
        raise Exception("Bad infix")

class literal_token(token):
    def __init__(self, value):
        self.value = int(value)
    def prefix(self, parser):
        return self.value

class operator_add_token(token):
    bind_left = 10
    def prefix(self, parser):
        return parser.expression(100)
    def infix(self, parser, left):
        right = parser.expression(10)
        return left + right

class operator_sub_token(token):
    bind_left = 10
    def prefix(self, parser):
        return -parser.expression(100)
    def infix(self, parser, left):
        return left - parser.expression(10)

class operator_mul_token(token):
    bind_left = 20
    def infix(self, parser, left):
        return left * parser.expression(20)

class operator_div_token(token):
    bind_left = 20
    def infix(self, parser, left):
        return left / parser.expression(20)

class operator_pow_token(token):
    bind_left = 30
    def infix(self, parser, left):
        return left ** parser.expression(30 - 1)

class operator_lparen_token(token):
    def prefix(self, parser):
        expr = parser.expression()
        parser.match(operator_rparen_token)
        return expr

class operator_rparen_token(token):
    pass

class operator_lsquare_token(token):
    def prefix(self, parser):
        result = []
        while not parser.opt(operator_rsquare_token):
            if result != []:
                parser.match(operator_comma_token)
            result.append(parser.expression())
        return result

class operator_rsquare_token(token):
    pass

class operator_comma_token(token):
    pass

class end_token(token):
    pass

# while True:
#    program = raw_input("> ")
#    print repr(parser().parse(program))

import unittest

class TestBlah(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual(expected, parser().parse(input))

    def checkError(self, input):
        self.assertRaises(Exception, lambda: parser().parse(input))

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
