# Kitbash

Josh's Warhammer 40K kitbashing pipeline. Goal: a squad picked in the Squad Builder arrives in Blender with every
part where it belongs, whatever maker it came from, and prints cleanly. Consistent placement is the product.

- **Kitbash Library** (`D:\Kitbash Library` on the PC; sidecars mirrored in `library/`): one STL + `<part>.sockets.json`
  per part (sockets, fits, variants). `_sources.csv`, `_hidden.txt`, `_builder\index.json` + previews, `_backups\`.
- **TIOW Inbox** (`addons/tiow_inbox.py`): Blender add-on that imports and snaps parts; Save Correction.
- **Squad Builder** (`squad-builder/`): one offline page, guided picking, sends a squad to Blender.
- **Kitbash Finalise** (`addons/kitbash_finalise.py`): booleans a model into print pieces with pegs and a letter.
- Part Sockets is Josh's own add-on and is not in this repo.

## Read only what the task needs

| Need | Read |
|---|---|
| What's open / waiting on Josh | `docs/OPEN.md` |
| How a kit or feature was done | `docs/notes/INDEX.md`, then the one entry |
| Sidecar format and placing conventions | skill `kitbash-sidecars` |
| PC paths, delivery, index, corrections, tests | `docs/reference.md` |
| What is installed on the PC | `tools/installed.json` (check with `tools/kb.py verify`) |

Do not read `addons/tiow_inbox.py` whole (226 KB): `grep -n "^def \|^class "` and read the functions you need.

## Standing rules (Josh)

- Keep usage low. Ask before heavy work when a question saves effort. Ask for a smaller blend instead of copying a huge one.
- Test a subset: only the parts a change can affect. The full regression is `Run checks.bat` on the PC (free), not here.
- Every part must fit every kit: follow the shared conventions, never a new frame per kit.
- Never overwrite what Josh or Prepare made: merge sidecars with `kb.sidecar.merge` (it keeps clicked / copied / auto
  anchors, `tiow_corrected`, `tiow_holds`, `exact`). Back up first.
- Parts without a fit are still filed under their type and logged, never dropped.
- Renegade chapter: no aquilas, purity seals or scrolls (`_hidden.txt`; merge with Josh's current file).
- Public repo: no STL / OBJ / blend / npz / previews, and nothing identifying Josh (no surname, Windows user name;
  home paths as `~\...`). `tools/validate.py` and CI enforce this; run it before every commit.
- Never write TIOW's `config.json`. Never `pkill -f`. Delete only your own temp files; deletes on the PC need permission.
- Bionic legs: branch `bionic-1.18` (TIOW 1.18, Finalise 0.3.2) is abandoned. Never merge or deliver it; the work
  restarts from scratch on `main` (`docs/OPEN.md`).

## Doing a task

1. Prefer running on the PC (repo clone, real library, no staging): see `docs/reference.md`. Use the container only
   for Blender-heavy work, set up with `tools/setup_container.sh`.
2. New maker's heads / pads / loose bits: `kits/creator/add_creator.py`. Anything else: write against `kb/`
   (geometry, sidecars, index, delivery). Don't copy helpers into a new script and don't hardcode `/home/claude` paths.
3. Deliver with `tools/kb.py apply` (checks, backup, write, verify). Never hand-roll the md5 steps.
4. A new part type or joint: edit `joints.json`, run `tools/gen_joints.py`.
5. Finish: `tools/validate.py`, commit to `main` and push (session attribution lines), add `docs/notes/NNN-<slug>.md`
   plus its line in `INDEX.md`, update `docs/OPEN.md` and `tools/installed.json`. Notes are not copied anywhere else.
