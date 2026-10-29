#!/bin/bash
# full regression on 1.14: the 1.13 suites, Josh's sequence, then BBoosty + CyberBrush (t_nc needs merge_all.py run first)
bash /home/claude/test/v113/run_all.sh | grep -v ALL-DONE
PY=/home/claude/bpyenv/bin/python
for t in t_josh t_nc; do (cd /home/claude/test/v114 && timeout 3000 $PY $t.py > /home/claude/test/v114/reg_$t.log 2>&1); echo "v114/$t: $(grep -c "^  ok" /home/claude/test/v114/reg_$t.log) ok, $(grep "^FAILS" /home/claude/test/v114/reg_$t.log | tail -1)"; done
echo ALL-DONE
