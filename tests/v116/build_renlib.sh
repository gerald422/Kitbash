#!/bin/bash
# renamed copies: renref (reflib renamed), renvar (varlib renamed); run after build_varlib.sh
set -e
cd /home/claude/test/v116
rm -rf renref renvar
cp -a reflib renref; cp -a varlib renvar
python3 make_index.py reflib > /dev/null       # index with every file (variants' titles come from it)
cp reflib/_sources.csv renref/_sources.csv
python3 make_index.py renvar > /dev/null
python3 /home/claude/fold/plan_names.py reflib/_sources.csv names_ref.csv
python3 /home/claude/fold/rename_library.py renref names_ref.csv ren_ref_log.csv
python3 /home/claude/fold/rename_library.py renvar names_ref.csv ren_var_log.csv
