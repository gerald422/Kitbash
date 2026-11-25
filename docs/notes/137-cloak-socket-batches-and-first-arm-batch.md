# 137 - Cloak socket batches for every torso, and the first arm batch (Nov 25)

Josh: "anything i have not used add it to the hidden list". He also asked for the batch files to be built while he
sleeps, so he can work through them the next day, and for the arm batches.

## Hidden

These went into `_hidden.txt` (library and repo copies; the old copy is in
`_backups\hide unused cloaks 2026-11-25 0021\before`):
- the Mar Fil Captain cape;
- the 6 cloaks he removed: Marta Jul 2025 (the fur), Sharks, Aug 2025 Cloaks 1-2 (Terminator), Space Wolves Cloaks 2-3.

Nothing is deleted.

## The Cloak socket on every other torso (`make_cloak_socket_batch.py`)

Each torso's Cloak socket starts as its own written Back socket, the same way Torso 2's Cloak socket is its Back frame.
So every cloak starts against the backpack mount exactly as Josh placed it on Torso 2.

The torsos differ in shape, so Josh moves the cloak to sit right on each one. That move is the torso's Cloak socket
(half "socket"), and all 17 cloaks share it.

Each column holds:
- the torso, stood on its waist in Torso 2's frame;
- its written pieces, locked: the spacer, arm, guide and pad (mirrored), Helmet 1, Back Pack 1 and Legs 1A;
- **CyberBrush Cloak 1** (circles), the part to move;
- **Marta 49 March Cloak 2** (no circles), riding on it by the two written fits, in its own collection to hide. `batch.py` specs now take `"collection"` for this.

The first column is Torso 2 as written.

**The five files**, in `~\Desktop\mar fil connectors\batches\`, all dated 2026-11-25:

| File | Torsos |
|---|---|
| Redwarden and TN torsos 1 | 22 |
| TN torsos 2 | 17 |
| TN torsos 3 | 16 |
| Mar Fil torsos | 7: those not hidden in the builder |
| Mar Fil hidden torsos | 27: Josh hid these in the builder on Nov 1 (Assault 1, 3-6, Intercessor 1-4, Veteran A-D, Bladeguard 1-2, 13 Outriders). Optional |

**Checked by renders:** columns of TN 1 and Mar Fil, from the back and side, against Torso 2. Both cloaks sit as on
Torso 2.

## Stage 3, first arm batch (`make_arm_batch.py`)

The file is `03 Stage 3 - Mar Fil Assault right arms (2026-11-25).blend`: the 23 right Assault arms other than 2B R.

- **Each column:** Torso 2 locked; the spacer on its written Shoulder R; Helmet 1, Back Pack 1 and Legs 1A on their fits; and the arm on the spacer.
- **The arm** is the part to move (depth and turn); its mirror shows live.
- **What's written:** the arm's Shoulder R fit (half "fit") and the mirror fit in its L variant (the B arms have one).
- **Where each arm starts:** its old Shoulder R fit on Torso 2's old socket (stage 1 backup), carried by Josh's stage 1
  change to Arm 2B R. That change is nil: he moved the spacer, not the arm. So each arm starts at its old seat.
- **Check:** see-through close-ups show each arm meeting the spacer about as deep as Arm 2B R does.
- **No pads on these arms:** each arm's Pad R socket is still the old frame until stage 4.

Only one arm batch for now: Josh's fixes on it may show a repeated correction to pre-set in the next ones.
