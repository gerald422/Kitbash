#!/bin/bash
# full regression on the current add-on: fresh test library, then every suite
cd /home/claude/kits
python3 make_kitlib.py /home/claude/kits/amv2_partial.json > /dev/null && python3 vet/make_vetlib.py > /dev/null && python3 iv2/make_iv2lib.py > /dev/null \
  && python3 cj/make_cjlib.py > /dev/null && python3 or/make_orlib.py > /dev/null && python3 tm/make_tmlib.py > /dev/null || { echo "LIB FAILED"; exit 1; }
PY=/home/claude/bpyenv/bin/python
for t in v17/t_marine.py v17/t_full.py v18/t_wrist.py v19/t_vet.py v110/t_iv2.py v110/t_iv2_pairs.py v111/t_cj.py v111/t_or.py v111/t_tm.py v111/t_cross.py; do
  d=/home/claude/test/$(dirname $t); n=$(basename $t .py)
  (cd $d && timeout 6000 $PY $n.py > /home/claude/test/v111/reg_$n.log 2>&1)
  echo "$t: $(grep -c '^  ok' /home/claude/test/v111/reg_$n.log) ok, $(grep '^FAILS' /home/claude/test/v111/reg_$n.log | tail -1)"
done
echo ALL-DONE
