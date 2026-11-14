"""Preview sheet (notes 098): parts with the connectors kb.connect found on them, in colour, and where the library
puts the same joint, as a red outline of the connector. Where they agree the colour sits inside the red ring.
One render (Workbench), each part turned so its connectors face the camera; left parts shown mirrored (as the
library treats them). Read-only on the library.

    BL  connector_preview.py LIBRARY OUT.png SPEC [SPEC ...] --parts "REL;REL;..." [--cols 3] [--cell 26]
        SPEC = CONNECTOR.stl::SOURCE_REL::fit | socket:TYPE   (as connector_search_check.py)
  BL = blender --background --factory-startup --python connector_preview.py --
"""
import sys, os, json
import numpy as np
import bpy
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
from connector_try import sock
from kb import connect as C, geo
import masters as MS

COLS = [(0.10, 0.40, 1.00), (1.00, 0.50, 0.00), (0.10, 0.75, 0.20), (0.60, 0.20, 0.90), (0.0, 0.7, 0.7)]
GREY, RED, INK = (0.78, 0.78, 0.76), (0.95, 0.0, 0.0), (0.05, 0.05, 0.05)


def mesh_obj(name, V, F, col):
    me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], F.tolist()); me.update()
    ob = bpy.data.objects.new(name, me); ob.color = col + (1.0,); bpy.context.scene.collection.objects.link(ob); return ob


def tri_obj(name, tri, col):
    return mesh_obj(name, tri.reshape(-1, 3), np.arange(len(tri) * 3).reshape(-1, 3), col)


def ring(tri, r=0.05):
    """the open connector's edge (edges used by one triangle) as thin tubes, (V, F)"""
    V, inv = np.unique(tri.reshape(-1, 3).round(5), axis=0, return_inverse=True); T = inv.reshape(-1, 3)
    E = np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1); u, c = np.unique(E, axis=0, return_counts=True); B = u[c == 1]
    out_v, out_f = [], []
    for k, (a, b) in enumerate(B):
        p, q = V[a], V[b]; d = q - p; L = np.linalg.norm(d)
        if L < 1e-9: continue
        d /= L; x = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 1, 0]); x /= np.linalg.norm(x); y = np.cross(d, x)
        o = [r * (np.cos(a_) * x + np.sin(a_) * y) for a_ in (0, 2.094, 4.189)]; n = len(out_v)
        out_v += [p + o[0], p + o[1], p + o[2], q + o[0], q + o[1], q + o[2]]
        out_f += [(n, n + 1, n + 4, n + 3), (n + 1, n + 2, n + 5, n + 4), (n + 2, n, n + 3, n + 5)]
    return np.array(out_v), np.array(out_f)


def outward(tri):
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n = n.sum(0); return n / (np.linalg.norm(n) + 1e-12)


def align(a, b):
    """rotation taking unit a onto unit b"""
    v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else np.diag([1.0, -1, -1])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K / (1 + c)


def text(s, at, size):
    cu = bpy.data.curves.new("t", "FONT"); cu.body = s; cu.size = size; cu.align_x = "CENTER"
    ob = bpy.data.objects.new("t", cu); ob.location = at; ob.color = INK + (1.0,); bpy.context.scene.collection.objects.link(ob)


