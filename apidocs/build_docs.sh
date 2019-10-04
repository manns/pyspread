#!/bin/bash

echo $BASH_SOURCE

HERE_DIR=`dirname "$BASH_SOURCE"`
ROOT_DIR=`realpath $HERE_DIR/..`
echo $ROOT_DIR

sphinx-build -a -b html $ROOT_DIR/apidocs $ROOT_DIR/public/