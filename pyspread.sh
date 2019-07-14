#!/bin/bash

#export PYTHONPATH=$PYTHONPATH:/home/mn/prog/Phoenix

# Calls pyspread from top level folder of extracted tarball
export PYTHONPATH=$PYTHONPATH:.
python3 ./src/pyspread.py $@
