**Nov 15-16: the no-cut runs for the other makers, Josh's scope decisions, the drift found in the Mar Fil set-up,
and the new placement plan (`docs/PLAN.md`), which replaces item 5 of the old open list (now `docs/archive/`).**

- **Josh, Nov 15:** "go ahead with the other makers no cut list". `hands.py` (notes 105 / 107) was made to run
  without a blend (the host part's own surface is the spot), with an optional first example, a stop after N empty
  rounds, `--workers`, and a `write DIR` step; seat.py got a quick check of a fitted part at its own fit (`at_fit`,
  "near_first"), so a round over a maker takes seconds a part. Parts with no fit, searched from scratch afterwards,
  gave **0 sure matches** (Springles 303, Marta 48): the method only sorts parts that already have a fit.
- **Written to the library (backups in each task's `before`):** hand fits BBoosty 22, Turtle Ninja Heresy 9 and
  Tacticus 1, Marta Weapons 2, Bits 34. Dry runs only: Marta Tacticus hands (37 groups), Springles hands (stopped),
  backpacks of Turtle Ninja Heresy, BBoosty, Springles, CyberBrush. The per-maker configs were not kept.
- **Scope, Josh, Nov 15-16:** Terminators and Gravis are not part of this system (they would need their own base
  fits); no Marta Phobos; plain arms Mar Fil and (Nov 16) Springles; Springles guns not yet; weapons with a hand and
  two-armed weapons from every maker. He asked for a clear note "as it's been lost a few times": `CLAUDE.md`, the
  generated `docs/cuts-needed.md`, and now `docs/PLAN.md`.
- **Josh rejected the no-cut method:** "I want everything to be working in the new way so fitted against the match
  part". Then, on 264 per-sculpt "designs": "there are to my knowledge 3 wrist styles ... The mesh is almost
  irrelevant to the fit of any of this and only the mating surfaces and the roll matter at all." The cause: taking
  every bit of the hand touching the arm (fingers, knuckles) as the connector.
- **Drift found in the Mar Fil set-up (checked Nov 15 against the runs):**
  - his pad-spot, wrist and shin-spot cuts were found but never replaced existing sockets (written only where a part
    had none; the shin spot never, as it is on both legs). Library Pad sockets vs his cut: 0.15 mm / 5.7 deg median,
    8 of 65 over 0.5 mm; Hand 0.21 mm / 5.6 deg; Forearm agrees (0.01 mm);
  - each connector's anchor was its reference part's library fit (his placed Shoulder Pad 1 / Shin Pad 1 in the
    blends sit 0.26 mm / 1.0 deg and 0.18 mm / 0.7 deg from those);
  - round connectors took their roll from each part's own old fit;
  - weapon hands and backpacks were seated from old-fit examples (notes 105, 107), not cuts; 44 two-armed weapons
    kept library fits; near matches were written (legs 84 of 87).
- **Torsos** (checked Nov 16): sockets come from Mar Fil Assault Torso 1's "3rd attempt" placement copied by kit
  frame (Mar Fil, Old Style), my rules plus whole-torso shape carry (Turtle Ninja), Mar Fil sockets shifted by face
  differences (CyberBrush). Not cuts.
- **The new plan, grilled and agreed Nov 16:** `docs/PLAN.md`. Key points: cuts of the mating surface only, each
  reference sat against a Mar Fil part (one ruler: joint, frame, scale); anchor = his placement; roll from the file;
  hosts' anchors replaced by the cuts; near matches written and flagged; torso cuts per armour mark per maker, the
  rest per maker; joints stored as numbers and the origin set at import, STLs no longer rewritten (sharing = scripts,
  recipes and cuts, not files); Mar Fil first, proved on a small set before any library run.
- **Retired:** `kits/connectors/hands.py` and seat.py's "placed" connectors (kept as the record of these runs).
- Also Nov 15, at Josh's request: all Squad Builder share servers (4 copies, one serving) and both cloudflared
  tunnels stopped.
