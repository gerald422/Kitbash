"""Stage 2 (the Cloak socket on every torso): one batch of torsos, each wearing the cloaks by their written fits
(notes 136, 137).

    BL kits/seat/make_cloak_socket_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME (--from EARLIER_SPEC.json | TORSO_REL ...)
  --from: the torsos (hosts) of an earlier torso batch spec, e.g. 02-tn-torsos-2.json
  BL = blender --background --factory-startup --python

Torso 2's Cloak socket is its Back frame (notes 134-136). Each torso's Cloak socket starts the same way: its own
written Back socket (Josh checked every one in the torso batches). So each cloak starts against the backpack mount
exactly as Josh placed it on Torso 2. The torsos differ in shape, so Josh moves the cloak to sit right on each one;
that move is the torso's Cloak socket (half "socket"), and all 17 cloaks share it.

Each column is the torso stood on its waist (Torso 2's frame), with its written pieces locked so the clearance shows:
the spacer, Arm 2B R, the guide and Shoulder Pad 1 (the left side mirrored), Helmet 1, Back Pack 1 and Legs 1A. On top,
both movable and each in its own collection so Josh can show one at a time (Nov 25; at first the second rode, locked,
on the first):
- CyberBrush Bug Hunters Cloak 1 (circles on the straps): its move is the torso's Cloak socket;
- Marta 49 March 2026 Cloak 2 (no circles): its move is the torso's "Cloak Plain" socket (Josh: the no-circles style
  needs its own socket; notes 138).
The first column is Torso 2 as written, all locked: the target."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import geom as G, batch as B, make_torso_batch as MT

CB = "CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Cloaks/Cloaks/CyberBrush Bug Hunters - Cloak 1"
M49 = "Marta PunkGirl - Tacticus/49 March 2026/Cloaks/Marta 49 March 2026 - Cloak 2"
CIRCLES, PLAIN = "CLOAK 1 - circles on the straps", "CLOAK 2 - no circles"     # a collection each, to show one at a time


def fit(rel, sock): return G.M4(B.sidecar(MT.LIB, rel)["fits"][sock])


def pieces(tid, pre, rel, cloak_on, live):
    """the locked written pieces on torso tid, and the two cloaks: the circles one on cloak_on (a part when live)"""
    out = []
    sh = next((s for s in B.sidecar(MT.LIB, rel).get("sockets") or [] if s["type"] == "Shoulder R"), None)
    if sh and (sh.get("props") or {}).get("kb_connectors"):
        col = MT.column(tid, pre, None, locked=True); col[0]["pose"]["shift_from"] = [rel, "Shoulder R"]; out += col
    for sock, pid, ref_obj, prel, c, joint in MT.PIECES:
        out.append({"id": "%s_%s" % (tid, pid), "role": "check", "name": "%s%s" % (pre, ref_obj.split(" - ")[-1]), "rel": prel,
                    "parent": tid, "on": sock, "pose": {"fit": sock}})
    for cid, rel_c, nm, coll in (("_cloak", CB, "Cloak (circles)", CIRCLES), ("_cloak2", M49, "Cloak (no circles)", PLAIN)):
        cl = {"id": tid + cid, "role": "part" if live else "check", "name": pre + nm, "rel": rel_c, "parent": tid, "on": "Cloak",
              "pose": {"fit": "Cloak"}, "joint": "Cloak on the Cloak socket", "collection": coll + ("" if live else " (reference)")}
        if live:                         # both movable, each its own (Josh, Nov 25); the circles one writes the socket,
            cl.update(on_matrix=G.flat16(cloak_on),          # the other is compared with it at the write
                      note="starts on this torso's backpack socket as on Torso 2; move it to sit right on this torso")
            cl["write"] = {"host": tid, "socket": "Cloak" if cid == "_cloak" else "Cloak Plain", "half": "socket"}   # notes 138
        out.append(cl)
    return out


def main(A):
    spec_out, blend_out, name = A[0], A[1], A[2]; torsos = A[3:]
    if "--from" in A:
        s = json.load(open(A[A.index("--from") + 1], encoding="utf-8"))
        torsos = [o["rel"] for o in s["objects"] if o["role"] == "host" and o["id"] != "ref"]
    S2 = MT.sockets(MT.T2); assert "Cloak" in S2, "Torso 2 has no Cloak socket yet (notes 136)"
    objs = [{"id": "ref", "role": "host", "name": "REFERENCE Torso 2 (locked)", "rel": MT.T2, "pose": {"place": True}, "at": [0, 0, 0]}]
    objs += pieces("ref", "REF ", MT.T2, None, live=False); log = []
    for k, rel in enumerate(torsos, 1):
        tid = "t%d" % k; short = os.path.basename(rel); old = MT.sockets(rel)
        if "Back" not in old or "Waist" not in old: log.append("%-40s left out: no written Back / Waist socket" % short[-40:]); continue
        host = {"id": tid, "role": "host", "name": short, "rel": rel, "at": [MT.GAP * (k % MT.PER_ROW), 0, -MT.ROW_GAP * (k // MT.PER_ROW)],
                "pose": {"matrix": G.flat16(S2["Waist"] @ np.linalg.inv(old["Waist"]))}}      # stood on its waist as Torso 2
        F = MT.mirror_frame(old, old["Waist"])
        if F is not None: host["mirror_frame"] = G.flat16(F)
        objs += [host] + pieces(tid, short.split(" - ")[-1][:30] + " ", rel, old["Back"], live=True)
        log.append("%-40s Cloak starts on its Back socket%s" % (short[-40:], "" if "Cloak" not in old else " (it already had a Cloak socket)"))
    spec = {"name": name, "stage": "2 (the Cloak socket)", "out": blend_out, "sources": MT.SRC,
            "about": "Each torso: move the circles cloak to sit right on that torso (the other cloak rides on it; its collection can be hidden). Each move is that torso's Cloak socket, shared by every cloak. The left column is Torso 2 as written, locked.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("%d torsos" % sum(1 for o in objs if o["role"] == "host" and o["id"] != "ref")); print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
