# Kitbash

Tools for building Space Marine kitbashes from a library of STL parts: send parts from
TIOW-FTRP or the Squad Builder page into Blender, where they snap onto each other by
sockets, then booleaned into print pieces.

**No STLs here.** The makers' files stay on your drive; this repository holds the code and
the sidecars (`<part>.sockets.json`: sockets, fits and anchors) that make them fit.

| Folder | What |
|---|---|
| `addons/tiow_inbox.py` | TIOW Inbox (Blender add-on): imports and snaps parts, Save Correction, bases settle |
| `addons/kitbash_finalise.py` | Kitbash Finalise (Blender add-on): booleans a model into print pieces with pegs and letters |
| `bridge/` | TIOW-FTRP side: `apply-blender-bridge.mjs` (Send to Blender patch), `_library.json`, the add-on's README, the lift-out script |
| `squad-builder/` | The Squad Builder page (`src/`, built into `Squad Builder.html` by `build_page.py`), Prepare (`prepare_builder.py`, `build_index.py`) and its tests |
| `library/` | Every sidecar from `D:\Kitbash Library`, same folders, plus `_sources.csv` and the move/rename logs |
| `library-tools/` | Building, renaming and folding the library; `sync_sidecars.py` copies sidecars between the library and `library/` |
| `kits/` | The scripts that worked out each kit's sockets and fits |
| `tests/`, `finalise/tests/` | Blender test scripts (written for the build machine's paths) |
| `docs/project-notes.md` | The full history: decisions, measurements, versions |

## Install

- Blender 5.1: copy `addons/tiow_inbox.py` and `addons/kitbash_finalise.py` into
  `%APPDATA%\Blender Foundation\Blender\5.1\scripts\addons` (or Install from Disk), tick them, restart Blender.
  Part Sockets must be enabled too.
- Squad Builder: `squad-builder\Squad Builder.html`, with `Prepare Squad Builder.bat`, `prepare_builder.py`
  and `build_index.py` beside it. See `squad-builder/README.txt`.

## Keeping the sidecars here up to date

Save Correction, anchors you click and Prepare all write sidecars in `D:\Kitbash Library`. To record them:

    library-tools\Export sidecars to repo.bat      (or: python library-tools/sync_sidecars.py export "D:\Kitbash Library" library)

then commit. `sync_sidecars.py import library "D:\Kitbash Library"` puts a committed version back.

## Branches

- `main`: what is installed (TIOW Inbox 1.17.3, Finalise 0.3.3).
- `bionic-1.18`: the bionic legs work (TIOW Inbox 1.18, Finalise 0.3.2), on hold until the plug position is settled.
  It predates 1.17.1-1.17.3, so those changes need merging in when it resumes.
