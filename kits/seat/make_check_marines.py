"""Random check marines from approved parts only, placed from the library alone (socket . fit, the way TIOW does it), to
look for roll-backs (Josh, Nov 25; notes 140).

    BL kits/seat/make_check_marines.py -- SPEC_OUT.json BATCH_OUT.blend N [--seed S]
  then  BL kits/seat/batch.py -- build SPEC_OUT.json
  BL = blender --background --factory-startup --python

Approved = written from Josh's batches: a torso socket marked props.kb_josh, a part fit in "exact". Each marine:
- a torso with Josh's sockets (makers taken in turn: Mar Fil, Turtle Ninja, Redwarden), stood on its waist;
- the spacer on its Shoulder R, and a right arm with an exact Shoulder R fit on it; the left side is its mirror;
- the guide and pad only on an arm whose Pad R socket is Josh's (so far only Arm 2B R);
- Helmet 1, Back Pack 1 and Legs 1A (the reference pieces; the only approved ones);
- a cloak: circles ones on Cloak, no-circles ones on Cloak Plain (notes 138).
Everything is a locked check piece; nothing is written."""
import os, sys, json, glob, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import geom as G, batch as B, make_torso_batch as MT

LIB = MT.LIB


def josh_sockets(rel): return {s["type"] for s in B.sidecar(LIB, rel).get("sockets") or [] if (s.get("props") or {}).get("kb_josh")}
def exact(rel): return set(B.sidecar(LIB, rel).get("exact") or [])


def approved():
    hidden = set(l.strip().replace("\\", "/")[:-4] for l in open(os.path.join(LIB, "_hidden.txt"), encoding="utf-8-sig") if l.strip().endswith(".stl"))
    torsos = set()
    for f in glob.glob(os.path.join(HERE, "batches", "02-*.json")):
        s = json.load(open(f, encoding="utf-8")); torsos |= {o["rel"] for o in s["objects"] if o["role"] == "host"}
    need = {"Shoulder R", "Neck", "Back", "Waist", "Cloak", "Cloak Plain"}
    torsos = sorted(r for r in torsos if r not in hidden and need <= josh_sockets(r))
    arms = sorted(os.path.relpath(p, LIB).replace("\\", "/")[:-len(".sockets.json")]
                  for p in glob.glob(os.path.join(LIB, "Mar Fil - Tacticus", "*", "Arms", "*.sockets.json")) + glob.glob(os.path.join(LIB, "Mar Fil - Tacticus", "*", "*", "Arms", "*.sockets.json")))
    arms = [a for a in arms if "Shoulder R" in exact(a) and a not in hidden]
    cloaks = []
    for f in glob.glob(os.path.join(HERE, "batches", "02-cloaks-on-torso-2.json")):
        s = json.load(open(f, encoding="utf-8")); cloaks += [o["rel"] for o in s["objects"] if o["id"].endswith("_cloak")]
    cloaks = [(c, "Cloak Plain" if "Cloak Plain" in exact(c) else "Cloak") for c in cloaks if c not in hidden and "Cloak" in exact(c)]
    return torsos, arms, cloaks


def main(A):
    spec_out, blend_out, n = A[0], A[1], int(A[2])
    seed = int(B.opt(A, "--seed", random.randrange(10000))); rng = random.Random(seed)
    torsos, arms, cloaks = approved()
    print("approved: %d torsos, %d right arms, %d cloaks; seed %d" % (len(torsos), len(arms), len(cloaks), seed))
    makers = [[t for t in torsos if t.startswith(m)] for m in ("Mar Fil", "Turtle Ninja", "Redwarden")]
    S2 = MT.sockets(MT.T2); objs, log = [], []
    for k in range(n):
        pool = [m for m in makers if m][k % len([m for m in makers if m])]
        rel = rng.choice(pool); pool.remove(rel)                              # each torso once
        arm = MT.ARM if k == 0 else rng.choice(arms); cl, csock = rng.choice(cloaks)
        tid = "m%d" % (k + 1); old = MT.sockets(rel); short = os.path.basename(rel)
        host = {"id": tid, "role": "host", "name": "%d %s" % (k + 1, short), "rel": rel, "at": [MT.GAP * k, 0, 0],
                "pose": {"matrix": G.flat16(S2["Waist"] @ np.linalg.inv(old["Waist"]))}}
        F = MT.mirror_frame(old, old["Waist"])
        if F is not None: host["mirror_frame"] = G.flat16(F)
        col = MT.column(tid, "%d " % (k + 1), None, locked=True); col[0]["pose"]["shift_from"] = [rel, "Shoulder R"]
        col[1]["rel"] = arm; col[1]["name"] = "%d %s" % (k + 1, os.path.basename(arm))
        if "Pad R" not in josh_sockets(arm): col = col[:2]                    # no approved pad seat on this arm yet
        objs += [host] + col
        objs += [{"id": "%s_%s" % (tid, pid), "role": "check", "name": "%d %s" % (k + 1, ref_obj.split(" - ")[-1]), "rel": prel,
                  "parent": tid, "on": sock, "pose": {"fit": sock}} for sock, pid, ref_obj, prel, c, joint in MT.PIECES]
        objs.append({"id": tid + "_cloak", "role": "check", "name": "%d %s" % (k + 1, os.path.basename(cl)), "rel": cl,
                     "parent": tid, "on": csock, "pose": {"fit": csock}})
        log.append("%d  %-55s arm %-28s cloak %s (%s)%s" % (k + 1, short[-55:], os.path.basename(arm)[-28:], os.path.basename(cl), csock,
                                                           "" if len(col) > 2 else "  [no pad: the arm's Pad R isn't approved yet]"))
    spec = {"name": "Check marines (seed %d)" % seed, "stage": "check (no write)", "out": blend_out, "sources": MT.SRC,
            "about": "Random marines from approved parts only, each placed from the library (socket . fit) as TIOW does. Look for anything out of place: nothing here is written.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
