"""Stage 4 (arms' sockets), Nov 25: the four reference hand fits from Josh's placements on Arm 2A R.

    BL kits/seat/ref_hand_fits.py -- [--check]
  BL = blender --background --factory-startup --python

Josh placed Chain Sword 1 R, 2 R and 3 R (one per wrist angle) and Shield R on Arm 2A R in the reference file
(`Kitbash reference NEW (starter 2026-11-19).blend`; their cuts `Assault weapon wrist 1/2/3/shield`). Each weapon's
Hand R fit = Arm 2A R's Hand R socket (kept as the frame) to that weapon, from his placement, so TIOW (socket . fit)
puts each one where he did. The fits are marked exact (merge keeps them); Arm 2A R's Hand R socket is marked Josh's
(props.kb_josh) and stays the locked reference in the stage 4 batches. Backs up first (library and repo mirror)."""
import os, sys, json, time, shutil
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B
from kb import sidecar as SC

LIB = "D:/Kitbash Library"; A2 = "Mar Fil - Tacticus/AssaultMarines-V2/"
ARM = A2 + "Arms/MarFil Assault - Arm 2A R"
REF = "~/Desktop/mar fil connectors/Kitbash reference NEW (starter 2026-11-19).blend"
WEAPONS = [  # library path, object in the reference file (placed on Arm 2A R)
    (A2 + "Melee/MarFil Assault - Chain Sword 1 R", "MarFil Assault - Chain Sword 1 R.001", "wrist 1"),
    (A2 + "Melee/MarFil Assault - Chain Sword 2 R", "MarFil Assault - Chain Sword 2 R", "wrist 2"),
    (A2 + "Melee/MarFil Assault - Chain Sword 3 R", "MarFil Assault - Chain Sword 3 R", "wrist 3"),
    (None, "MarFil Assault - Shield R", "wrist shield")]


def find(rel_tail):
    import glob
    hits = glob.glob(os.path.join(LIB, A2, "**", rel_tail + ".stl"), recursive=True)
    assert len(hits) == 1, (rel_tail, hits); return os.path.relpath(hits[0], LIB).replace("\\", "/")[:-4]


def main(A):
    check = "--check" in A
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(REF), load_ui=False); bpy.context.view_layer.update()
    ob = bpy.data.objects
    W_arm = B.own_world(ob["MarFil Assault - Arm 2A R"], ARM, LIB, B.sidecar(LIB, ARM))
    arm, arm_style = SC.load(os.path.join(LIB, ARM + SC.SUFFIX))
    S = G.M4(next(s["matrix"] for s in arm["sockets"] if s["type"] == "Hand R"))
    out = {}
    for rel, name, cut in WEAPONS:
        rel = rel or find("MarFil Assault - Shield R")
        W = B.own_world(ob[name], rel, LIB, B.sidecar(LIB, rel))
        F = np.linalg.inv(S) @ np.linalg.inv(W_arm) @ W
        d, st = SC.load(os.path.join(LIB, rel + SC.SUFFIX)); old = (d.get("fits") or {}).get("Hand R")
        print("%-38s %s; %s" % (os.path.basename(rel), cut, "new" if old is None else "%.2f mm %.1f deg from the old fit" % tuple(G.off(G.M4(old), F))))
        if "Hand R" in (d.get("exact") or []): raise SystemExit("%s: Hand R already exact (Josh's): not changed" % rel)
        d.setdefault("fits", {})["Hand R"] = G.flat16(F)
        d["exact"] = sorted(set(d.get("exact") or []) | {"Hand R"})
        if isinstance(d.get("notes"), dict) or d.get("notes") is None:
            d.setdefault("notes", {})["Hand R"] = "Josh's placement on Arm 2A R (reference file, cut 'Assault weapon %s'), against 2A R's Hand R socket (kits/seat/ref_hand_fits.py, %s)" % (cut, time.strftime("%Y-%m-%d"))
        out[rel] = (d, st)
    s = next(s for s in arm["sockets"] if s["type"] == "Hand R")
    s.setdefault("props", {})["kb_josh"] = "reference: Josh's four hand placements (ref_hand_fits.py)"
    out[ARM] = (arm, arm_style)
    if check: print("--check: nothing written"); return
    bk = os.path.join(LIB, "_backups", "ref hand fits %s" % time.strftime("%Y-%m-%d %H%M"), "before", "lib")
    for rel in out:
        src = B.lp(os.path.join(LIB, rel + SC.SUFFIX)); dst = B.lp(os.path.join(bk, rel + SC.SUFFIX))
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
    for rel, (d, st) in out.items():
        src = B.lp(os.path.join(LIB, rel + SC.SUFFIX)); repo = B.lp(os.path.join(REPO, "library", rel + SC.SUFFIX))
        same = os.path.exists(repo) and open(repo, "rb").read() == open(src, "rb").read()
        data = SC.save(src, d, st)
        if same: open(repo, "wb").write(data)
        else: print("NOTE: repo copy of %s differed; left alone" % rel)
    print("written %d sidecars; backup %s" % (len(out), bk))
    # check: TIOW's socket . fit against Josh's placement
    for rel, name, cut in WEAPONS:
        rel = rel or find("MarFil Assault - Shield R")
        F = G.M4(SC.load(os.path.join(LIB, rel + SC.SUFFIX))[0]["fits"]["Hand R"])
        W = B.own_world(ob[name], rel, LIB, B.sidecar(LIB, rel))
        print("check %-30s %.4f mm %.3f deg" % (os.path.basename(rel), *G.off(W_arm @ S @ F, W)))


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
