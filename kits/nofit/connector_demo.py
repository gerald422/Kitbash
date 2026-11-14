"""Demo (notes 098): whole marines snapped with the connector method next to the same marines snapped with the
library's fits. One torso (its sockets, as TIOW uses them); the legs, both arms and both pauldrons placed by
  library: part placed at socket @ the part's own fit (the arm's own Pad socket for the pauldron)
  new:     the fit / Pad socket taken from where kb.connect found the connector (the reference's fit moved by the
           match); pauldrons keep their own fit on that Pad socket until the pad-inside connector exists.
Parts the library can't snap (no fit), and parts the search finds no connector on, are left out and said so;
each new placement says how far it is from the library's (median over the part). Colours in the new row: green =
sure, yellow = look, red = none (left at the library's placement, or left out). Read-only on the library.

    BL  connector_demo.py LIBRARY OUT.png --arm-conns DISC.stl,PADSPOT.stl,OTHER.stl.. --legs-conn WAIST.stl
        --arm-ref ARM_REL --legs-ref LEGS_REL --model "LABEL|TORSO|LEGS|ARM_R|ARM_L|PAD_R|PAD_L" [--model ...]
  BL = blender --background --factory-startup --python connector_demo.py --
  (arm connectors: the first is the shoulder disc, the second the pad spot, any others are searched with them)
"""
import sys, os, json
import numpy as np
import bpy
from mathutils import Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
from connector_try import sock
from kb import connect as C
MX = np.diag([-1.0, 1, 1, 1])
LEVEL = {"sure": (0.25, 0.75, 0.30), "look": (0.95, 0.80, 0.20), "none": (0.90, 0.30, 0.25)}
GREY, LIBC, INK = (0.75, 0.75, 0.73), (0.70, 0.72, 0.80), (0.05, 0.05, 0.05)


def side(lib, rel): return json.load(open(lib + "/" + rel + ".sockets.json", encoding="utf-8-sig"))
def fit(sc, name):
    f = (sc.get("fits") or {}).get(name); return None if f is None else np.array(f).reshape(4, 4)
def socket(sc, name):
    return next((np.array(s["matrix"]).reshape(4, 4) for s in sc.get("sockets", []) if s["type"] == name), None)


def add(name, tri, M, col):
    """the part's triangles placed by M (4x4), as one object coloured col"""
    V = tri.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]; F = np.arange(len(V)).reshape(-1, 3)
    if np.linalg.det(M[:3, :3]) < 0: F = F[:, [0, 2, 1]]
    me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], F.tolist()); me.update()
    ob = bpy.data.objects.new(name, me); ob.color = col + (1.0,); bpy.context.scene.collection.objects.link(ob)


def moved(tri, M1, M2):
    """how far the part is from where the library puts it: median over its corners, mm"""
    V = tri.reshape(-1, 3)[::7]; a = V @ M1[:3, :3].T + M1[:3, 3]; b = V @ M2[:3, :3].T + M2[:3, 3]
    return ", %.1f mm from library" % float(np.median(np.linalg.norm(a - b, axis=1)))


def text(s, at, size, rot):
    cu = bpy.data.curves.new("t", "FONT"); cu.body = s; cu.size = size; cu.align_x = "CENTER"
    ob = bpy.data.objects.new("t", cu); ob.matrix_world = Matrix.Translation(at) @ rot.to_4x4(); ob.color = INK + (1.0,)
    bpy.context.scene.collection.objects.link(ob)