def run(lib, out, specs, A):
    opt = lambda n, d=None: A[A.index(n) + 1] if n in A else d
    rels = opt("--parts").split(";"); cols = int(opt("--cols", 3)); cell = float(opt("--cell", 26))
    # never bpy.ops.wm.read_factory_settings here: on the PC it drops the extensions' Python packages (notes 098)
    for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    cons, ref = [], {}
    for sp in specs:
        conn, src, mode = sp.split("::"); con = C.Connector.from_stl(conn, os.path.splitext(os.path.basename(conn))[0]); cons.append(con)
        s0 = json.load(open(lib + "/" + src + ".sockets.json", encoding="utf-8-sig")); typ = mode.split(":")[1] if mode.startswith("socket") else None
        ref[con.name] = (typ, MS.right_fit(s0)[0], sock(s0, typ) if typ else None)
    for k, rel in enumerate(rels):
        s1 = json.load(open(lib + "/" + rel + ".sockets.json", encoding="utf-8-sig")); F0, left = MS.right_fit(s1)
        surf = C.Surface(C.soup(lib + "/" + rel + ".stl", s1.get("scale", 1.0)), mirror=left); found = C.find_all(cons, surf)
        pieces, dirs, lines = [], [], []
        for j, con in enumerate(cons):
            typ, Fsrc, Ssrc = ref[con.name]; f = found[con.name]
            M0 = (sock(s1, typ) @ np.linalg.inv(Ssrc) if sock(s1, typ) is not None else None) if typ else (np.linalg.inv(F0) @ Fsrc if F0 is not None else None)
            note = f["level"] + (" ambiguous" if f.get("ambiguous") else "")
            if f["level"] != "none":
                T = con.surf.tri @ f["M"][:3, :3].T + f["M"][:3, 3]; nrm = outward(T); pieces.append(("found", T + 0.03 * nrm, COLS[j % len(COLS)])); dirs.append(nrm)
            if M0 is not None:
                T0 = con.surf.tri @ M0[:3, :3].T + M0[:3, 3]; nrm0 = outward(T0); pieces.append(("lib", T0 + 0.06 * nrm0, RED))
                if f["level"] != "none":
                    d = float(np.linalg.norm((f["M"][:3, :3] @ con.c + f["M"][:3, 3]) - (M0[:3, :3] @ con.c + M0[:3, 3])))
                    note += ", %.1f mm from library" % d
                else: dirs.append(nrm0)
            elif f["level"] != "none": note += ", library has none"
            lines.append("%s: %s" % (con.name.replace("_file", ""), note))
        # turn the part so its connectors face the camera (+Z), middle of its box at the cell's middle
        v = np.sum(dirs, 0) if dirs else np.array([0, 0, 1.0]); v = v / (np.linalg.norm(v) + 1e-12); R = align(v, np.array([0, 0, 1.0]))
        mid = (surf.tri.reshape(-1, 3).min(0) + surf.tri.reshape(-1, 3).max(0)) / 2
        ext = np.ptp(((surf.tri.reshape(-1, 3) - mid) @ R.T)[:, :2], 0).max(); s = 0.72 * cell / ext   # each part fills its tile
        cx, cy = (k % cols) * cell, -(k // cols) * cell * 1.15
        place = lambda T: (T - mid) @ R.T * s + np.array([cx, cy, 0])
        tri_obj("part%d" % k, place(surf.tri), GREY)
        for kind, T, col in pieces:
            if kind == "found": tri_obj("c%d" % k, place(T), col)
            else: rv, rf = ring(place(T), cell * 0.006); ob = mesh_obj("lib%d" % k, rv, rf, col); ob.show_in_front = True
        name = os.path.basename(rel).replace("MarFil ", "") + (" (left, mirrored)" if left else "") + "   [x%.1f]" % s
        text(name, (cx, cy - cell * 0.47, 40), cell * 0.045)
        for i, ln in enumerate(lines): text(ln, (cx, cy - cell * 0.47 - (i + 1) * cell * 0.05, 40), cell * 0.036)
        print("%d %s: %s" % (k + 1, name, " | ".join(lines)), flush=True)
    rows = (len(rels) + cols - 1) // cols
    key = "   ".join("%s = %s" % (c.name.replace("_file", ""), ["blue", "orange", "green", "purple", "teal"][j % 5]) for j, c in enumerate(cons)) + "   red ring = where the library puts it"
    text(key, ((cols - 1) * cell / 2, cell * 0.62, 40), cell * 0.04)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; w, h = cols * cell, rows * cell * 1.15 + cell * 0.3
    cam.data.ortho_scale = max(w, h * 1.5) * 1.02; cam.location = ((cols - 1) * cell / 2, -(rows - 1) * cell * 1.15 / 2 + cell * 0.05, 200)
    cam.data.clip_end = 1000
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "OBJECT"
    sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = "WORLD"
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1); sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = 2400, 1600; sc.render.filepath = out; sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True); print("wrote", out)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]; k = 2
    while k < len(A) and not A[k].startswith("--"): k += 1
    run(A[0], A[1], A[2:k], A[k:])
