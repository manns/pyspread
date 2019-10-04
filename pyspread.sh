#!/bin/bash

# Calls pyspread from top level folder of extracted tarball
export PYTHONPATH=$PYTHONPATH:.
python3 ./src/pyspread.py $@