def run(lib, out, A):
    opt = lambda n: A[A.index(n) + 1] if n in A else None
    models = [A[i + 1].split("|") for i, a in enumerate(A) if a == "--model"]
    arm_cons = [C.Connector.from_stl(p, "arm%d" % i) for i, p in enumerate(opt("--arm-conns").split(","))]
    legs_con = C.Connector.from_stl(opt("--legs-conn"), "waist")
    aref, lref = side(lib, opt("--arm-ref")), side(lib, opt("--legs-ref"))
    F_disc, S_pad = fit(aref, "Shoulder R"), socket(aref, "Pad R"); F_waist = fit(lref, "Waist")
    for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)        # never read_factory_settings (notes 098)
    sc = bpy.context.scene
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    d = np.array([-0.35, -1.0, -0.22]); d /= np.linalg.norm(d)                 # the camera looks at the front, from the right, above
    z = -d; x = np.cross([0, 0, 1.0], z); x /= np.linalg.norm(x); y = np.cross(z, x); rot = Matrix(np.c_[x, y, z].tolist())
    gap, row = 62.0, 80.0; notes = []
    for k, (label, torso, legs, arm_r, arm_l, pad_r, pad_l) in enumerate(models):
        off = np.eye(4); off[0, 3] = -k * gap                                # the camera faces the front: -X is to its right
        st = side(lib, torso); T = C.soup(lib + "/" + torso + ".stl", st.get("scale", 1.0)); lines = {"lib": [], "new": []}
        for r, (dz, key) in enumerate(((row, "lib"), (0.0, "new"))):
            O = off.copy(); O[2, 3] = dz; add("torso", T, O, GREY)
        # legs on the torso's Waist
        sl = side(lib, legs); tri = C.soup(lib + "/" + legs + ".stl", sl.get("scale", 1.0)); Sw = socket(st, "Waist")
        O = off.copy(); O[2, 3] = row; Fl = fit(sl, "Waist")
        if Fl is not None: add("legs", tri, O @ Sw @ Fl, LIBC)
        else: lines["lib"].append("legs: no fit (not placed)")
        f = C.find(legs_con, C.Surface(tri)); O = off.copy(); Fn = F_waist @ np.linalg.inv(f["M"])
        if f["level"] != "none":
            add("legs", tri, O @ Sw @ Fn, LEVEL[f["level"]]); lines["new"].append("legs: %s%s" % (f["level"], moved(tri, Sw @ Fl, Sw @ Fn) if Fl is not None else ", library has no fit"))
        else: lines["new"].append("legs: no match (not placed): another waist design")
        # arms on the torso's shoulders, pauldrons on the arms' Pad sockets
        for sd, arm, pad in (("R", arm_r, pad_r), ("L", arm_l, pad_l)):
            sa = side(lib, arm); left = arm.endswith(" L"); tri = C.soup(lib + "/" + arm + ".stl", sa.get("scale", 1.0))
            Ssh = socket(st, "Shoulder " + sd); sp = side(lib, pad); ptri = C.soup(lib + "/" + pad + ".stl", sp.get("scale", 1.0))
            Fp = fit(sp, "Pad " + sd); pmir = False
            if Fp is None: Fp = fit(sp, "Pad R" if sd == "L" else "Pad L"); pmir = True     # a one-sided pad on the other side: mirrored
            P = (lambda Fp_: (MX @ Fp_ if pmir else Fp_))(Fp) if Fp is not None else None
            # library
            O = off.copy(); O[2, 3] = row; Fa = fit(sa, "Shoulder " + sd)
            if Fa is not None:
                A_ = O @ Ssh @ Fa; add("arm", tri, A_, LIBC)
                Sp = socket(sa, "Pad " + sd)
                if Sp is not None and P is not None: add("pad", ptri, A_ @ Sp @ P, LIBC)
                else: lines["lib"].append("pad %s: no Pad socket or fit" % sd)
            else: lines["lib"].append("arm %s: no fit" % sd)
            # new: the arm searched as a right arm (a left one mirrored), as the library does
            found = C.find_all(arm_cons, C.Surface(tri, mirror=left)); fd, fpd = found["arm0"], found["arm1"]
            Fr = F_disc @ np.linalg.inv(fd["M"]); Fa_new = MX @ Fr @ MX if left else Fr
            if fd["level"] == "none":
                lines["new"].append("arm %s: no match (not placed)" % sd); continue
            O = off.copy(); A_ = O @ Ssh @ Fa_new; add("arm", tri, A_, LEVEL[fd["level"]])
            arm_moved = moved(tri, Ssh @ Fa, Ssh @ Fa_new) if Fa is not None else ", library has no fit"
            if fpd["level"] != "none":
                Sr = fpd["M"] @ S_pad; Sp_new = MX @ Sr @ MX if left else Sr; how = fpd["level"]
            else:
                Sp_new = socket(sa, "Pad " + sd); how = "none, library's socket" if Sp_new is not None else "none"
            pad_moved = ""
            if Sp_new is not None and P is not None:
                add("pad", ptri, A_ @ Sp_new @ P, LEVEL[fpd["level"]])
                if Fa is not None and socket(sa, "Pad " + sd) is not None:
                    pad_moved = moved(ptri, Ssh @ Fa @ socket(sa, "Pad " + sd) @ P, Ssh @ Fa_new @ Sp_new @ P)
            lines["new"].append("arm %s: %s%s | pad: %s%s" % (sd, fd["level"], arm_moved, how, pad_moved))
        rows = [("library fits", row, lines["lib"] or ["everything has a fit"]), ("connector method", 0.0, lines["new"])]
        for title, dz, ls in rows:
            base = np.array([-k * gap, 30.0, dz - 4.0])
            text("%s - %s" % (label, title), base, 2.6, rot)
            for i, ln in enumerate(ls): text(ln, base - np.array([0, 0, 3.2 * (i + 1)]), 1.8, rot)
        notes.append("%s | library: %s | new: %s" % (label, "; ".join(lines["lib"]) or "all fitted", "; ".join(lines["new"])))
        print(notes[-1], flush=True)
    span = (len(models) - 1) * gap
    cam.data.type = "ORTHO"; cam.data.ortho_scale = max(span + gap, (row + 80) * 1.5) * 1.05; cam.data.clip_end = 2000
    centre = np.array([-span / 2, 0.0, row / 2 + 8]); cam.matrix_world = Matrix.Translation(centre - d * 400) @ rot.to_4x4()
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "OBJECT"
    sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = "WORLD"
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1); sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = 2400, 1600; sc.render.filepath = out; sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True); print("wrote", out)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    run(A[0], A[1], A[2:])
