#!/usr/bin/python

# Example parser that generates an AST for an expression

from varas import *
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

def handle_lparen(parser, content):
    expr = parser.expression()
    parser.match(")")
    return expr

def handle_lsquare(parser, content):
    result = []
    while not parser.opt("]"):
        if result:
            parser.match(",")
        result.append(parser.expression())
    return ("list", result)

def ident(x): 
    return x

actions = ActionMap()
actions.add_literal(LITERAL_TOKEN, int)
actions.add_unary_op("+", ident)
actions.add_unary_op("-", lambda x: ("neg", x))
actions.add_binary_op("+", 10, Assoc.LEFT, lambda l, r: ("add", l, r))
actions.add_binary_op("-", 10, Assoc.LEFT, lambda l, r: ("sub", l, r))
actions.add_binary_op("*", 20, Assoc.LEFT, lambda l, r: ("mul", l, r))
actions.add_binary_op("/", 20, Assoc.LEFT, lambda l, r: ("div", l, r))
actions.add_binary_op("^", 30, Assoc.RIGHT, lambda l, r: ("pow", l, r))
actions.add_prefix_handler("(", handle_lparen)
actions.add_prefix_handler("[", handle_lsquare)

import unittest

class TestExpr(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual([expected], 
                         list(Parser().parse(tokenize(input), actions)))

    def checkError(self, input):
        self.assertRaises(ParseException, lambda: Parser().parse(tokenize(input), actions))

    def test_(self):
        self.check(1, "1")
        self.check(1, "(1)")
        self.check(("add", 1, 2), "1+2")
        self.check(("add", 1, ("mul", 2, 3)), "1+2*3")
        self.check(("mul", 1, ("add", 2, 3)), "1*(2+3)")
        self.check(("list", [1, 2, 3]), "[1, 2, 3]")

if len(sys.argv) > 1 and sys.argv[1] == "-t":
    sys.argv.pop(1)
    unittest.main()
else:
    while True:
        try:
            program = raw_input("> ")
            print repr(Parser().parse(tokenize(program), actions).next())
        except EOFError:
            print("")
            exit(0)
