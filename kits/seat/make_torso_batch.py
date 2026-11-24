"""Stage 2 (torsos' sockets): write the batch spec for a set of torsos (docs/PLAN.md, the stage table).

    BL kits/seat/make_torso_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME TORSO_REL [TORSO_REL ...]
  BL = blender --background --factory-startup --python

Each torso gets its own column (80 mm apart, rows of 8 stacked 120 mm down), next to the reference column (Torso 2, all locked, as Josh placed it):
- the spacer on Shoulder R (Josh moves it; its move is the socket), with Arm 2B R on it by its written fit and the
  guide and Shoulder Pad 1 on the arm by theirs (locked, riding); the left side is the live mirror;
- the reference helmet, backpack and legs on Neck, Back and Waist (Josh moves them; each move is that socket), each
  carried by its pose on Torso 2 in the reference file (Josh's own placements; the library's old fits differ:
  helmet 1.2 deg, Legs 1A 9.5 deg).
Where each piece starts (Claude's seat, the skill kitbash-seat-by-shape): Josh's Torso 2 cut surface for that socket
(the reference file's 'Assault Torso Shoulder / neck / back / waist' cuts) fitted onto the torso by trimmed ICP, and
Torso 2's socket carried by that fit. Only the cut's shape is matched (CLAUDE.md). The torso's own old socket is used
instead if the cut doesn't land, and every start is reported.

The reference column's pieces are written once (batch 02; later batches skip a socket that is already Josh's) ("both" halves: Torso 2's socket as it is and each piece's fit = Josh's
reference placement), so every torso's sockets are judged with the fits that will be in the library."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
from mathutils.bvhtree import BVHTree
import geom as G, batch as B
import kb.sidecar as SC

LIB = "D:/Kitbash Library"
MF = "Mar Fil - Tacticus/"
T2 = MF + "AssaultMarines-V2/Chests/MarFil Assault - Torso 2"
ARM = MF + "AssaultMarines-V2/Arms/MarFil Assault - Arm 2B R"
PAD = MF + "AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1"
SRC = {"ref": "~/Desktop/mar fil connectors/Kitbash reference NEW (starter 2026-11-19).blend",
       "seat": "~/Desktop/mar fil connectors/Pauldron adapter - seat and cut (2026-11-23).blend",
       "arms": "~/Desktop/Operation Marine/arms.blend"}
PIECES = [   # socket, id, ref object, library path, cut on Torso 2 in the reference file, joint
    ("Neck", "head", "MarFil Intercessor - Helmet 1", MF + "Intercessors-V2/Intercessors-Bits/Helmets-Heads/Heads/MarFil Intercessor - Helmet 1", "Assault Torso neck", "Helmet on the Neck"),
    ("Back", "pack", "MarFil Intercessor - Back Pack 1", MF + "Intercessors-V2/Intercessors-Bits/Backpacks/MarFil Intercessor - Back Pack 1", "Assault torso back", "Backpack on the Back"),
    ("Waist", "legs", "MarFil Assault - Legs 1A", MF + "AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A", "Assault Torso waist", "Legs on the Waist")]
SHOULDER_CUT = "Assault Torso Shoulder"
GAP = 80.0                  # mm between columns
PER_ROW, ROW_GAP = 8, 120.0   # columns per row (the reference takes the first slot), mm between rows
GUIDE = {"kind": "guide", "from": "seat", "obj": "Adapter - MarFil Assault - Arm 2B R"}


def sockets(rel): return {s["type"]: G.M4(s["matrix"]) for s in B.sidecar(LIB, rel).get("sockets") or []}


def carried(cut_P, rel, S_t2, old):
    """Torso 2's socket carried onto torso rel by fitting the cut points (Torso 2 own coordinates) onto it"""
    T = B.stl_tris(LIB, rel, B.sidecar(LIB, rel)); V = T.reshape(-1, 3)
    b = BVHTree.FromPolygons([tuple(v) for v in V], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(T))])
    R, t, rms = G.icp(b, cut_P, np.eye(3), np.zeros(3), iters=40, keep=0.8, lim=3.0)
    if rms >= 0.3: return (old, "the cut didn't land (rms %.1f mm): the torso's old socket" % min(rms, 9)) if old is not None else (None, "the cut didn't land (rms %.1f mm) and there is no old socket: left out" % min(rms, 9))
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; S = M @ S_t2
    return S, "cut fitted, rms %.3f mm; %s from the old socket" % (rms, "n/a" if old is None else "%.2f mm %.1f deg" % tuple(G.off(S, old)))


