# Example JSON parser from spec at http://www.json.org/fatfree.html
# JSON value is: string | number | object | array | true | false | null

from varas import *
import sys
import re

STRING_TOKEN = 1
NUMBER_TOKEN = 2

tokenizer = Tokenizer(
    (r"\"(?:[^\"\\]|(?:\\u[A-Fa-f0-9]{4})|(?:\\[\"\\/bfnrt]))*\"", STRING_TOKEN),
    (r"-?(?:0|(?:[1-9]\d*))(?:\.\d*)?(?:eE[+-]?\d*)?",             NUMBER_TOKEN),
    (r"[{:,}\[\]]|true|false|null",                                None))

string_escapes = {
    '"':  '"',
    '\\': '\\',
    '/':  '/',
    'b':  '\b',
    'f':  '\f',
    'n':  '\n',
    'r':  '\r',
    't':  '\t' }

def handle_string(token):
    def unescape_backslash(match):
        s = match.group(1)
        if s[0] == 'u':
            return chr(int(s[1:]))
        else:
            return string_escapes[s]
        
    s = token.content[1:-1]
    return re.sub(r"\\((u....)|.)", unescape_backslash, s)

def handle_number(token):
    s = token.content
    if "." in s: 
        return float(s) 
    else: 
        return int(s)

def handle_object(parser, expr_spec, token):
    result = {}
    while not parser.opt("}"):
        if len(result):
            parser.match(",")
        key = handle_string(parser.match(STRING_TOKEN))
        parser.match(":")
        value = parser.expression(expr_spec)
        result[key] = value
    return result

def handle_array(parser, expr_spec, token):
    result = []
    while not parser.opt("]"):
        if result:
            parser.match(",")
        result.append(parser.expression(expr_spec))
    return result

json = ExprSpec()
json.add_word(STRING_TOKEN, handle_string)
json.add_word(NUMBER_TOKEN, handle_number) 
json.add_prefix_handler("{", handle_object)
json.add_prefix_handler("[", handle_array)
json.add_word("true", lambda t: True)
json.add_word("false", lambda t: False)
json.add_word("null", lambda t: None)

def parse_expr(input):
    return list(Parser(tokenizer.tokenize(input)).parse(json))

import unittest

class TestJson(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual([expected], parse_expr(input))

    def checkError(self, input):
        self.assertRaises(ParseError, parse_expr, input)

    def test_string(self):
        self.check("", '""')
        self.check("foo", '"foo"')
        self.check("\"", r'"\""')
        self.check("\\", r'"\\"')
        self.check("/", r'"\/"')  # todo: check JSON escaped quote
        self.check("\b\f\n\r\t", '"\\b\\f\\n\\r\\t"')

    def test_number(self):
        self.check(1, "1")
        self.check(1.0, "1.0")

    def test_object(self):
        source = r'''
        {
            "name": "Jack (\"Bee\") Nimble", 
            "format": {
                "type":       "rect", 
                "width":      1920, 
                "height":     1080, 
                "interlace":  false, 
                "frame rate": 24,
                "floating":   2.5
            }
        }'''

        expected = {
            "name": "Jack (\"Bee\") Nimble", 
            "format": {
                "type":       "rect", 
                "width":      1920, 
                "height":     1080, 
                "interlace":  False, 
                "frame rate": 24,
                "floating":   2.5
                }
            }
        self.check(expected, source)

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


