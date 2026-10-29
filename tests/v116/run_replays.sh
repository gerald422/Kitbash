#!/bin/bash
cd /home/claude/test/v116
PY=/home/claude/bpyenv/bin/python
for t in v19/t_vet v110/t_iv2 v111/t_or v111/t_cross v17/t_marine; do
  n=$(basename $t)
  timeout 4000 $PY replay.py /home/claude/test/$t.py /home/claude/test/v116/rep_ref rep_${n}_ref.json > rep_${n}_ref.log 2>&1
  timeout 4000 $PY replay.py /home/claude/test/$t.py /home/claude/test/v116/rep_ren rep_${n}_ren.json rep_ren_log.csv > rep_${n}_ren.log 2>&1
  echo "$t: $(python3 cmp_logs.py rep_${n}_ref.json rep_${n}_ren.json | tail -1)"
  python3 cmp_logs.py rep_${n}_ref.json rep_${n}_ren.json | grep DIFF | head -5
done
echo REPLAYS-DONE