def main(A):
    spec_out, blend_out, name, torsos = A[0], A[1], A[2], A[3:]
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(SRC["ref"]), load_ui=False); bpy.context.view_layer.update()
    Wt = B.own_world(bpy.data.objects["MarFil Assault - Torso 2"], T2, LIB, B.sidecar(LIB, T2)); Ti = np.linalg.inv(Wt)
    cut = {}
    for c in [SHOULDER_CUT] + [p[4] for p in PIECES]:
        P = G.verts_world(bpy.data.objects[c]) @ Ti[:3, :3].T + Ti[:3, 3]
        cut[c] = P[np.linspace(0, len(P) - 1, min(len(P), 1500)).astype(int)]
    S2 = sockets(T2); objs = []; log = []
    # the reference column: Torso 2 and Josh's pieces, locked
    objs.append({"id": "ref", "role": "host", "name": "REFERENCE Torso 2 (locked)", "rel": T2, "pose": {"from": "ref", "obj": "MarFil Assault - Torso 2"}, "at": [0, 0, 0]})
    objs += column("ref", "REF ", None, locked=True)
    josh = {s["type"] for s in B.sidecar(LIB, T2).get("sockets") or [] if SC.protected(s)}
    for sock, pid, ref_obj, rel, c, joint in PIECES:
        o = {"id": "ref_" + pid, "role": "check", "name": "REF %s" % ref_obj.split(" - ")[-1], "rel": rel, "parent": "ref", "on": sock,
             "pose": {"from": "ref", "obj": ref_obj, "relative_to": ["MarFil Assault - Torso 2", "ref"]}}
        if sock not in josh: o["write"] = {"host": "ref", "socket": sock, "half": "both"}   # written once (batch 02, notes 124)
        objs.append(o)
    for k, rel in enumerate(torsos, 1):
        tid = "t%d" % k; short = os.path.basename(rel).replace("MarFil ", ""); old = sockets(rel)
        mine = [{"id": tid, "role": "host", "name": short, "rel": rel, "pose": {"place": True},
                 "at": [GAP * (k % PER_ROW), 0, -ROW_GAP * (k // PER_ROW)]}]
        S, why = carried(cut[SHOULDER_CUT], rel, S2["Shoulder R"], old.get("Shoulder R")); log.append("%-28s Shoulder R  %s" % (short, why))
        if S is not None: mine += column(tid, short + " ", S)
        for sock, pid, ref_obj, prel, c, joint in PIECES:
            S, why = carried(cut[c], rel, S2[sock], old.get(sock)); log.append("%-28s %-11s %s" % (short, sock, why))
            if S is None: continue
            mine.append({"id": "%s_%s" % (tid, pid), "role": "part", "name": "%s %s" % (short, ref_obj.split(" - ")[-1]), "rel": prel,
                         "parent": tid, "on": sock, "on_matrix": G.flat16(S), "joint": joint,
                         "pose": {"from": "ref", "obj": ref_obj, "relative_to": ["MarFil Assault - Torso 2", "ref"], "carry": ["ref", sock]},
                         "note": "starts where your Torso 2 %s cut fits this torso; move it to where it belongs on this torso" % sock,
                         "write": {"host": tid, "socket": sock, "half": "socket"}})
        if len(mine) > 1: objs += mine
        else: log.append("%-28s left out: nothing lands on it" % short)
    spec = {"name": name, "stage": "2 (torsos' sockets)", "out": blend_out, "sources": SRC,
            "about": "Each torso: move the spacer (the arm, guide and pad ride on it), the helmet, the backpack and the legs to where they belong on that torso. Each move is that torso's socket. The left column is the reference (Torso 2 as you placed it), locked.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("SPEC", spec_out, flush=True)


def column(tid, pre, S_sh, locked=False):
    """the spacer on Shoulder R with Arm 2B R, the guide and Shoulder Pad 1 riding on it"""
    sp = {"id": tid + "_spacer", "role": "check" if locked else "part", "name": pre + "Spacer", "connector": {"kind": "spacer", "from": "arms", "obj": "Springles Spacer"},
          "parent": tid, "on": "Shoulder R", "mirror": True, "joint": "Spacer on Shoulder R",
          "pose": {"at_pivot": True, "shift_from": [T2, "Shoulder R"]}}
    if S_sh is not None:
        sp.update(on_matrix=G.flat16(S_sh), note="starts where your Torso 2 shoulder cut fits this torso; move it (the arm rides) to where the arm belongs",
                  write={"host": tid, "socket": "Shoulder R", "mirror": "Shoulder L", "half": "socket"})
    return [sp,
            {"id": tid + "_arm", "role": "check", "name": pre + "Arm 2B R", "rel": ARM, "parent": tid + "_spacer", "on": "arm seat", "mirror": True, "pose": {"fit": "Shoulder R"}},
            {"id": tid + "_guide", "role": "check", "name": pre + "Guide", "connector": GUIDE, "parent": tid + "_arm", "on": "Pad R", "mirror": True, "pose": {"at_pivot": True}},
            {"id": tid + "_pad", "role": "check", "name": pre + "Shoulder Pad 1", "rel": PAD, "parent": tid + "_guide", "on": "crown", "mirror": True, "pose": {"fit": "Pad R"}}]


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    finally: sys.stdout.flush(); os._exit(0)
