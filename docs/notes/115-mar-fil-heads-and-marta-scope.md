# 115: Mar Fil heads done; Marta brought in (Nov 19)

## Cuts that looked off their parts

22 of the 33 cuts looked 0.05-0.5 mm off the part objects beside them in the reference. Checked: every cut matches a
library file triangle for triangle; some reference objects are slightly different meshes, and a few cuts came from
another file than the part next to them (`Assault arm wrist a` and the Assault pad spot from Arm 2A R, the
Intercessor pad spot from Arm 5 R, the Veteran wrist from Combi Weapon 4A). A copy with fresh library parts put
exactly under every cut (`Kitbash reference (cuts put back 2026-11-19).blend`) gives the same joints from the reader,
except the pad joint by 0.06 mm / 0.13 deg. So the offsets don't affect the runs; nothing to fix.

## Heads (run 20)

Josh's `Intercessor Neck` cut (Intercessor Helmet 1; the Intercessor and Assault helmets are the same, so one cut)
is in `~\Desktop\mar fil connectors\Kitbash reference updated.blend`. `reference.cut_name` now reads `<type> neck`
as the head neck (a torso's neck cut always says "torso"). Run 20 (`proving 20 heads`, 74 heads, 5 min on 24
workers): 72 sure (51 on the Intercessor cut, 21 on the Bladeguard one; was 21 sure), 2 not placed: Veteran Helmet A
and B (65-70 % on the Bladeguard cut). Sheets look seated. Largest roll changes from the file: Assault Head 13
(27.5 deg), Intercessor Head 2 (-18.8 deg).

## Marta

In (Josh): Marta legs, arms, hands, weapons (ranged, melee, two-handed), bases, pauldrons, shin pads, accessories
and most loose bits; Terminator and Gravis accessories too. Out: Marta torsos, heads, backpacks. Legs first, then
arms. Marta Tacticus has 186 legs and 224 arms (111 R, 72 L, 41 unsided). Marta legs need their own waist cut and,
being flat topped, a torso spacer on a Mar Fil torso (as the Springles arms do). The reader can't yet take a joint
through a spacer (the child cut must sit on the host): to build with the Springles spacer.

## One legs waist cut (runs 22-24)

- Run 22: Josh's deeper waist cut (`new waiist cut`, taken on Intercessor Legs 1, 3.5 mm deep against the old
  Assault cut's 0.8 mm) alone: Intercessor legs 1 sure, 23 near (Josh: near perfect), the other 21 legs none (64-75 %
  cover: the cut's back and lower sides, the Intercessor belt and hips, are on none of them). It showed the old cut's
  flat top let the Intercessor legs slide: 2-4 mm and 6-31 deg off (3.2 mm / 8 deg on Legs 1, where the new cut matches
  Josh's placement).
- Run 24: Josh's trimmed `another waist legs cut` alone: 43 of 46 placed (2 sure, 41 near); not placed: Intercessor
  Legs 10, Jump Chaplain Legs A, Techmarine Legs 4. Intercessor legs within 0.3 mm / 4 deg of run 22 (18 of 25).
  Assault, Jump Chaplain and Techmarine legs move 2.3-5 mm / 7-12 deg from the old cut's; Josh: "they look right,
  use the one cut". Jump Chaplain Legs D comes out turned 176 deg (backwards).
- A per-armour-type preference between cuts was tried and dropped (one cut instead).
- Legs are children on the waist: a near waist is written and flagged, as for any child (hosts-sure-only is about
  the legs' own spots).
