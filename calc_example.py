#!/usr/bin/python

# Example parser that calculates the result of an expression

from varas import *
from operator import *
import sys
import re

LITERAL_TOKEN = 1

token_pat = re.compile("\s*(?:(\d+)|(.))")

def tokenize(program):

    for number, operator in token_pat.findall(program):
        if number:
            yield LITERAL_TOKEN, number
        else:
            yield operator, operator

    yield Parser.END_TOKEN, None

def handle_lparen(parser, actions, content):
    expr = parser.expression(actions)
    parser.match(")")
    return expr

def handle_lsquare(parser, actions, content):
    result = []
    while not parser.opt("]"):
        if result != []:
            parser.match(",")
        result.append(parser.expression(actions))
    return result

def ident(x): 
    return x

actions = ActionMap()
actions.add_literal(LITERAL_TOKEN, int)
actions.add_unary_op("+", ident)
actions.add_unary_op("-", neg)
actions.add_binary_op("+", 10, 10, add)
actions.add_binary_op("-", 10, 10, sub)
actions.add_binary_op("*", 20, 20, mul)
actions.add_binary_op("/", 20, 20, div)
actions.add_binary_op("^", 30, 29, pow)
actions.add_prefix_handler("(", handle_lparen)
actions.add_prefix_handler("[", handle_lsquare)

import unittest

class TestCalc(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual(expected, Parser().parse(tokenize(input), actions))

    def checkError(self, input):
        self.assertRaises(Exception, lambda: Parser().parse(tokenize(input), actions))

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
        self.checkError("1 * * 2")
        self.checkError("1 1")
        self.checkError("( 1")
        self.checkError(") 1")
        self.checkError("1 (")
        self.checkError("1 )")
        self.checkError("1 +")

if len(sys.argv) > 1 and sys.argv[1] == "-t":
    sys.argv.pop(1)
    unittest.main()
else:
    while True:
        try:
            program = raw_input("> ")
            print repr(Parser().parse(tokenize(program), actions))
        except EOFError:
            print("")
            exit(0)
