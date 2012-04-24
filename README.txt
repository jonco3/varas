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

Next we set up an expression spec - this tells the parser what to do when it
encounters tokens.

  >>> expr = ExprSpec()

To deal with number literals we add an action that just calls the int() function
on the content of the token

  >>> expr.add_word("NUMBER", lambda token: int(token.content))

To parse some input, we need to plug the parser and tokenizer together.  The
tokenizer is used to create a generator which is passed to the Parser
constructor along with the expression spec:

  >>> def parse(text):
  ...   return Parser(expr, tok.tokenize(text)).parse()

Now we can check that this parses numbers:

  >>> parse("42")
  42


  1>>> expr_spec.add_binary_op("+", 10, Assoc.LEFT,
  1...                         lambda token, left, right: left + right)
  1>>> expr_spec.add_binary_op("-", 10, Assoc.LEFT,
  1...                         lambda token, left, right: left - right)
