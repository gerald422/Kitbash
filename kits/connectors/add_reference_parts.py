"""Add parts for Josh to cut into the reference file (docs/PLAN.md, "The reference file"), after a backup copy. Each new
part comes with the Mar Fil part it sits against (so the reader takes its joint from that part), in groups set apart
along X, each at the library's position as a starting point only: Josh sets the pose by eye and cuts. Nothing in the
file is changed or moved; only objects are added, to the "Mar Fil" collection, named as their library file.

    blender --background --factory-startup --python kits/connectors/add_reference_parts.py -- [REF.blend] [--lib LIB]"""
import bpy, os, sys, json, shutil, time
import numpy as np
from mathutils import Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO)
from kb import origin as OG

A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
LIB = A[A.index("--lib") + 1] if "--lib" in A else "D:/Kitbash Library"
REF = next((a for a in A if a.endswith(".blend")), os.path.expanduser("~/Desktop/mar fil connectors/Kitbash reference.blend"))
MF = "Mar Fil - Tacticus/"
TORSO = MF + "AssaultMarines-V2/Chests/MarFil Assault - Torso 2"
ARM = MF + "AssaultMarines-V2/Arms/MarFil Assault - Arm 2B R"
SWORD = MF + "AssaultMarines-V2/Melee/MarFil Assault - Chain Sword 1 R"
PAD = MF + "AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1"
JUMP = MF + "AssaultMarines-V2/Jump Packs/MarFil Assault - Jump Pack 1"
PACK = MF + "Intercessors-V2/Intercessors-Bits/Backpacks/MarFil Intercessor - Back Pack 1"
# a group: (x offset, torso, [(part, its host: "torso" or an earlier part's key, host socket, fit names)])
# the key of a part is its index in the list
GROUPS = [
    (80, TORSO, [(MF + "Intercessors-V2/Intercessors-Bits/Arms/MarFil Intercessor - Arm 1 R", "torso", "Shoulder R", ("Shoulder R", "Shoulder")),
                 (SWORD, 0, "Hand R", ("Hand R", "Hand")), (PAD, 0, "Pad R", ("Pad R", "Pad"))]),
    (160, TORSO, [(MF + "VeteranBladeSquad/Arms/MarFil Bladeguard - Arm 10A", "torso", "Shoulder R", ("Shoulder R", "Shoulder")),
                  (SWORD, 0, "Hand R", ("Hand R", "Hand")), (PAD, 0, "Pad R", ("Pad R", "Pad"))]),
    (240, TORSO, [(ARM, "torso", "Shoulder R", ("Shoulder R", "Shoulder")),
                  (MF + "Intercessors-V2/Intercessors-Bits/Shoulder Pads/MarFil Intercessor - Shoulder Pad 1", 0, "Pad R", ("Pad R", "Pad")),
                  (MF + "VeteranBladeSquad/Axes/Melee/MarFil Bladeguard - Axe 1A #97", 0, "Hand R", ("Hand R", "Hand")),
                  (MF + "VeteranSquad/Weapons/Pistols/MarFil Veteran - Combi Weapon 4A", 0, "Hand R", ("Hand R", "Hand")),
                  (MF + "AssaultMarines-V2/Melee/Shields/MarFil Assault - Shield R", 0, "Hand R", ("Hand R", "Hand", "Shield R", "Shield"))]),
    (-80, TORSO, [(MF + "CaptainWithJumpPack/Jump Packs/MarFil Captainwithjumppack - Jump Pack", "torso", "Back", ("Back",))]),
    (-160, MF + "ChaplainWithJumpPack/Chests/MarFil Jump Chaplain - Chest Chaplain", [(JUMP, "torso", "Back", ("Back",))]),
    (-240, MF + "Techmarine/Chests/MarFil Techmarine - Chest", [(PACK, "torso", "Back", ("Back",))]),
]
MX = np.diag([-1.0, 1, 1, 1])
M = lambda a: np.array(a, float).reshape(4, 4)


def sidecar(rel): return OG.with_joint_fit(json.load(open(LIB + "/" + rel + ".sockets.json", encoding="utf-8-sig")))
def sock(sc, t): return next((M(s["matrix"]) for s in sc.get("sockets") or [] if s.get("type") == t), None)
def fit(sc, names): f = sc.get("fits") or {}; return next((M(f[n]) for n in names if n in f), None)


def main():
    if not os.path.exists(REF): sys.exit("STOP: %s not found" % REF)
    bak = os.path.join(os.path.dirname(REF), "Kitbash reference (before additions %s).blend" % time.strftime("%Y-%m-%d %H%M"))
    shutil.copy2(REF, bak); print("backup: %s" % bak)
    bpy.ops.wm.open_mainfile(filepath=REF, load_ui=False)
    coll = bpy.data.collections.get("Mar Fil")
    if coll is None: sys.exit("STOP: no 'Mar Fil' collection in the file; nothing written")
    def load(rel, W):
        bpy.ops.wm.stl_import(filepath=LIB + "/" + rel + ".stl")
        o = bpy.context.selected_objects[0]; o.name = os.path.basename(rel); o.data.name = o.name
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o); o.matrix_world = Matrix(np.asarray(W).tolist()); return o
    report = []
    # the left shin pad: the right one mirrored about the marine's middle (the torso's waist), for Josh to set by eye
    T = bpy.data.objects.get("MarFil Assault - Torso 2"); R = bpy.data.objects.get("MarFil Assault - Shin Pad 1")
    Sw = sock(sidecar(TORSO), "Waist")
    if T is None or R is None or Sw is None: report.append("left shin pad: torso, shin pad or the torso's Waist socket not found; not added")
    else:
        Jw = np.array(T.matrix_world) @ Sw; o = load(MF + "AssaultMarines-V2/Knee Pads/MarFil Assault - Shin Pad 1", Jw @ MX @ np.linalg.inv(Jw) @ np.array(R.matrix_world))
        report.append("left shin pad: %s, the right one mirrored (negative X scale), on Legs 1A's left shin" % o.name)
    for x, torso, parts in GROUPS:
        Wt = np.eye(4); Wt[0, 3] = x; tsc = sidecar(torso); load(torso, Wt); placed = {"torso": (Wt, tsc, torso)}
        for i, (rel, host, st, fits) in enumerate(parts):
            Hw, hs, hrel = placed[host]; sc = sidecar(rel); S, F = sock(hs, st), fit(sc, fits)
            if S is None and hrel != torso: S = sock(sidecar(ARM if host != "torso" else TORSO), st)       # no socket on it: the reference's as a start
            if S is None: S = sock(sidecar(TORSO), st)
            if F is None: F = np.eye(4); report.append("%s: no %s fit in the library, put at its host's %s socket as it is" % (os.path.basename(rel), "/".join(fits), st))
            W = Hw @ S @ F if S is not None else Hw; o = load(rel, W); placed[i] = (W, sc, rel)
        report.append("x %+4d: %s" % (x, ", ".join(os.path.basename(p[0]) for p in [(torso,)] + parts)))
    bpy.ops.wm.save_as_mainfile(filepath=REF)
    print("saved %s" % REF)
    for r in report: print("  " + r)


if __name__ == "__main__":
    main()
