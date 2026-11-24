"""Stage 2 (torsos' sockets): write the batch spec for a set of torsos (docs/PLAN.md, the stage table).

    BL kits/seat/make_torso_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME TORSO_REL [TORSO_REL ...] [--preset SOCKET=16 numbers]
  --preset: a repeated fix of Josh's (a 4x4 in the socket's axes, row-major, comma separated) put on every piece on
  that socket, shown "pre-set" (e.g. his Turtle Ninja legs change on the Waist, notes 131)
  BL = blender --background --factory-startup --python

Each torso gets its own column (80 mm apart, rows of 8 stacked 120 mm down), stood on its waist as Torso 2 is,
with its mirror plane (mirror_frame), next to the reference column (Torso 2, all locked, as Josh placed it):
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


T2_CENTRE = None                                     # Torso 2's bounding-box centre (own coordinates), set in main


def carried(cut_P, rel, S_t2, old):
    """Torso 2's socket carried onto torso rel by fitting the cut points (Torso 2 own coordinates) onto it. A torso with
    no socket at all starts the fit from the offset of the two bounding-box centres (a file lying elsewhere, e.g. the
    Bike Chaplain's chest, 31 mm down); if the cut still doesn't land, Torso 2's socket moved by that offset is a rough
    start for Josh to place by eye (Nov 24: "Batch, I place by eye")."""
    T = B.stl_tris(LIB, rel, B.sidecar(LIB, rel)); V = T.reshape(-1, 3)
    b = BVHTree.FromPolygons([tuple(v) for v in V], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(T))])
    t0 = np.zeros(3) if old is not None else (V.min(0) + V.max(0)) / 2 - T2_CENTRE
    R, t, rms = G.icp(b, cut_P, np.eye(3), t0, iters=40, keep=0.8, lim=3.0)
    if rms >= 0.3:
        if old is not None: return old, "the cut didn't land (rms %.1f mm): the torso's old socket" % min(rms, 9)
        M0 = np.eye(4); M0[:3, 3] = t0
        return M0 @ S_t2, "the cut didn't land (rms %.1f mm), no old socket: a rough start (Torso 2's, moved %.1f mm), place by eye" % (min(rms, 9), np.linalg.norm(t0))
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; S = M @ S_t2
    return S, "cut fitted, rms %.3f mm; %s from the old socket" % (rms, "n/a" if old is None else "%.2f mm %.1f deg" % tuple(G.off(S, old)))


def main(A):
    pre = {}
    while "--preset" in A:
        k = A.index("--preset"); sock, nums = A[k + 1].split("=", 1); pre[sock] = [float(x) for x in nums.split(",")]
        assert len(pre[sock]) == 16, "--preset needs 16 numbers"; A = A[:k] + A[k + 2:]
    cloak_ref = None
    if "--cloak-ref" in A: k = A.index("--cloak-ref"); cloak_ref = A[k + 1]; A = A[:k] + A[k + 2:]
    spec_out, blend_out, name, torsos = A[0], A[1], A[2], A[3:]
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(SRC["ref"]), load_ui=False); bpy.context.view_layer.update()
    Wt = B.own_world(bpy.data.objects["MarFil Assault - Torso 2"], T2, LIB, B.sidecar(LIB, T2)); Ti = np.linalg.inv(Wt)
    cut = {}
    for c in [SHOULDER_CUT] + [p[4] for p in PIECES]:
        P = G.verts_world(bpy.data.objects[c]) @ Ti[:3, :3].T + Ti[:3, 3]
        cut[c] = P[np.linspace(0, len(P) - 1, min(len(P), 1500)).astype(int)]
    S2 = sockets(T2); objs = []; log = []
    global T2_CENTRE; V2 = B.stl_tris(LIB, T2, B.sidecar(LIB, T2)).reshape(-1, 3); T2_CENTRE = (V2.min(0) + V2.max(0)) / 2
    # the reference column: Torso 2 and Josh's pieces, locked
    objs.append({"id": "ref", "role": "host", "name": "REFERENCE Torso 2 (locked)", "rel": T2, "pose": {"from": "ref", "obj": "MarFil Assault - Torso 2"}, "at": [0, 0, 0]})
    objs += column("ref", "REF ", None, locked=True)
    josh = {s["type"] for s in B.sidecar(LIB, T2).get("sockets") or [] if SC.protected(s)}
    for sock, pid, ref_obj, rel, c, joint in PIECES:
        o = {"id": "ref_" + pid, "role": "check", "name": "REF %s" % ref_obj.split(" - ")[-1], "rel": rel, "parent": "ref", "on": sock,
             "pose": {"from": "ref", "obj": ref_obj, "relative_to": ["MarFil Assault - Torso 2", "ref"]}}
        if sock not in josh: o["write"] = {"host": "ref", "socket": sock, "half": "both"}   # written once (batch 02, notes 124)
        objs.append(o)
    if cloak_ref:                                    # the reference cloak, once (notes 133): Torso 2's Cloak socket starts on its
        objs.append({"id": "ref_cloak", "role": "part", "name": "REF " + os.path.basename(cloak_ref).split(" - ")[-1], "rel": cloak_ref,
                     "parent": "ref", "on": "Cloak", "on_matrix": G.flat16(S2["Back"]), "joint": "Cloak on the Cloak socket",
                     "pose": {"matrix": G.flat16(Wt)},       # Back frame; the cloak starts in its rig frame (Mar Fil's own)
                     "note": "the reference cloak: move it to where it belongs on Torso 2 (its fit); the socket stays Torso 2's Back frame",
                     "write": {"host": "ref", "socket": "Cloak", "half": "both"}})
    for k, rel in enumerate(torsos, 1):
        tid = "t%d" % k; short = os.path.basename(rel).replace("MarFil ", ""); old = sockets(rel)
        starts = {sock: carried(cut[c], rel, S2[sock], old.get(sock)) for sock, pid, ref_obj, prel, c, joint in PIECES}
        Sw = starts["Waist"][0] if starts["Waist"][0] is not None else old.get("Waist")
        host = {"id": tid, "role": "host", "name": short, "rel": rel, "at": [GAP * (k % PER_ROW), 0, -ROW_GAP * (k // PER_ROW)],
                "pose": {"place": True} if Sw is None else {"matrix": G.flat16(Wt @ S2["Waist"] @ np.linalg.inv(Sw))}}   # stood on its waist as Torso 2
        F = mirror_frame(old, Sw)
        if F is not None: host["mirror_frame"] = G.flat16(F)
        mine = [host]
        S, why = carried(cut[SHOULDER_CUT], rel, S2["Shoulder R"], old.get("Shoulder R")); log.append("%-28s Shoulder R  %s" % (short, why))
        if S is not None: mine += column(tid, short + " ", S)
        for sock, pid, ref_obj, prel, c, joint in PIECES:
            S, why = starts[sock]; log.append("%-28s %-11s %s" % (short, sock, why))
            if S is None: continue
            extra = {"preset": pre[sock]} if sock in pre else {}
            mine.append({"id": "%s_%s" % (tid, pid), "role": "part", "name": "%s %s" % (short, ref_obj.split(" - ")[-1]), "rel": prel,
                         "parent": tid, "on": sock, "on_matrix": G.flat16(S), "joint": joint,
                         "pose": {"from": "ref", "obj": ref_obj, "relative_to": ["MarFil Assault - Torso 2", "ref"], "carry": ["ref", sock]},
                         "note": "starts where your Torso 2 %s cut fits this torso; move it to where it belongs on this torso" % sock,
                         "write": {"host": tid, "socket": sock, "half": "socket"}, **extra})
        if len(mine) > 1: objs += mine
        else: log.append("%-28s left out: nothing lands on it" % short)
    spec = {"name": name, "stage": "2 (torsos' sockets)", "out": blend_out, "sources": SRC,
            "about": "Each torso: move the spacer (the arm, guide and pad ride on it), the helmet, the backpack and the legs to where they belong on that torso. Each move is that torso's socket. The left column is the reference (Torso 2 as you placed it), locked.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("SPEC", spec_out, flush=True)


def mirror_frame(old, Sw):
    """the torso's mirror plane, as a frame whose YZ plane it is (own coordinates): the waist's turn, through the middle
    of the old shoulders. Torso files lie every which way (Turtle Ninja: Y up, the plane at z = 6.4), so X = 0 is only
    Mar Fil's. Straight torsos' old shoulders mirror across it to 0.05 mm / 1 deg (Mar Fil: 0.007 mm, = X = 0)."""
    if Sw is None: return None
    F = np.array(Sw, dtype=float).copy()
    if "Shoulder R" in old and "Shoulder L" in old: F[:3, 3] = (old["Shoulder R"][:3, 3] + old["Shoulder L"][:3, 3]) / 2
    return F


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
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
