#!/bin/bash
# full regression on 1.13: the 1.12 suites (fresh test library), then Springles
bash /home/claude/test/v112/run_all.sh | grep -v ALL-DONE
python3 /home/claude/kits/spr/make_sprlib.py > /dev/null
PY=/home/claude/bpyenv/bin/python
(cd /home/claude/test/v113 && timeout 3000 $PY t_spr.py > /home/claude/test/v113/reg_t_spr.log 2>&1); echo "v113/t_spr: $(grep -c "^  ok" /home/claude/test/v113/reg_t_spr.log) ok, $(grep "^FAILS" /home/claude/test/v113/reg_t_spr.log | tail -1)"
echo ALL-DONE
