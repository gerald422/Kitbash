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

## Mirrored cloaks (Josh: "They all bend in one direction or another so a mirrored version for all would be preferred")

Nothing needs adding to the library for this:
- The Mirror button (Squad Builder and TIOW Inbox 1.17.11, `mirror_in_place` / `mirrored_sidecar`) already makes any
  part's mirror image. It puts the mirror on the same socket with the fit mirrored (MX . F . MX) and keeps the part's
  `scale`.
- A cloak's socket is centred: Torso 2's Cloak socket is at x = -0.001 mm, square to the torso. So the mirrored cloak
  hangs from the same spot and sweeps the other way.
- The other torsos' Cloak sockets start from Torso 2's, so the same holds for them. A socket Josh moves a little
  off-centre mirrors about where he put it.

Checked by renders on Torso 2: CyberBrush Cloak 1 and Marta Aug 2025 Cloak 5 (scaled), as placed and mirrored.

It works once cloaks snap. Cloaks are still under `noJoint` in `joints.json`; the Cloak joint goes on when the cloak
batches are written (stage 6 in the plan).

## Written: the Mar Fil hidden torsos (Nov 25)

Josh: "are all good", with the file unchanged. So each of the 27 torsos' Cloak socket is its Back socket, as built.

- Written with `batch.py write`; the old sidecars are in `_backups\batch write 2026-11-25 0853`.
- Every joint placed from the library matched the file: 0.0000 mm.
- The batch file went to the Recycle Bin.

## Written: the 7 Mar Fil torsos (Nov 25)

Josh: "also good", with the file unchanged. So each torso's Cloak socket is its Back socket, as built: Torso 2 Insert, Intercessor Chest 5, Veteran Chest E, Techmarine, Jump Chaplain, Outrider Torso B and the Bike Chaplain chest.

- Written with `batch.py write`; the old sidecars are in `_backups\batch write 2026-11-25 0854`.
- Every joint matched the file: 0.0000 mm.
- Every Mar Fil torso now has a Cloak socket.

## TN cloak files redone as "b" (Nov 25)

Josh: the no-circles cloak was locked, so he couldn't adjust it. He asked for each cloak in its own collection, to show
one at a time.

The three TN files are rebuilt as `(2026-11-25 b)`. Neither had been saved since it was built, so nothing of his was
lost. The old copies went to the Recycle Bin.

In the new files:
- both cloaks are movable, and both pivot on the torso's Cloak start (its Back);
- they sit in collections `CLOAK 1 - circles on the straps` and `CLOAK 2 - no circles`;
- the circles cloak's move is written as the torso's Cloak socket;
- the no-circles cloak's move is compared with it at the write. If the two moves differ on a torso, Josh decides
  there (one socket can't hold two different moves).
