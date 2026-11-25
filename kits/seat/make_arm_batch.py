"""Stage 3 (arms on the spacer: depth and turn): one batch of right arms, each on the spacer on Torso 2 (notes 137).

    BL kits/seat/make_arm_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME ARM_REL [ARM_REL ...]
  BL = blender --background --factory-startup --python

Each column is Torso 2 (locked, as written), the spacer on its Shoulder R socket (locked; the left side its mirror),
Helmet 1, Back Pack 1 and Legs 1A on their fits, and the arm on the spacer: the part Josh moves (depth and turn). Its
mirror shows live on the left. The write is the arm's Shoulder R fit (half "fit", Torso 2's socket is known-good) and
its mirrored fit in the L variant where the arm has one.

Where an arm starts: its old Shoulder R fit (from before the spacer) on Torso 2's old socket, carried by the change
Josh made to Arm 2B R in stage 1 (old pose -> his pose on the spacer, both in Torso 2's own coordinates). Arms of the
same kit and shoulder sculpt sat the same way before the spacer, so the same change is the best start; Josh fixes
the depth and the turn. The first column is Torso 2 with Arm 2B R, guide and pad as written, all locked: the target.

The pads are not shown on the arms being fixed: each arm's Pad R socket is still the old frame until stage 4."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import geom as G, batch as B, make_torso_batch as MT

STAGE1 = os.path.join(MT.LIB, "_backups", "batch write 2026-11-24 1723", "before", "lib")     # before the spacer (notes 122)


def old(rel, key, typ):
    d = json.load(open(os.path.join(STAGE1, rel + ".sockets.json"), encoding="utf-8-sig"))
    return G.M4(d["fits"][typ]) if key == "fit" else G.M4(next(s["matrix"] for s in d["sockets"] if s["type"] == typ))


def main(A):
    spec_out, blend_out, name, arms = A[0], A[1], A[2], A[3:]
    S2 = MT.sockets(MT.T2); S_old = old(MT.T2, "socket", "Shoulder R")
    now_2b = S2["Shoulder R"] @ G.M4(B.sidecar(MT.LIB, MT.ARM)["fits"]["Shoulder R"])
    delta = now_2b @ np.linalg.inv(S_old @ old(MT.ARM, "fit", "Shoulder R"))          # Josh's stage 1 change to Arm 2B R
    log = ["Josh's Arm 2B R change in stage 1: %.2f mm %.1f deg (Torso 2 own coordinates)" % tuple(G.off(delta, np.eye(4)))]
    objs = [{"id": "ref", "role": "host", "name": "REFERENCE Torso 2 (locked)", "rel": MT.T2, "pose": {"place": True}, "at": [0, 0, 0]}]
    objs += MT.column("ref", "REF ", None, locked=True)
    checks = lambda tid, pre: [{"id": "%s_%s" % (tid, pid), "role": "check", "name": pre + ref_obj.split(" - ")[-1], "rel": prel,
                                "parent": tid, "on": sock, "pose": {"fit": sock}} for sock, pid, ref_obj, prel, c, joint in MT.PIECES]
    objs += checks("ref", "REF ")
    for k, rel in enumerate(arms, 1):
        tid = "a%d" % k; short = os.path.basename(rel).replace("MarFil ", ""); sc = B.sidecar(MT.LIB, rel)
        at = np.eye(4); at[:3, 3] = [MT.GAP * (k % MT.PER_ROW), 0, -MT.ROW_GAP * (k // MT.PER_ROW)]
        F_old = (sc.get("fits") or {}).get("Shoulder R")
        if F_old is None: log.append("%-34s left out: no old Shoulder R fit to start from" % short); continue
        start = delta @ S_old @ G.M4(F_old)
        log.append("%-34s starts %.2f mm %.1f deg from its old seat%s" % (short, *G.off(start, S_old @ G.M4(F_old)),
                   "; mirrored in %s" % B._mirror_variant(sc)["name"] if B._mirror_variant(sc) else ""))
        objs += [{"id": tid, "role": "host", "name": "Torso 2 for " + short, "rel": MT.T2, "pose": {"place": True}, "at": list(at[:3, 3])},
                 {"id": tid + "_spacer", "role": "check", "name": short + " Spacer", "connector": {"kind": "spacer", "from": "arms", "obj": "Springles Spacer"},
                  "parent": tid, "on": "Shoulder R", "mirror": True, "pose": {"at_pivot": True, "shift_from": [MT.T2, "Shoulder R"]}},
                 {"id": tid + "_arm", "role": "part", "name": short, "rel": rel, "parent": tid + "_spacer", "on": "arm seat", "mirror": True,
                  "joint": "Arm on the spacer", "pose": {"matrix": G.flat16(at @ start)},
                  "note": "starts at its old seat moved the way you moved Arm 2B R onto the spacer; set its depth on the spacer and its turn",
                  "write": {"host": tid, "socket": "Shoulder R", "mirror": "Shoulder L", "half": "fit"}}]
        objs += checks(tid, short + " ")
    spec = {"name": name, "stage": "3 (arms on the spacer)", "out": blend_out, "sources": MT.SRC,
            "about": "Each column: move the arm on the spacer (its depth into the spacer and its turn) so it sits right on Torso 2. Its mirror shows on the left. Each placement is that arm's fit. The left column is Torso 2 with Arm 2B R as written, locked.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
