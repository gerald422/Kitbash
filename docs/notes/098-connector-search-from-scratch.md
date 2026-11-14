**The search from scratch (Nov 14): `kb/connect.py` finds Josh's connectors on a part without its fit. Checked on
every fitted Mar Fil arm (220) and legs (88): a "sure" answer was never wrong where the library's joint agrees with
the shape, and the 5 where it disagrees look like library errors. The production seating script is next.**

- **Why a new search**: notes 097's (`connector_try.py`, random places, point-to-point ICP) found wrist B on 7 of 25
  arms that all have it and the pad spot on 0 of 25.
- **How `kb.connect.find()` works** (numpy + Blender's KD tree; no scipy, nothing installed into Blender):
  candidate places every 0.35 mm over the part with smoothed normals; the connector's anchor (its point nearest its
  middle) put normal-to-normal on each and spun in 15 deg steps; each pose scored by how many of 48 connector points
  land on the part's surface (a voxel grid, ~0.2 mm); the best 12 places x up to 3 turns settled by **point-to-plane
  ICP** (point-to-point crawls along smooth surfaces: 0.2-0.5 mm short in the test) and scored point to plane
  (median mm and share of the connector on the surface), so a part's sampling density doesn't matter. If that isn't
  sure, a wider pass (36 places, 10 deg). Ties (within 0.01 mm): the pose nearest where the connector sits on its
  reference is kept (Mar Fil exports in its kit frame), and `ambiguous` says another place fits as well.
- **`find_all()`**: a part type's connectors searched together, each place used by one connector (the best fit
  claims it first). Needed: **wrist A fits the shoulder disc** (0.007 mm even on its own arm); with the disc claimed
  it has to find the wrist. Mar Fil arms: disc (`arm connector.blend`, notes 096), pad spot, wrist A, wrist B.
- **Levels**: `sure` = median <= 0.005 mm and >= 90% on the surface (a copy of the reference's connector);
  `look` = <= 0.03 and >= 75% (a variant: placed, to be looked at); else `none`. Copies fit at 0.0005-0.002.
- **Check** (`kits/nofit/connector_search_check.py`: truth = the connector settled where the part's own fit / socket
  puts the joint; the search never sees it). Right = within 0.5 mm and 5 deg of tilt.

  | connector | sure: right / disagrees with library | look: right / wrong | none |
  |---|---|---|---|
  | shoulder disc (220 arms) | 182 / 0 | 12 / 17 | 9 (variants, 2-disc bolters) |
  | pad spot (220 arms) | 57 / 4 | 54 / 4 | 101 (79 have another shoulder) |
  | wrist A (220 arms) | 27 / 1 (+1 gun, no joint in library) | 36 / 28 (+25 no joint) | 102 |
  | wrist B (220 arms) | 32 / 0 (+11 with no Forearm socket in library) | 0 | 177 |
  | legs waist (88) | 5 / 0 | 71 / 11 | 1 |

  **Where a sure answer disagrees with the library, the library looks wrong** (an exact copy, 0.0007-0.0016 mm and
  95-100% on the surface, where the library's joint fits at 0.16-0.20 / 26-33%): Pad sockets of Outrider Arm Wight
  Handle A1 L, B1 L, B2 L and Arm With Handle B R (4-14 mm off); Veteran Arm B's Hand socket (12 mm). Wrist B is an
  exact copy on Assault Arm 8B L / R, 8C L and Jump Chaplain Arm A-D L / R, which have no Forearm socket. Not checked
  by eye yet.
- **Weak spots**: wrist A is a plain shallow round face: right on its copies, poor on variants (look 36 right / 28
  wrong). The legs waist is a variant on most legs (Intercessor legs 0.5-0.7 mm off, flagged look); on Bladeguard /
  Veteran "Body" parts (legs with torso) it also fits a ring 28 mm up (flagged ambiguous).
- **Time**: ~12 s a legs, ~50 s an arm with four connectors (the wider pass runs on most): the KD tree queries in
  Python are the cost. Fine for a background `.bat` per drop; worth speeding up later.
- **Whole marines** (`kits/nofit/connector_demo.py`, Assault Torso 1, library fits vs the connector method):
  Assault legs / arms / pads 0.5-1.0 mm from the library's (median over the part); Veteran Arm C 0.0, Outrider
  Handle B1 L 2.1. **The turn is the weak spot**: round connectors fix where a part sits, not the arm's swing about
  the shoulder or the legs' heading; the search keeps the turn the part has in its own file, which holds only for a
  kit exported in the reference's frame. Outrider Legs B end ~10 deg from the library (Outrider legs are exported
  ~90 deg turned; flagged look); Captain with Jump Pack arms (no fit in the library) go on as their file has them,
  arms out (its kit sits 13 mm higher; no Captain torso to check); its legs match no waist (another design).
  Ways to fix the turn: connectors cut with a keyed (non-round) feature, or Josh's turn fix per connector.
- **Never `read_factory_settings` in a script on the PC**: the first preview did, and Blender removed Node Arrange's
  networkx from `extensions\.local` (put back by Blender on its next start; `docs/reference.md`).
- **Test**: `tests/kb/t_connect.py` (Blender, ~10 s, made-up shapes: moved / turned / mirrored parts found exactly,
  a different design not). Nothing written to the library.
