**Parts with no fit are dropped on their socket in the page, so they can be placed by eye there (Nov 13; Josh).**

Why: item 2's fitter keeps only what it is sure of (about half of new arms, a third of legs), and 2,547 library parts
have no fit. Until now the page gave such a part no place at all ("no X fit yet: placed by eye in Blender"): it was
not drawn, so Adjust could not touch it, and the only way to fit it was in Blender.

- **What changed** (`squad-builder/src/app.js`, `dropOn`): a part with no fit for its slot's socket is placed with the
  middle of its box on that socket (the socket with its gap), upright as its file is (its `upright` turn if it has
  one), marked `inst.nofit`, its place kept as a fit (`inst.dropF`). Legs with no Waist / Flat Waist fit drop on the
  torso's Waist. The list under the model still flags it ("no Neck fit yet: dropped on its spot, place it with Adjust,
  then Save fit") and the card keeps "no fit yet". Josh asked for the centre of the scene "or similar": the socket is
  the nearest thing to where it ends up.
- **Adjust** starts from the dropped place; Save fit writes the part's first fit (and `exact`) as any other. The log
  line has `"before": null`; on replay a first fit is applied only where the part still has none or already has that
  one (not over a fit it has gained since). `share_server.py` needed no change (a missing fit was already accepted).
- **Nothing else moves**: no sidecar is written until Save fit, `no_fit.txt` and the sidecar's own note stay, and
  Blender still parks an unfitted part beside the model. A part whose *host* lacks the socket (torsos without
  sockets) is as before: nowhere to drop it.
- **Tested** in a browser on the real index (6,564 parts, served read only): Torso 1 with a helmet, an arm and legs
  that have no fit: all three drawn with their middle exactly on Neck / Shoulder L / Waist, flagged; the helmet
  selected in Adjust, nudged 3 mm, saved (no library folder connected: for the visit) -> fit and `exact` on the part,
  flag gone, log entry with `before` null; `sidecarWithFit` on that arm's real sockets file adds the fit and `exact`
  and leaves the rest (its "filed without a fit" note too); replay applies a first fit and does not replace another.
  Not run: the playwright page tests (not installed on the PC), a save into the real library, the shared page.
