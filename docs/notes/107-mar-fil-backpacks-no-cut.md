**Mar Fil backpacks seated with no cut and moved onto the back joint (Nov 15): 32 of 32 in 3 mount designs.**

- **How:** `kits/connectors/hands.py` is now general: config keys `fit` (the joint, default Hand), `label`,
  optional `spot_mm` / `gap`. The config is `kits/connectors/marfil_packs.json`.
  - One example per mount design is put on Assault Torso 3's Back socket by its library fit.
  - Its side is whatever of it lies within `gap` 0.6 mm of the torso's own surface within `spot_mm` 25 mm of the
    socket. That comes from the new `seat.py` "placed" connector with no `spot` (no blend, no cut).
  - `seat.py side_sock` now finds unsided sockets ("Back") as they are.
  - Josh: "I'm happy with your cut let's use that". He had also cut one, but it wasn't in `~\Desktop\mar fil
    connectors` when looked for.
- **Survey first:** the library's Back fits sit 0.01-0.05 mm off the torso (Intercessor, Hellblaster) or
  0.23-0.28 mm off (Backpacks 1-4, Bladeguard, Veteran, Techmarine), hence the 0.6 mm gap. The Bike Chaplain pack had
  no fit.
- **Designs** (`_backups/packs-2026-11-15`):
  - Veteran Backpack A + 13 (Veteran 7, Bladeguard 6): 0.00 mm from their library fits.
  - Intercessor Back Pack 1 + 12 (Intercessor 6, BackPackUpdate 4, Techmarine, Bike Chaplain): median 0.06 mm.
    - Backpacks 1-4 move 0.86 mm / 5.6 deg; they now seat like the Intercessor pack (match 0.0003-0.0008 mm).
    - The Techmarine pack moves 0.74 mm.
    - The Bike Chaplain pack gets its first fit.
  - Hellblaster Pack 1 + 4: 0.01 mm.
  - Nothing far or flipped.
- **Written:** 29 fits (`seat.py write connectors-2026-11-15-40/41/42 --sure --near 2`).
- **Moved:** 32 files (`origins.py run kits/connectors/marfil_packs_origins.json`, task `origins-2026-11-15-5`; the
  origin moved 34 mm, from the kit frame to the back joint).
  - Check: 32 models (each pack on Assault Torso 3 or Intercessor Chest 1) recorded before the move and built after:
    all 64 parts where they were.
- **Mar Fil now has every type seated by connectors** except accessories (last, on purpose) and the parts listed in
  `docs/cuts-needed.md`.
