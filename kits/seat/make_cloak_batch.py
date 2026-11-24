"""Stage 2 (the Cloak socket): the cloaks placed on Torso 2 by Josh, one column each (notes 134).

    BL kits/seat/make_cloak_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME CLOAK_REL [CLOAK_REL ...]
  BL = blender --background --factory-startup --python

Each column is a locked Torso 2 with its reference pieces on their written fits: the spacer, Arm 2B R, the guide and
Shoulder Pad 1 (the left side mirrored), Helmet 1, Back Pack 1 and Legs 1A. So the cloak's clearance shows. On top of
that is one cloak (a part) on Torso 2's new Cloak socket, which is Torso 2's Back frame.

Cloaks lie anywhere in their own files: no shared frame, some maybe turned. A cloak starts only moved, its
bounding-box centre put behind the back (CLOAK_AT, Torso 2 own coordinates); Josh places it by eye. The write gives
every cloak its Cloak fit (half "fit"), and the first one also writes Torso 2's Cloak socket (half "both"; the Back
frame). Later batches carry the socket to every other torso by its Back socket. Mar Fil's Captain cape was rejected by
Josh (Nov 24) and is not used."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B, make_torso_batch as MT

CLOAK_AT = np.array([0.0, -10.0, 33.0])          # behind Torso 2's back, at shoulder-blade height (own coordinates)


def main(A):
    spec_out, blend_out, name, cloaks = A[0], A[1], A[2], A[3:]
    S2 = MT.sockets(MT.T2); objs = []
    for k, rel in enumerate(cloaks):
        tid = "c%d" % (k + 1); short = os.path.basename(rel)
        objs.append({"id": tid, "role": "host", "name": "Torso 2 for " + short, "rel": MT.T2, "pose": {"place": True},
                     "at": [MT.GAP * (k % MT.PER_ROW), 0, -MT.ROW_GAP * (k // MT.PER_ROW)]})
        objs += MT.column(tid, "%s " % tid, None, locked=True)
        for sock, pid, ref_obj, prel, c, joint in MT.PIECES:
            objs.append({"id": "%s_%s" % (tid, pid), "role": "check", "name": "%s %s" % (tid, ref_obj.split(" - ")[-1]), "rel": prel,
                         "parent": tid, "on": sock, "pose": {"fit": sock}})
        V = B.stl_tris(MT.LIB, rel, B.sidecar(MT.LIB, rel)).reshape(-1, 3); W = np.eye(4); W[:3, 3] = CLOAK_AT - (V.min(0) + V.max(0)) / 2
        objs.append({"id": tid + "_cloak", "role": "part", "name": short, "rel": rel, "parent": tid, "on": "Cloak",
                     "on_matrix": G.flat16(S2["Back"]), "joint": "Cloak on the Cloak socket",
                     "pose": {"matrix": G.flat16(np.array([[1, 0, 0, MT.GAP * (k % MT.PER_ROW)], [0, 1, 0, 0], [0, 0, 1, -MT.ROW_GAP * (k // MT.PER_ROW)], [0, 0, 0, 1]]) @ W)},
                     "note": "a rough start (only moved behind the back): place the cloak on Torso 2 by eye",
                     "write": {"host": tid, "socket": "Cloak", "half": "both" if k == 0 else "fit"}})
    spec = {"name": name, "stage": "2 (the Cloak socket)", "out": blend_out, "sources": MT.SRC,
            "about": "Each column: place the cloak on Torso 2 where it belongs (everything else is locked). Each placement is that cloak's fit on the Cloak socket.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("%d cloaks" % len(cloaks)); print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
