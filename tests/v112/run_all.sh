#!/bin/bash
# full regression on the current add-on: fresh test library, then every suite
cd /home/claude/kits
python3 make_kitlib.py /home/claude/kits/amv2_partial.json > /dev/null && python3 vet/make_vetlib.py > /dev/null && python3 iv2/make_iv2lib.py > /dev/null \
  && python3 cj/make_cjlib.py > /dev/null && python3 or/make_orlib.py > /dev/null && python3 tm/make_tmlib.py > /dev/null || { echo "LIB FAILED"; exit 1; }
PY=/home/claude/bpyenv/bin/python
for t in v17/t_marine.py v17/t_full.py v18/t_wrist.py v19/t_vet.py v110/t_iv2.py v110/t_iv2_pairs.py v111/t_cj.py v111/t_or.py v111/t_tm.py v111/t_cross.py; do
  d=/home/claude/test/$(dirname $t); n=$(basename $t .py)
  (cd $d && timeout 6000 $PY $n.py > /home/claude/test/v112/reg_$n.log 2>&1)
  echo "$t: $(grep -c '^  ok' /home/claude/test/v112/reg_$n.log) ok, $(grep '^FAILS' /home/claude/test/v112/reg_$n.log | tail -1)"
done

python3 /home/claude/kits/cr/make_crlib.py > /dev/null; for m in dev_bt/sc_bt dev_bt/sc_terr stage_top stage_oneoff stage_marta; do python3 /mnt/user-data/outputs/deliver111/merge_sidecars.py /home/claude/kits/out112/$m /home/claude/test/kitlib > /dev/null; done; (cd /home/claude/test/v112 && timeout 3000 $PY t_flat.py > /home/claude/test/v112/reg_t_flat.log 2>&1); echo "v112/t_flat: $(grep -c "^  ok" /home/claude/test/v112/reg_t_flat.log) ok, $(grep "^FAILS" /home/claude/test/v112/reg_t_flat.log | tail -1)"
(cd /home/claude/test/v112 && timeout 3000 $PY t_tn2.py > /home/claude/test/v112/reg_t_tn2.log 2>&1); echo "v112/t_tn2: $(grep -c "^  ok" /home/claude/test/v112/reg_t_tn2.log) ok, $(grep "^FAILS" /home/claude/test/v112/reg_t_tn2.log | tail -1)"
for t in t_oneoff t_marta; do (cd /home/claude/test/v112 && timeout 3000 $PY $t.py > /home/claude/test/v112/reg_$t.log 2>&1); echo "v112/$t: $(grep -c "^  ok" /home/claude/test/v112/reg_$t.log) ok, $(grep "^FAILS" /home/claude/test/v112/reg_$t.log | tail -1)"; done
echo ALL-DONE
