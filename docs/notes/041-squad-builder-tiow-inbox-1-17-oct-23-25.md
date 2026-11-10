**Squad Builder + TIOW Inbox 1.17 (Oct 23–25).** Josh: TIOW's navigation is what makes it clunky. He wants:
- guided selection (torso, then legs, arms…);
- a whole squad sent in one go ("5 torsos etc");
- outlines rather than thumbnails, and ghost outlines of parts in the builder.

"Happy for this to be separate". It was built while his computer was out of reach; delivery and a run on the real library wait for it.

**The page** (`Squad Builder.html`, one offline file, three.js r147 inlined):
- **Steps:** Torso, Legs, Arms R/L, Head, Back, Shoulder pads R/L, Weapons R/L, Shin pads R/L, Base.
- **Filtering:** each step lists only parts that fit what's already picked, i.e. the model has a socket for them.
- **Cards** are outline drawings (edges over a dark fill). Hovering a card shows the part in place, as a blue outline, on every model.
- **Placement:** picks are drawn where Blender will put them, using the inbox's maths:
  - socket × gap × fit;
  - mirrored lefts and maker's left copies;
  - the adaptor for flat legs on a Mar Fil torso (adaptor number is a setting, default 3);
  - stood on the base.
- **Squads:** 1–10 models side by side, 80 mm apart. "Same part for every model" is the default; untick it to pick for one model at a time.
- **Files:** reads the library through the browser's folder access (Chrome/Edge; handles remembered, one click reconnects). Send writes one request JSON per part into TIOW's inbox.

**The index:** `_builder\index.json` plus one ~6,000-triangle preview mesh per part (`KBP1` binary). Made by `Prepare Squad Builder.bat`, which runs `prepare_builder.py` in Blender in the background:
- It first works out the anchors some parts only get on their first import: wrist sockets, Pad anchors, Shin anchors and hand fits. It saves them in the sidecars, so the page shows those parts exactly where Blender puts them.
- It resumes from `_builder\anchors_done.txt`. After the first run it only does new or changed parts.

**Inbox 1.17** adds three request fields:
- `model`: the squad model's id. A part with a `model` goes on that model, whatever is selected in Blender.
- `socket`: the socket type to land on.
- `at`: [x, y, z] mm for a model's first part (the torso). That part becomes the model's root (`tiow_model_root`) and is placed at `at`.

**Tests:**
- `builder/test/drive.js` (Playwright) builds a 3-model squad through the page's own cards.
- `t_squad.py` sends those requests through 1.17 in Blender and checks every part against where the page drew it. 48 checks, all within 0.05 mm / 0.1°, covering maker's left copies, mirrored pads and shins, the adaptor path and the base stand.
- Anchor pass over the demo library: 677 parts, 0 failures.
- Regression on 1.17: 15 suites, 1,135 checks (t_marine 47, t_full 50, t_wrist 21, t_vet 79, t_iv2 111, t_iv2_pairs 67, t_cj 131, t_or 218, t_tm 108, t_cross 146, t_flat 31, t_tn2 26, t_oneoff 60, t_marta 8, t_variants 32), no failures.

**Online demo:** an artifact named "Squad Builder".
- It holds a 524-part sample: MarFil Assault, Veteran, Jump Chaplain and Helmets; TN Mk10 and Mk6 Assault; Marta; bases; adaptors.
- Previews are 3,000 triangles. They are packed as base64 text because artifacts can't serve binary files or `_` folders.
- Send only reports what would go to Blender.
