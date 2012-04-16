#!/usr/bin/env python

import unittest
from test.calc_example import TestCalc
from test.expr_example import TestExpr
from test.json_example import TestJson

tests = [ TestCalc, 
          TestExpr, 
          TestJson ]

suites = [ unittest.TestLoader().loadTestsFromTestCase(test) 
           for test in tests ]

unittest.TextTestRunner(verbosity = 2).run(unittest.TestSuite(suites))
