#!/bin/bash
# two copies of the test library: reflib as it is, varlib with mirror copies folded in
set -e
cd /home/claude/test/v116
rm -rf reflib varlib holding fold_log.csv
cp -a /home/claude/test/kitlib reflib
cp -a /home/claude/test/kitlib varlib
python3 /home/claude/fold/fold_twins.py varlib pairs.json holding fold_log.csv
