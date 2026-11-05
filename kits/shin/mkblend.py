"""Shin pads by eye on Marta legs: May 2026 Legs 1 (May pad 1 R + L), Jul 2026 Legs 1 (Jul pad 1 L), Jan 2026 Legs 1 (Jan pad 1 R),
legs in torso coordinates side by side (locked), each pad as its own file mesh with a rough start in front of its shin;
the pad objects' origins at their centre in the pad's own frame (X across, Y to the knee, Z out)."""
import bpy, sys, json, numpy as np
from mathutils import Matrix
sys.path.insert(0, "/home/claude/kitbash/kits/plates"); sys.path.insert(0, "/home/claude/test")
from hol_common import stl, tf; import rend
from legs_frame import legs as legs_geo
U = "/mnt/user-data/uploads/d/Kitbash Library/"; OUT = sys.argv[sys.argv.index("--") + 1]
P = json.load(open("/home/claude/work/shin/pads.json")); K = {k.split("/")[-1]: k for k in json.load(open("/home/claude/work/shin/proposed.json"))}
SET = [("Marta May 2026 - Legs 1", [("Marta May 2026 - Shin Pad 1 R", "R"), ("Marta May 2026 - Shin Pad 1 L", "L")]),
       ("Marta Jul 2026 - Legs 1", [("Marta Jul 2026 - Shin Pad 1 L", "L")]),
       ("Marta Jan 2026 - Legs 1", [("Marta Jan 2026 - Shin Pad 1 R", "R")])]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def ob(name, V, T, M, col, lock=False):
    me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], T.tolist()); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.matrix_world = Matrix(M.tolist()); o.color = col
    o.hide_select = lock; return o
def pad_frame(V):
    c = (V.min(0) + V.max(0)) / 2; w, E = np.linalg.eigh(np.cov((V - V.mean(0)).T))
    z = E[:, 0] * np.sign(E[2, 0] or 1); y = E[:, 2] * (np.sign(E[1, 2]) or 1); y = y - z * (y @ z); y /= np.linalg.norm(y); x = np.cross(y, z)
    F = np.eye(4); F[:3, 0], F[:3, 1], F[:3, 2], F[:3, 3] = x, y, z, c; return F
obs = []
for i, (ln, pads) in enumerate(SET):
    _, V, T, M = legs_geo(K[ln], U); Off = np.eye(4); Off[0, 3] = 45 * i; W = Off @ M
    obs.append(ob(ln + " (locked)", V, T, W, rend.GREY, lock=True)); Pw = tf(W, V); z0, z1 = Pw[:, 2].min(), Pw[:, 2].max()
    for pn, s in pads:
        PV, PT = stl(U + P[pn] + ".stl"); F = pad_frame(PV); Fi = np.linalg.inv(F); PVl = tf(Fi, PV)      # pad mesh in its own frame
        sx = 1 if s == "R" else -1
        sel = Pw[((Pw[:, 0] - 45 * i) * sx > 1.0) & (Pw[:, 2] > z0 + 0.25 * (z1 - z0)) & (Pw[:, 2] < z0 + 0.45 * (z1 - z0))]
        fwd = np.array([0.25 * sx, 1.0, 0]); fwd /= np.linalg.norm(fwd); front = sel[np.argmax(sel @ fwd)]
        G = np.eye(4); G[:3, 2] = fwd; G[:3, 1] = [0, 0, 1.0]; G[:3, 0] = np.cross(G[:3, 1], G[:3, 2])
        G[:3, 3] = front + fwd * (np.ptp(PVl[:, 2]) / 2 + 0.4) + np.array([0, 0, 0.0])
        obs.append(ob("%s - %s (place)" % (ln.replace("Marta ", ""), pn.replace("Marta ", "")), PVl, PT, G, rend.BLUE))
print([o.name for o in obs])
bpy.context.view_layer.update()
cam = rend.setup(sc, 700); f = rend.render(sc, "/home/claude/work/shin", "blend", obs, {"front": (0.3, 1, 0.15), "side": (1, 0.2, 0.1)}, [o.color for o in obs])
bpy.data.objects.remove(bpy.data.objects["cam"])
for a in bpy.data.screens:
    for ar in a.areas:
        if ar.type == 'VIEW_3D':
            for s_ in ar.spaces:
                if s_.type == 'VIEW_3D': s_.shading.color_type = 'OBJECT'; s_.clip_end = 10000
sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = 'MILLIMETERS'
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("saved", f)
