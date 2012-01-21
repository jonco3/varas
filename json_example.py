#!/usr/bin/python

# Example JSON parser from spec at http://www.json.org/fatfree.html
# JSON value is: string | number | object | array | true | false | null

from varas import *
import sys
import re

LITERAL_STRING_TOKEN = 1
LITERAL_NUMBER_TOKEN = 2

string_pattern = r"\"(?:[^\"\\]|(?:\\u[A-Fa-f0-9]{4})|(?:\\[\"\\/bfnrt]))*\""
number_pattern = r"-?(?:0|(?:[1-9]\d*))(?:\.\d*)?(?:eE[+-]?\d*)?"
operator_pattern = r"[{:,}\[\]]|true|false|null"

pattern = re.compile("\s*(?:(%s)|(%s)|(%s))" % 
                     (string_pattern, number_pattern, operator_pattern))

def tokenize(text):
    pos = 0
    length = len(text)
    while pos < length:
        m = pattern.match(text, pos)
        if not m:
            raise SyntaxError("Can't tokenize input %s at %d" % (text[pos], pos))
        pos += len(m.group(0))
        if m.group(1):
            yield LITERAL_STRING_TOKEN, m.group(1)
        elif m.group(2):
            yield LITERAL_NUMBER_TOKEN, m.group(2)
        else:
            yield m.group(3), m.group(3)        
    yield Parser.END_TOKEN, ""    

def handle_string(s):
    return s[1:-1] # todo unescape

def handle_number(s):
    if "." in s: 
        return float(s) 
    else: 
        return int(s)

def handle_object(parser, actions, content):
    result = {}
    while not parser.opt("}"):
        if len(result):
            print("handle_object %s\n" % repr(result))
            parser.match(",")
        key = handle_string(parser.match(LITERAL_STRING_TOKEN))
        parser.match(":")
        value = parser.expression(actions)
        result[key] = value
    return result

def handle_array(parser, actions, content):
    result = []
    while not parser.opt("]"):
        if result:
            parser.match(",")
        result.append(parser.expression(actions))
    return result

json = ActionMap()
json.add_literal(LITERAL_STRING_TOKEN, handle_string)
json.add_literal(LITERAL_NUMBER_TOKEN, handle_number) 
json.add_prefix_handler("{", handle_object)
json.add_prefix_handler("[", handle_array)
json.add_literal("true", lambda s: True)
json.add_literal("false", lambda s: False)
json.add_literal("null", lambda s: None)

import unittest

class TestJson(unittest.TestCase):

    def check(self, expected, input):
        self.assertEqual(expected, Parser().parse(tokenize(input), json))

    def checkError(self, input):
        self.assertRaises(Exception, lambda: Parser().parse(tokenize(input), json))

    def test_string(self):
        self.check("", '""')
        self.check("foo", '"foo"')
        #self.check("fo\"o", r'"fo\"o"') todo: unescape
        self.checkError('"foo')
        self.checkError('foo"')
        self.checkError('"fo"o"')

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
                "frame rate": 24
            }
        }'''

        expected = {
            "name": "Jack (\"Bee\") Nimble", 
            "format": {
                "type":       "rect", 
                "width":      1920, 
                "height":     1080, 
                "interlace":  False, 
                "frame rate": 24
                }
            }
        self.check(expected, source)


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


