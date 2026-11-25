"""The no-circles cloaks' own socket, "Cloak Plain" (Josh, Nov 25: "Yes needs its own socket"; notes 138).

    BL kits/seat/cloak_plain.py -- D_BATCH.blend [--check]
  BL = blender --background --factory-startup --python

Cloaks come in two styles that Josh places differently on the TN torsos. CyberBrush's have circles on the straps;
Marta's don't. One Cloak socket can't hold both moves, so:
- the circles cloaks stay on "Cloak";
- the no-circles cloaks (Marta) also get a "Cloak Plain" fit, the same matrix as their written Cloak fit. Their Cloak
  fit stays: a written fix is never changed. The Cloak joint (stage 6) lists "Cloak Plain" first, byFit, so a Marta
  cloak lands there.
- Every torso already written gets its Cloak Plain socket:
  - Torso 2 and the 34 Mar Fil torsos: = their Cloak socket. There Josh approved both styles on the same socket.
  - The 17 TN torsos of batch 2: = Cloak . inv(D1) . D2. D1 and D2 are Josh's circles and no-circles moves on Mk7
    Torso Jump Pack A9, read from D_BATCH, where they were applied unchanged (t1_cloak, t1_cloak2 of TN torsos 3 c).
Later cloak batches write both sockets themselves (the no-circles cloak's move -> "Cloak Plain")."""
import os, sys, json, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B, make_torso_batch as MT
from kb import sidecar as SC

LIB = MT.LIB
PLAIN = ["Marta PunkGirl - Tacticus/49 March 2026/Cloaks/Marta 49 March 2026 - Cloak %d" % i for i in range(1, 8)] + [
    "Marta PunkGirl - Tacticus/Bits Death Watch Pt2/Cloaks/Marta Deathwatch 2 - Cloak",
    "Marta PunkGirl - Tacticus/SW Bits 10 October 2024/10 October 2024/wolf cloak/Cloaks/Marta Space Wolves - Cloak 1"] + [
    "Marta PunkGirl - Tacticus/SALE files August 2025/Pagan TORSO and BACK PACK and cloak/Cloaks/Marta Aug 2025 - Cloak %d" % i for i in (3, 4, 5)]


def hosts(spec):
    s = json.load(open(os.path.join(HERE, "batches", spec), encoding="utf-8"))
    return [o["rel"] for o in s["objects"] if o["role"] == "host" and o["id"] != "ref"]


def main(A):
    blend, check = A[0], "--check" in A
    bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    inf = lambda o: np.linalg.inv(B.own(by[o["kb_parent"]]) @ G.M4(o["kb_on_frame"])) @ np.array(o.matrix_world)
    D1, D2 = inf(by["t1_cloak"]), inf(by["t1_cloak2"])
    print("D1 %.3f mm %.2f deg, D2 %.3f mm %.2f deg" % (*G.off(D1, np.eye(4)), *G.off(D2, np.eye(4))))
    tag = "Josh's Cloak Plain socket (kits/seat/cloak_plain.py, %s; notes 138)" % time.strftime("%Y-%m-%d")
    props = {"tiow_from": tag, "kb_josh": "Cloak Plain (Nov 25)", "kb_connectors": []}
    work = {}                                                     # rel -> (old data, style, new part)
    tn2 = set(hosts("02-cloaks-tn-2.json"))
    for rel in [MT.T2] + hosts("02-cloaks-marfil.json") + hosts("02-cloaks-marfil-hidden.json") + sorted(tn2):
        d, style = SC.load(os.path.join(LIB, rel + SC.SUFFIX))
        C = next(G.M4(s["matrix"]) for s in d["sockets"] if s["type"] == "Cloak")
        M = C @ np.linalg.inv(D1) @ D2 if rel in tn2 else C
        work[rel] = (d, style, {"sockets": [B._socket(d.get("sockets"), "Cloak Plain", M, props, d.get("part") or os.path.basename(rel))]})
    for rel in PLAIN:
        d, style = SC.load(os.path.join(LIB, rel + SC.SUFFIX))
        work[rel] = (d, style, {"fits": {"Cloak Plain": d["fits"]["Cloak"]}, "exact": ["Cloak Plain"], "notes": {"Cloak Plain": tag}})
    out = {}
    for rel, (d, style, n) in work.items():
        if "Cloak Plain" in [s["type"] for s in d.get("sockets") or []] or "Cloak Plain" in (d.get("fits") or {}):
            raise SystemExit("%s already has Cloak Plain: nothing written" % rel)
        merged, kept = SC.merge(n, d)
        if kept: raise SystemExit("%s: protected, not written: %s" % (rel, kept))
        out[rel] = merged
    print("%d torsos get the socket (%d TN batch 2, moved by D1^-1 D2), %d cloaks the fit" % (len(out) - len(PLAIN), len(tn2), len(PLAIN)))
    if check: print("--check: nothing written"); return
    bk = os.path.join(LIB, "_backups", "cloak plain %s" % time.strftime("%Y-%m-%d %H%M"), "before", "lib")
    for rel in out:
        dst = os.path.join(bk, rel + SC.SUFFIX); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(open(os.path.join(LIB, rel + SC.SUFFIX), "rb").read())
    for rel, d in out.items():
        src = os.path.join(LIB, rel + SC.SUFFIX); rp = os.path.join(REPO, "library", rel + SC.SUFFIX)
        same = os.path.exists(rp) and open(rp, "rb").read() == open(src, "rb").read()
        data = SC.save(src, d, work[rel][1])
        if same: open(rp, "wb").write(data)
        else: print("NOTE: the repo copy of %s differed, left alone" % rel)
    bad = 0                                                       # read back
    for rel in out:
        d = SC.load(os.path.join(LIB, rel + SC.SUFFIX))[0]
        if rel in PLAIN: bad += d["fits"]["Cloak Plain"] != d["fits"]["Cloak"]
        else:
            C = next(G.M4(s["matrix"]) for s in d["sockets"] if s["type"] == "Cloak")
            P = next(G.M4(s["matrix"]) for s in d["sockets"] if s["type"] == "Cloak Plain")
            bad += sum(G.off(P, C @ np.linalg.inv(D1) @ D2 if rel in tn2 else C)) > 1e-4
    print("written %d sidecars, old copies in %s; read back: %d wrong" % (len(out), bk, bad), flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
