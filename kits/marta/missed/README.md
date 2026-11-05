# Marta parts the Nov 1 scan missed (Nov 5)

The Nov 2 one-handed run (`kits/marta/onehand/`) skipped some folders. Re-checked every Marta STL against
`_sources.csv` and the Nov 1 scan (presupported copies, duplicate downloads, bikes, armour bits, torsos and
two-armed sets left out): 43 single arms / held parts.

- `inscope2.json` -> `../onehand/job.py` (4 workers) -> `results2.jsonl` (30 arm, 10 held, 3 unknown) ->
  `../onehand/write_sidecars.py` beside the sources in `D:\new cults`.
- `rcheck.py`: each part through TIOW Inbox 1.17.7 on Mar Fil Assault Torso 1 (held parts in Arm 1A R's hand), check sheets.
- Left out after the sheets: Oct 2025 `heavy_arm_1-3` and d24 `R_arm_blood_effect` (forearm + hand pieces the hand
  rule took for held parts), `heavy_arms_5_with_eyes`, Jan 2026 `set_arms_2_with_katana`, Mar 2026
  `set_arms_4_with_chains` (two-armed sets); Relic Captain `set_arms_1.1/1.2/3.1` (no shoulder found).
- Hands holding skulls retyped Hands (the name rule said Melee).
- `keep.txt`: the 33 sources that went in (`library-tools`: survey_new -> plan_library --only Marta -> plan filtered
  to these -> build_library -> plan_names (kit names Mar 2026, Thicc Boi, Bionics) -> rename_library; thicc BOI filed
  under Terminator per Josh: heavy = Gravis, thicc = Terminator, phobois = Phobos).
