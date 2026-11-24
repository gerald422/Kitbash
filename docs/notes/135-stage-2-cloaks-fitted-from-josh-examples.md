# 135 - Stage 2: cloaks fitted from Josh's two examples (Nov 24)

Josh placed 3 cloaks in `02 Stage 2 - cloaks on Torso 2` and removed two that are for Terminators (Marta Aug 2025
Cloaks 1 and 2), leaving 21. He asked for his examples to be used on the others.

There are **two styles of cloak, each placed differently**: with circles on the straps, and without.
- With circles: his example is **CyberBrush Bug Hunters Cloak 1**.
- Without: his example is **Marta 49 March 2026 Cloak 2**.

Marta Aug 4 and 5 had only been turned 180 deg in place; they are not examples.

**Method** (`kits/seat/fit_cloaks_from_examples.py`; shape only, never the cloak geometry):
1. Each style's contact patch is the marine surface within 0.3 mm of his placed cloak: Torso 2, the pack, the arm, the
   pad and so on. That is 7522 points for circles and 1797 for plain.
2. A cloak is fitted by ICP of that patch onto its surface. It is scored by trimmed rms, plus how much of the cloak
   ends inside the torso.

**Proof.**
- A blind search (24 axis turns, both styles) found neither example: 43 deg and 158 deg off. A big sheet takes a small
  patch almost anywhere, so the blind search can't be trusted.
- A local refine from his own placements keeps them: 0.17 mm / 1.1 deg and 0.80 mm / 3.8 deg.

So the same-series cloaks start from their series' example, moved by the bounding-box centres, then a local refine.

**Result, chosen by close-up renders** (`02k fits - close-ups (before choosing).png` beside the batch):
- **Put in his file, 11:**
  - CyberBrush Cloaks 2, 4 and 5, and Marta 49 March Cloaks 1, 3, 4, 5 and 6 (rms 0.18-0.37 mm);
  - Marta Jul 2025 Cloak (the fur), Marta Aug 2025 Cloak 3 and Marta Space Wolves Cloak 2 (the blind search, but they
    look right).
- **Left at the rough start for Josh, 6:**
  - CyberBrush Cloak 3 and Marta 49 March Cloak 7: the series start didn't land (rms 2.1 and 4.3 mm); they lie
    differently in their files.
  - Marta Deathwatch 2, Sharks, Aug 2025 Cloaks 4 and 5, and Space Wolves Cloaks 1 and 3: the blind search put them
    across the waist, the hip or the side.

His Blender was the MCP one, so the 11 were set live, tagged `kb_applied`, and saved. `read` from disk: his 4 and the
11 changed, 6 untouched.

The first repo copy of the script was refused: it was the scratch version, which had the full home path (the Windows
user name) in it. The committed one works out its paths at run time.
