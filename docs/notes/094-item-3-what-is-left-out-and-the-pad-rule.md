**Item 3, second pass (Nov 14): what is left out on purpose, the pad rule over the unfitted pads (2 Mar Fil pads fitted), and why the rest stays for by-eye references.**

- **Left out on purpose (Josh, Nov 14; it was already the Oct 20 scope, notes 026, and notes 093 missed it):**
  - **Turtle Ninja: one pose a torso, the straight ("flat") one**, usually number 1 or 9 of each letter (about 30-40 in
    the Mk7-8 builder; 67 across the maker have their own sockets). The posed copies (the other eight of each letter:
    twisted, leaned, both) stay without sockets: 338 of them. Nothing from the "Kitbash Files (Rigging Required)"
    folders either (2 arms, 1 legs, 2 torsos).
  - **Marta: no torsos** (277); **heads skipped for now**, Josh comes back to them (287 unfitted, 250 hers).
  - `OUT` in `kits/nofit/carry_library.py` keeps `run` off all of these (`--all` to include them); the skill's Chests
    line and `docs/OPEN.md` say so too.
- **The 80 Turtle Ninja torsos socketed by notes 093 are posed copies** (numbers 2, 3, 5, 7, 8 beside a straight 1 or
  9), so against this. They are still in the library with their sockets; whether they are put back (backups:
  `_backups\carry-nofit-2026-11-14\before`, index entries to follow) or kept is asked of Josh. Not undone here.
