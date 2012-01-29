#!/bin/bash

export PYTHONPATH=src
python test/calc_example.py -t
python test/expr_example.py -t
python test/json_example.py -t
