"""Make the starting reference file for Josh's cuts (docs/PLAN.md, "The reference file"): Mar Fil Torso 2 at the centre
and the Mar Fil parts on it, each imported straight from the library and put where the library places it today. No
cuts: Josh adjusts each pose by eye (that pose is the anchor) and cuts the mating surfaces. Writes a NEW file only.

    blender --background --factory-startup --python kits/connectors/make_reference.py -- [OUT.blend] [--lib LIB]"""
import bpy, os, sys, json
import numpy as np
from mathutils import Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO)
from kb import origin as OG

A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
LIB = A[A.index("--lib") + 1] if "--lib" in A else "D:/Kitbash Library"
OUT = next((a for a in A if a.endswith(".blend")), os.path.expanduser("~/Desktop/mar fil connectors/Kitbash reference.blend"))
MF = "Mar Fil - Tacticus/"
TORSO = MF + "AssaultMarines-V2/Chests/MarFil Assault - Torso 2"
# (library path, host (None = the torso), host socket, the part's fit names, collection)
PARTS = [
    (MF + "AssaultMarines-V2/Arms/MarFil Assault - Arm 2B R", None, "Shoulder R", ("Shoulder R", "Shoulder"), "Mar Fil"),
    (MF + "AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A", None, "Waist", ("Waist",), "Mar Fil"),
    (MF + "VeteranBladeSquad/Heads/MarFil Bladeguard - Helmet 3A", None, "Neck", ("Neck",), "Mar Fil"),
    (MF + "AssaultMarines-V2/Jump Packs/MarFil Assault - Jump Pack 1", None, "Back", ("Back",), "Mar Fil"),
    (MF + "AssaultMarines-V2/Melee/MarFil Assault - Chain Sword 1 R", "Arm 2B R", "Hand R", ("Hand R", "Hand"), "Mar Fil"),
    (MF + "AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1", "Arm 2B R", "Pad R", ("Pad R", "Pad"), "Mar Fil"),
    (MF + "AssaultMarines-V2/Knee Pads/MarFil Assault - Shin Pad 1", "Legs 1A", "Shin R", ("Shin R", "Shin"), "Mar Fil"),
    (MF + "Intercessors-V2/Intercessors-Bits/Backpacks/MarFil Intercessor - Back Pack 1", None, "Back", ("Back",),
     "Mar Fil - backpack (instead of the jump pack: hide one)"),
]
M = lambda a: np.array(a, float).reshape(4, 4)


def sidecar(rel): return OG.with_joint_fit(json.load(open(LIB + "/" + rel + ".sockets.json", encoding="utf-8-sig")))


def sock(sc, t):
    for s in sc.get("sockets") or []:
        if s.get("type") == t: return M(s["matrix"])


def fit(sc, names):
    f = sc.get("fits") or {}
    return next((M(f[n]) for n in names if n in f), None)


def main():
    if os.path.exists(OUT): sys.exit("STOP: %s exists already; nothing written" % OUT)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    colls = {}
    def coll(name):
        if name not in colls: colls[name] = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(colls[name])
        return colls[name]
    def load(rel, W, cname):
        bpy.ops.wm.stl_import(filepath=LIB + "/" + rel + ".stl")
        o = bpy.context.selected_objects[0]; o.name = os.path.basename(rel); o.data.name = o.name
        for c in list(o.users_collection): c.objects.unlink(o)
        coll(cname).objects.link(o); o.matrix_world = Matrix(W.tolist())
        o["kitbash_library"] = rel; o["kitbash_file"] = "the library file as it is: don't apply transforms or edit the mesh"
        return o
    placed = {"torso": (np.eye(4), sidecar(TORSO))}
    load(TORSO, np.eye(4), "Mar Fil")
    report = []
    for rel, host, st, fits, cname in PARTS:
        Hw, hs = placed["torso"] if host is None else placed[host]
        S, sc = sock(hs, st), sidecar(rel); F = fit(sc, fits)
        if S is None or F is None:
            report.append("%s: no %s socket on its host or no %s fit: put at the centre" % (os.path.basename(rel), st, "/".join(fits)))
            W = np.eye(4)
        else:
            W = Hw @ S @ F
        load(rel, W, cname)
        placed[os.path.basename(rel).split(" - ", 1)[1]] = (W, sc)
    for c in ("Cuts", ):
        coll(c)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print("saved %s" % OUT)
    for r in report: print("  !! " + r)


if __name__ == "__main__":
    main()
