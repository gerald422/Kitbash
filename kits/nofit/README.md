# Parts filed without a fit (Nov 6)

Josh: "anything that doesn't have a fit is kept logged so I can do them if needed". On Nov 6 these parts went into the
library under their category with no fits, and every part left out was logged with a reason. Prepare's
`_builder\no_fit.txt` lists the filed ones. Each sidecar's `notes.category` says how its type was found.

## `marta/` (Marta weapons and arms)

- `classify.py` takes the Nov 2 leftovers (`_backups\marta-1h-2026-11-01\results.jsonl`) plus the Nov 5 extras and writes `plan.json`.
- It skips presupported copies, armour plates, and loose shields or handles whose joined "with handle" version is already in. Those are logged in `skipped.txt`.
- 146 were filed, and with the two-armed batch (41 sidecars, `kits/marta/twoarm2/`) that makes 185 library parts. Two were dropped as copies. The renames are in `rename_log.csv`.

## `setup-kits/` (leftovers in kits already set up)

The makers covered are Mar Fil, Turtle Ninja, Springles, BBoosty and Marta (every type).

**`survey.py`** goes through `D:\new cults` for the library's makers. It lists every STL/OBJ that isn't a `_sources.csv` source, and takes out:
- presupported copies;
- byte-identical copies of a library source (sampled hash);
- name twins.

**`classify_all.py`** sorts each leftover:
1. These are left out and logged:
   - macOS `._` files;
   - maker's left copies already folded into the right part as a mirror variant (the variant `from` keeps the copy's file name);
   - parts with the same triangle count and sorted bounding box (within 0.02 mm) as a library part from the same maker, i.e. a mirror or re-export;
   - bases, rocks and scenery;
   - posed or whole models.
2. The type comes from the first of these that gives one:
   - "no hands" in the name;
   - a Springles ammo belt (Heavy Weapon Cables);
   - a body-part word in the name;
   - the most common type among library parts from the same source folder;
   - the folder name (`partTypes.json`);
   - weapon or accessory words;
   - otherwise Unsorted.

**Results:**
- `log_all.csv` has one row per file: filed with its type and how the type was found, or left out and why.
- 2,131 were filed. `plan_library` then dropped 59 as copies of each other (`dropped_copies.json`), so **2,072 library parts**: Marta 1,009, Turtle Ninja 451, Springles 441, Mar Fil 133, BBoosty 97.
- Left out: 172 folded left copies, 106 `._` files, 36 bases, 21 same-shape copies, 11 BBoosty whole poses.
- 27 parts named with aquila, purity seal or scroll were already hidden by `_hidden.txt`'s word rules.
- `never_set_up.json` lists the kits with no part in the library yet (Mar Fil 20 kits, the Iron Hands folder 27, Springles mk6 cybernetics, TN Primus Medicae / WGBL). Josh picks which of these go in. The Iron Hands `Iron bits` folder and the Techmarine Conversion Kit (one part each in the library so far) were held back for him to pick too.

**Delivery** was the same for both batches. Sidecars were written beside the sources in `D:\new cults`, never over an existing one. Then, on the PC:
1. `survey_new`, then `plan_library --only <tops>`, then the plan filtered to these parts.
2. `build_library` in 140 s steps, then `verify` (0 bad).
3. `_sources.csv`: the original bytes kept and the rows appended (CRLF).
4. `plan_names`, then `rename_library` (its `_sources.csv` rewrite fails on the unquoted-comma rows, as before). The appended rows were renamed line by line.

Backups and plans are in `D:\Kitbash Library\_backups\marta-nofit-2026-11-06\` and `nofit-survey-2026-11-06\`.

## After Prepare (Josh, Nov 6)

The index is `88ed6e38` (6,451 parts, all with previews). Of the 2,257 new parts:
- **136 have fits:** 29 from the batch above, plus 107 that Prepare's hand and shield rules gave to held parts and shields.
- **1,180 are in `no_fit.txt`** (copied here; 1,229 parts in all).
- **703 torsos have no sockets yet**, so nothing attaches to them.
- **238 are types with no page step.**

`no_fit_all.csv` lists all 2,121 without a fit, with their status.
