# Example parser that calculates the result of an expression

from varas import *
from operator import *
import sys
import re

LITERAL_TOKEN = 1

tokenizer = Tokenizer(("\d+", LITERAL_TOKEN),
                      (".",   None))

def handle_lparen(parser, actions, token):
    expr = parser.expression(actions)
    parser.match(")")
    return expr

def handle_lsquare(parser, actions, token):
    result = []
    while not parser.opt("]"):
        if result:
            parser.match(",")
        result.append(parser.expression(actions))
    return result

expr_spec = ExprSpec()
expr_spec.add_word(LITERAL_TOKEN, lambda token: int(token.content))
expr_spec.add_unary_op("+", lambda token, right: right)
expr_spec.add_unary_op("-", lambda token, right: -right)
expr_spec.add_binary_op("+", 10, Assoc.LEFT, lambda t, l, r: l + r)
expr_spec.add_binary_op("-", 10, Assoc.LEFT, lambda t, l, r: l - r)
expr_spec.add_binary_op("*", 20, Assoc.LEFT, lambda t, l, r: l * r)
expr_spec.add_binary_op("/", 20, Assoc.LEFT, lambda t, l, r: l / r)
expr_spec.add_binary_op("^", 30, Assoc.RIGHT, lambda t, l, r: l ** r)
expr_spec.add_prefix_handler("(", handle_lparen)
expr_spec.add_prefix_handler("[", handle_lsquare)

def parse_expr(input):
    return list(Parser(tokenizer.tokenize(input)).parse(expr_spec))

import unittest

class TestCalc(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual([expected], parse_expr(input))

    def checkError(self, input):
        self.assertRaises(ParseError, parse_expr, input)

    def test_number(self):
        self.check(1, "1")
        self.check(2, " 2")
        self.check(123, "123")
        self.check(-234, "-234")
        self.check(-456, " - 456")
        self.check(456, "+456")

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
        self.checkError("( 1")
        self.checkError(") 1")
        self.checkError("1 (")
        self.checkError("1 )")
        self.checkError("1 +")

    def checkCount(self, expected, input):
        p = Parser(tokenizer.tokenize(input))
        for i in range(expected):
            self.assertFalse(p.at_end())
            e = p.expression(expr_spec)
        self.assertTrue(p.at_end())

    def test_multiple(self):
        self.checkCount(1, "1")
        self.checkCount(2, "1 2 * 3")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "-t":
        sys.argv.pop(1)
        unittest.main()
    else:
        while True:
            try:
                program = raw_input("> ")
                for result in parse_expr(program):
                    print(repr(result))
            except EOFError:
                print("")
                exit(0)
