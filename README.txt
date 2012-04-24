Varas
=====

Varas is a python Pratt parser framework, which aims to be general
purpose and easy to use.

Pratt parsers (also known as top down operator precendence parsers) are
simple to use and resonably efficent.  There are a few articles
describing them on the web:

  http://javascript.crockford.com/tdop/tdop.html

  http://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing/

Installation
------------

The source is available for download from github here:

  https://github.com/JonCoppeard/varas/downloads

You can run the test code like this:

  python run_tests.py

And you can install it using python distutils in the normal way:

  $ python setup.py install

A simple example
----------------

As a simple example, we can build a calculator that computes numerical expressions.

First we create a tokenizer.  There will be two types of tokens - literal
numbers and mathematical operators.  Tokens are matched by regular expressions.

  >>> from varas import *
  >>> tok = Tokenizer( ("\d+", "NUMBER"),
  ...                  ("[-+*/^]", None) )

  >>> list(tok.tokenize("2 +"))
  [Token('NUMBER', '2'), Token('+', '+'), Token(Token.END_TOKEN, '')]

Next we set up an expression spec to tell the parser what to do when it
encounters tokens.

  >>> expr = ExprSpec()

To deal with number literals we add an action that just calls the int() function
on the content of the token:

  >>> expr.add_word("NUMBER", lambda token: int(token.content))

To parse an expression and calculate the answer, we need to plug the parser and
tokenizer together.  This is done by creating a Parser object which takes both
the expression spec and a token generator.  We can then call the parse() method
to actually parse the input:

  >>> def calc(text):
  ...   return Parser(expr, tok.tokenize(text)).parse()

We can check that this parses numbers:

  >>> calc("42")
  42

Operators for addition and subtraction can be added to the expression spec like
this:

  >>> expr.add_binary_op("+", 10, Assoc.LEFT,
  ...                    lambda token, left, right: left + right)
  >>> expr.add_binary_op("-", 10, Assoc.LEFT,
  ...                    lambda token, left, right: left - right)

This allows us to process simple expressions:

  >>> calc("2 + 2")
  4

The number '10' in the lines above indicates the precedence of the operator.  To
add multiplication and division operators, we need to set a higher
precendence value to ensure the correct result:

  >>> expr.add_binary_op("*", 20, Assoc.LEFT,
  ...                    lambda token, left, right: left * right)
  >>> expr.add_binary_op("/", 20, Assoc.LEFT,
  ...                    lambda token, left, right: left / right)

  >>> calc("1 + 2 * 3")
  7

A more detailed example can be found in the file test/calc_example.py.
