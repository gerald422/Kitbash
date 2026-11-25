"""Re-fix the Turtle Ninja / Redwarden legs (Josh, Nov 25; notes 142): one TN torso and Redwarden, each stood by its
upright as TIOW stands it, with Legs 1A movable on the torso's Waist.

    BL kits/seat/make_legs_redo_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME
    BL kits/seat/batch.py -- build SPEC_OUT.json --then kits/seat/legs_floor.py
  BL = blender --background --factory-startup --python

Why: his TN legs change (notes 130-132) turns Legs 1A 18.5 deg against the torso (5 forward, 9.7 sideways, 14.5 twist;
Redwarden 19.0), so the legs and the base under them lean about 11 deg where Mar Fil's stand flat (notes 141).
Each legs piece starts at its written seat (his change). His new move is that torso's Waist socket (half "socket").
The TN move is then carried to every other TN torso; Redwarden's stays its own (Josh: Redwarden separate).

Each column also has its spacer, Arm 2B R, guide and pad (the left side mirrored), Helmet 1 and Back Pack 1, all locked,
and a flat floor (legs_floor.py) under its legs, at their lowest point, to judge the base by.
The first column is Torso 2 as written, all locked: the target."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import geom as G, batch as B, make_torso_batch as MT

TORSOS = ["Turtle Ninja - Heresy/Mk2-6 Builder/Mk2/Chests/TN Mk2 - Upper A1",       # where his TN change was made (notes 130)
          "Redwarden - Tacticus/Techmarine Conversion Kit/Chests/Redwarden Techmarine - Prime Techmarine Torso (Flat Bottom)"]


def column(tid, pre, rel, live):
    out = []
    sh = next((s for s in B.sidecar(MT.LIB, rel).get("sockets") or [] if s["type"] == "Shoulder R"), None)
    if sh and (sh.get("props") or {}).get("kb_connectors"):
        col = MT.column(tid, pre, None, locked=True); col[0]["pose"]["shift_from"] = [rel, "Shoulder R"]; out += col
    for sock, pid, ref_obj, prel, c, joint in MT.PIECES:
        e = {"id": "%s_%s" % (tid, pid), "role": "check", "name": "%s%s" % (pre, ref_obj.split(" - ")[-1]), "rel": prel,
             "parent": tid, "on": sock, "pose": {"fit": sock}}
        if sock == "Waist" and live:
            e.update(role="part", joint=joint, write={"host": tid, "socket": "Waist", "half": "socket", "redo": True},
                     note="starts at its written seat (your TN legs change); move it so the legs sit right AND stand flat on the floor")
        out.append(e)
    return out


def main(A):
    spec_out, blend_out, name = A[0], A[1], A[2]
    objs = [{"id": "ref", "role": "host", "name": "REFERENCE Torso 2 (locked)", "rel": MT.T2, "pose": {"place": True}, "at": [0, 0, 0]}]
    objs += column("ref", "REF ", MT.T2, live=False)
    for k, rel in enumerate(TORSOS, 1):
        tid = "t%d" % k; short = os.path.basename(rel); old = MT.sockets(rel)
        host = {"id": tid, "role": "host", "name": short, "rel": rel, "at": [MT.GAP * k, 0, 0],
                "pose": {"matrix": G.flat16(MT.upright(rel))}}      # stood as TIOW stands it (notes 141)
        F = MT.upright_mirror(rel, old)
        if F is not None: host["mirror_frame"] = G.flat16(F)
        objs += [host] + column(tid, short.split(" - ")[-1][:30] + " ", rel, live=True)
    spec = {"name": name, "stage": "2 (the Waist on TN / Redwarden torsos, redone)", "out": blend_out, "sources": MT.SRC,
            "about": "Move each torso's legs so they sit right on the torso and stand flat on the floor, as on Torso 2 (left, locked). The TN move is carried to every TN torso; Redwarden's stays its own.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
