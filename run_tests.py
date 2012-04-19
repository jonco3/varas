#!/usr/bin/env python

import unittest
import doctest
import os
import os.path
import glob

from test.calc_example import TestCalc
from test.expr_example import TestExpr
from test.json_example import TestJson

tests = [ TestCalc,
          TestExpr,
          TestJson ]

doc_dirs = [ "",
             "doc/" ]

def convert_to_unix_line_endings(source):
    assert os.path.isfile(source)  # ensures we're in the correct directory
    if not os.path.isdir("tmp"):
        os.mkdir("tmp")

    dest = "tmp/" + os.path.basename(source)
    source_file = open(source, "U")
    dest_file = open(dest, "w")
    dest_file.writelines(source_file)
    dest_file.close()
    source_file.close()
    return dest

doc_files = []
for doc_dir in doc_dirs:
    doc_files.extend(glob.glob(doc_dir + "*.txt"))
tmp_doc_files = [convert_to_unix_line_endings(file) for file in doc_files]

suites = [ unittest.TestLoader().loadTestsFromTestCase(test) for test in tests ] + \
    [ doctest.DocFileTest(file, module_relative = False) for file in tmp_doc_files ]

unittest.TextTestRunner(verbosity = 2).run(unittest.TestSuite(suites))

for file in tmp_doc_files:
    os.remove(file)