- **What the posed copies are** (measured before the scope was pointed out, kept in case they are wanted later):
  every pose keeps a flat round bottom face level in the file (45-50 mm2, normal within 0.2 deg of the file's down),
  so the file's frame is the legs' frame and the pose is the upper body turned over it. Numbers 2 / 3 are twists
  about the upright (7 deg), 4 / 7 leans of 10 deg (the upper body moved rigidly: 0.05 mm, the sampling floor, with
  the bottom cut level again), the rest both. The Nov 14 run missed most of them only because `kb.carry` tries the 4
  fitted parts nearest in box size, which seldom included the same letter's straight torso: against its own letter's
  number 1 a posed torso's shoulders, neck and back match at 0.05-0.10 mm. Carrying the waist with turning is wrong
  on a lean (it comes out tilted 10 deg, 0.2 mm under the bottom): the waist joints belong on the bottom face, the
  straight torso's own moved by the face centres' difference (the Nov 14 `turn` waists agree with that to 0.15 mm).
- **Pad rule over the unfitted pads** (`run --types "Shoulder Pads" --scopes rule`: `kb.fit.Pads`, pad 62's shell,
  add-a-maker's gates): 59 tried, 26 pass the gates (scale 0.851-1.349, <= 0.60 mm), 32 only match at the scale
  limit (smaller than 0.85 of pad 62, shields, cloaks with a pad, accessories filed as pads).
- **The pad rule checked against the library's own pads** (`loo --scope rule`, 87 fitted pads, 10 a maker): it gives
  the library's fit back on the makers whose pads it fitted in the first place (Redwarden 10 of 10, Springles 10 of
  10, WargamesPrint to its lift, Mar Fil 7 of 7, TN Mk10 2 of 2). On pads fitted another way it disagrees: BBoosty 8
  kept, none within 0.5 mm / 3 deg (7-25 deg); CyberBrush 6 kept, none (4 turned 172 deg); Marta 22 kept, 4 within,
  6 turned more than 100 deg; TN Moritat 82 deg. Which of the two is right there was not looked at, but pad 62's
  shell is nearly round and a small match distance does not pin its turn. By match distance: every pad within
  0.10 mm agreed (10 of 10 outside the three rule-made makers), the first wrong one is at 0.11.
- **Used** (`PAD_USE = 0.10` in the runner): 2 pads, `MarFil Captainwithjumppack - Shoulder Pad 1` and `2` (x1.06 /
  x1.05, 0.06 / 0.04 mm), `Pad R`. Blender (`test`: on Mar Fil Torso 1 + Arm 1A R): placed, closest 0.05 / 0.06 mm,
  no cut; pictures looked at. Not lifted with `padlift.py` (nothing cuts). Not used: the 3 Bike Chaplain pads
  (0.17-0.18 mm), 7 TN Mk4 Tactical pauldrons (0.15-0.16), 14 Marta pads (0.22-0.35), 1 Marta shield.
- **Delivered** (`pads-rule-2026-11-14`, `kb.py apply`: 4 files, md5s match, backups
  `_backups\pads-rule-2026-11-14\before`): 2 sidecars merged, the index in place, 2 lines out of `no_fit.txt`.
- **What is still without a fit in the five types, and what it needs** (nothing here can be had by more matching):
  arms 80 (about half are effects, accessories, whole figures filed under Arms; the real ones are one-off character
  arms and two-arm sets with no near-copy), legs 51 (the same: Heavy Gurl 7, Aggressor 3, kneeling / laying one-offs,
  accessories), pads 57 (above), heads (later). Each family wants one placed by eye (Adjust on the page, Save fit)
  and can then be carried to its folder (`run` again), or a rule of its own. The pad rule's disagreement with the
  library on BBoosty / CyberBrush / Marta pads belongs to item 4 (pauldrons).
- **Pads by their inside only (Josh, Nov 14: "the exterior is effectively irrelevant, only the internal shape matters
  ... one fit should be needed and the rest copied by shape match").** `kb.carry.inner` cuts a pad's surface down to
  what is seen from the middle of its dome (the nearest point in each 3 deg direction from the centre of the ball it
  lies on; cross-sections looked at: clean on plain and badged pads, partial on a skull-hand pad, meaningless on
  shields). `Inner` / `InnerRef` let `kb.carry.like` run on insides; the match is then the distance 90% of the points
  are within, both ways (`GATES["inner"]` 0.20 mm: the rim has to line up, a dome alone matches at any turn), and of
  turns matching alike the smallest is taken. Runner: `run` / `loo --inner`, `families`.
- **Checked on fitted pads** (`loo --inner`, 87 pads, folder then maker): insides that coincide do exist (matches of
  0.04-0.09 mm, rim included). Kept from folder-mates 54, 42 of them within 0.5 mm / 3 deg of the library's own fit
  (Redwarden 10 of 10, Springles 10 of 10, Mar Fil 8 of 9, TN Mk10 2 of 2, BBoosty 6 of 7, WargamesPrint 2 of 3); from
  the same maker elsewhere 31 kept, 24 within. **The ones that are not within are pairs of pads whose insides
  coincide and whose library fits differ**: Marta Termi Shoulder 1 / 2 by 54 deg, Marta SW Terminator 3 / 5 by 8-9,
  Techmarine V2 pads 6-14, WargamesPrint Pad 18 by 9, Mar Fil Outrider L by 18, CyberBrush Set 1 by 123-180 (a
  front-back alike inside cannot say which way round it is). So it is the library's fits that disagree with each
  other there, which is item 4's pauldron problem, measured: a family needs one fit and the rest copied from it.
- **Over the 57 unfitted pads** (`run --inner`): 1 has a fitted pad with the same inside (Marta SW Terminator Pad 4,
  0.20 mm, at the limit, from a pad whose own fit is one of the disagreeing ones: not delivered). The others are
  unfitted because nothing fitted has their inside. Grouped among themselves (`families`): 45 families; the ones with
  more than one pad are TN Mk4 Tactical Pauldron 1-5, 8 (6) and 6, 7 (2), Marta Sep 2026 Thicc Shoulder Pad 1-3,
  Marta Aug 2025 Shoulder Pad 3 + Mithraism Shoulder Pad 1, 2, Marta Shoulder Sield 1, 7, Bike Chaplain Pad 2 R + L.
  The measure is strict (a cloak or trim seen from inside counts), so Marta's singles may be split too far.
- **Not done**: nothing written to the library from the inside matching. Next choices: one pad placed by eye in each
  many-pad family, then `run --inner`; the same matching used to make each fitted family agree on one fit (item 4);
  pad 62's inside (not its whole shell, with scale) as the rule for the one-offs.
