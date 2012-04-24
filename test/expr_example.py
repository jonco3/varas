# Example parser that generates an AST for an expression

from varas import *
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
    return ("list", result)

def parse_expr(input):
    return list(Parser(expr_spec, tokenizer.tokenize(input)).parse_all())

expr_spec = ExprSpec()
expr_spec.add_word(LITERAL_TOKEN, lambda t: int(t.content))
expr_spec.add_unary_op("+", lambda t, r: r)
expr_spec.add_unary_op("-", lambda t, r: ("neg", r))
expr_spec.add_binary_op("+", 10, Assoc.LEFT, lambda t, l, r: ("add", l, r))
expr_spec.add_binary_op("-", 10, Assoc.LEFT, lambda t, l, r: ("sub", l, r))
expr_spec.add_binary_op("*", 20, Assoc.LEFT, lambda t, l, r: ("mul", l, r))
expr_spec.add_binary_op("/", 20, Assoc.LEFT, lambda t, l, r: ("div", l, r))
expr_spec.add_binary_op("^", 30, Assoc.RIGHT, lambda t, l, r: ("pow", l, r))
expr_spec.add_prefix_handler("(", handle_lparen)
expr_spec.add_prefix_handler("[", handle_lsquare)

import unittest

class TestExpr(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual([expected], parse_expr(input))

    def checkError(self, input):
        self.assertRaises(ParseError, parse_expr, input)

    def test_(self):
        self.check(1, "1")
        self.check(1, "(1)")
        self.check(("add", 1, 2), "1+2")
        self.check(("add", 1, ("mul", 2, 3)), "1+2*3")
        self.check(("mul", 1, ("add", 2, 3)), "1*(2+3)")
        self.check(("list", [1, 2, 3]), "[1, 2, 3]")

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
