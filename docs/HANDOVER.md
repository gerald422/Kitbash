# Kitbash build: handover (1 Nov 2026)

Everything needed to pick this work up in a fresh Claude session. The full history, with every measured value and
decision, is `docs/project-notes.md` (the same file is the Project doc `claude/part-sockets-tiow-integration.md`).
How to make sidecars is the skill `.claude/skills/kitbash-sidecars/SKILL.md` (copy in the Project at
`claude/skills/kitbash-sidecars/SKILL.md`).

## What the build is

Josh's Warhammer 40K kitbashing pipeline, three pieces that share one part library:

- **Kitbash Library** (`D:\Kitbash Library` on Josh's PC): every printable part as an STL with a
  `<part>.sockets.json` sidecar (sockets, fits, variants). `_sources.csv` lists every part and where it came from
  (`D:\new cults\...`), `_hidden.txt` hides parts from the page (renegade chapter: no aquilas, purity seals or
  scrolls, plus Josh's own hides), `_builder\index.json` + `_builder\previews\` feed the page, `_backups\` holds a
  dated folder per change.
- **TIOW Inbox** (Blender add-on, `addons/tiow_inbox.py`, now **1.17.5**): imports parts sent from TIOW-FTRP or the
  page, rebuilds their sockets, snaps them onto the model (rock/settle for belt bits, base rise, adaptors and
  connectors), Save Correction (Fix the Part / Fix the Socket).
- **Squad Builder** (`squad-builder/`, one offline HTML page): pick parts step by step (Base, Legs, Torso, Arms
  R/L/Two-handed, Head, Back, Wings, Shoulder pads, Weapons, Shin pads, Loincloth, Belt), see them placed from the
  index, send the squad to Blender through `<library>\_builder\inbox`.
- Also: **Kitbash Finalise** (`addons/kitbash_finalise.py`, 0.3.3, booleans a model into print pieces) and
  **Part Sockets** (Josh's own add-on, 6.2.0 in the container; it is not in this repo).

## Git

- Repo: <https://github.com/gerald422/Kitbash> (public: sidecars and scripts only, never STLs/OBJs/blends/npz/
  previews - `.gitignore` blocks them; the makers' files are paid).
- Branches: `main` = what is installed on Josh's PC. `bionic-1.18` = TIOW Inbox 1.18 bionic legs + Finalise 0.3.2,
  on hold (Josh: don't deliver it); it predates 1.17.1-1.17.5, so merge `main` in when it resumes.
- Latest commits: `4568b9a` blade wings (1.17.5), `453c8f6` loincloth 3 fit, `5426f65` loincloths own type
  (1.17.4), `be69b80` query.blend corrections (1.17.3).
- Commit messages end with:

      Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
      Claude-Session: https://claude.ai/code/session_016bHhLDVq9BWo6Q3ZdwuYyk

  (a new session uses its own session link). Push straight to `main`; no PRs so far.
- Layout: `addons/` (TIOW Inbox, Finalise), `bridge/` (bridge README, `_library.json` template, TIOW-FTRP patch),
  `squad-builder/` (`src/` + `build_page.py` -> `Squad Builder.html`, `build_index.py`, `prepare_builder.py`,
  `test/` page tests), `library/` (every sidecar, `_sources.csv`, `_hidden.txt`, byte-for-byte incl. CRLF),
  `library-tools/` (plan/build/rename/fold/sync), `kits/` (one folder of build scripts per kit or task),
  `tests/` (Blender checks), `tools/setup_container.sh`, `docs/`.

## Starting a fresh session

1. Attach the repo with push access (`add_repo` gerald422/Kitbash, push) and clone to `/home/claude/kitbash`.
2. Make sure the session is linked to Josh's PC (the remote-devices tools). Stage
   `C:\Users\jpark\Desktop\part_sockets_6.2.0.zip`.
3. `bash /home/claude/kitbash/tools/setup_container.sh` - venv `/home/claude/bpyenv` with bpy 5.1.2, numpy, scipy,
   pillow; Part Sockets, TIOW Inbox and Finalise in the container Blender's add-ons; the old working paths
   (`/home/claude/kits`, `/real`, `/test` ...) that the scripts import from.
4. Stage the library files a task needs (below) and work from `/mnt/user-data/uploads/d/Kitbash Library/...`.

## Josh's PC (through the device tools)

Connected folders: `C:\Users\jpark\Desktop`, `D:\` (and `D:\new cults`), `C:\Users\jpark\AppData\Roaming\Blender
Foundation\Blender\5.1` (and its `extensions\user_default\part_sockets`), `C:\Users\jpark\AppData\Local\TIOW-FTRP`.

| What | Where |
|---|---|
| Library | `D:\Kitbash Library\` |
| Maker downloads | `D:\new cults\` |
| Bridge folder | `C:\Users\jpark\Desktop\TIOW Blender bridge\` (`tiow_inbox.py`, `README.txt`, `_library.json`, `old-<version>\`) |
| Page | `...\TIOW Blender bridge\Squad Builder\` (`Squad Builder.html`, `README.txt`, `build_index.py`, `prepare_builder.py`, `Prepare Squad Builder.bat`) |
| Blender add-ons | `C:\Users\jpark\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\` (`tiow_inbox.py`, `kitbash_finalise.py`) |
| Josh's working blends | `Desktop\query.blend` (his correction file), `Desktop\Operation Marine\*.blend` (large: base_jumpack.blend 191 MB) |
| Mechadendrite assets | `Desktop\tubes, pipes, chains\` |

**Installed now (md5, first 8):** TIOW Inbox 1.17.5 `50f7c9f3` (bridge + Blender add-ons), bridge README
`60bbaf0e`, page `54d32ecb`, page README `f7cb2f49`, `build_index.py` `72ed280c`, `prepare_builder.py` `47521b31`,
`_builder\index.json` `e5187e45` (3,451 parts), `_sources.csv` `43974530`, `_hidden.txt` `36e23889`,
Finalise 0.3.3. Josh restarts Blender after an add-on change.

## How the work is done

- **Staging:** `device_stage_files` copies into `/mnt/user-data/uploads/<d | Desktop | new cults ...>/...`. At most
  7 folder levels below a connected folder: for deeper files, `tar czf` them (device_bash) into a connected folder
  (e.g. `D:\Kitbash Library\_backups\<task-date>\`) and stage the archive. Large blends: stage only when needed.
- **Disk:** the container allowance is ~44 GB. On "no space left on device" delete your own old outputs (test
  `.blend1` copies, renders), never Josh's files.
- **Delivering:** write the files under `/mnt/user-data/outputs/<task-date>/...`; first check on the PC that the
  files you will replace still have the md5 you based the work on (Josh edits `_hidden.txt` from the page);
  back up (`_backups\<task-date>\` in the library, `old-<version>\` in the bridge folder); `mkdir` new folders with
  device_bash; `device_commit_files`; md5-check every file on the PC.
- **The page index:** update `_builder\index.json` in place so Josh needn't run Prepare: changed parts get
  `build_index.part_data(new sidecar)` (fits, sockets, exact, adaptor); new parts come from
  `build_index.build(minilib)` (a folder with their files and a `_sources.csv`), merged in with their previews;
  write it back compact (`separators=(",", ":")`, it round-trips byte-identically).
- **Josh's corrections in a blend** (`kits/corrections/query-*`): list the parts (`list_src.py`), rebuild the same
  model with TIOW in the container and compare each part to his relative to the torso (`rebuild.py`), so TIOW's own
  rock/settle/base rise isn't mistaken for his moves; then save with TIOW's `correct_socket` / `correct_part`
  (`both=False`, `folder=False`, `correct.py`) and rebuild again to confirm 0.00 mm.
- **Tests: a subset only** - the parts a change can affect, a few Blender models (`tests/<task>/t_*.py`, run with
  `/home/claude/bpyenv/bin/python t.py -- args`) and the page tests for the steps touched
  (`squad-builder/test/t_*_step.js` against a served test library: `_builder/index.json` staged from the PC, the
  previews it needs, `_hidden.txt`).
- After each task: commit + push, add an entry to `docs/project-notes.md` (top of the dated list), copy it to the
  Project doc `claude/part-sockets-tiow-integration.md`.

## Josh's standing rules

- STLs never go in the repo; sidecars yes. No mesh-derived caches (npz, bin, previews) either.
- Test only a subset of the parts a change affects; don't re-run every suite (usage).
- Never write TIOW's `config.json`.
- Delete only your own temp files or files Josh approves; deletes on the PC need `device_request_delete_permission`.
- Stage each delivery under a new path and md5-check it on the PC.
- Never `pkill -f`.
- Bionic legs are on hold: don't deliver 1.18 or Finalise 0.3.2.
- Ask clarifying questions before heavy work when that saves effort; ask Josh to save smaller files rather than
  copying huge blends.
- Renegade chapter: no aquilas, purity seals or scrolls (the hidden list; sculpted-in aquilas get added by path).
- Keep usage low: Josh is on a usage budget.

## TIOW Inbox versions since 1.17

- 1.17 squads from the page (model + socket per request); 1.17.1 the page writes into `<library>\_builder\inbox`;
  1.17.2 bases rise to the feet, Save Correction (Fix the Part -> fit + `exact`; Fix the Socket -> host socket,
  `tiow_corrected`).
- 1.17.3 a corrected socket is trusted: belt bits on it aren't rocked, only settled.
- 1.17.4 `Loincloths` type, the only one on Belt Front; belt bits on Hip R/L and Belt Back.
- 1.17.5 `Wings` bring their connector (`Wing Mounts`): the wing's sidecar `adaptor` (library path) goes on the
  pack's `Wing Mount R/L`, the wing hangs from the connector's `Wing R/L`; a request for a socket the model hasn't
  got yet keeps its side.

## Open items (oldest first)

- Captain with Jump Pack belt plates: Josh to review; mirrored copies for the other hip; his chest plate and cape.
- Mechadendrite tails and mechadendrites (spec in the notes; assets in `Desktop\tubes, pipes, chains\`); the TN Mk6
  Universal pack now has `Mechadendrite L/R` sockets from Josh.
- BBoosty and CyberBrush accessories without fits; Plasma Incinerator 3A/3B by eye.
- Bionic legs: waiting for Josh's plug example; `bionic-1.18` needs `main` merged in.
- Which Chaplain / Techmarine "hip armour" files Josh meant.
- Loincloths: offered to give the other banded loincloths (Marta May 1-8, Jul 1-6, Ghostrider 1-2, Thicc 1) the
  same tuck as May 3 (Fix the Part, Whole Folder per set) - waiting for Josh. TN Librarian Buckle and Bottle had
  only a Belt Front fit and no longer place - ask whether the buckle counts as a front piece.
- query.blend: TN Mk5 Helmet 10 sits 0.82 mm off its fit; Josh didn't mention it, left alone.
- Wings: only the TN Mk6 Universal has Wing Mounts (Josh's choice); the other Techmarine connectors (Cables,
  Exhaust, Pivot Base, Semi-Sphere, Sphere, Sideways joints) and Malal3D's own JumpPackCore aren't in the library.
