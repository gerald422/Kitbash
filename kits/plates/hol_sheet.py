"""Contact sheet: every fitted part on the left hip plate of Assault Legs 4A, seen from the left side (and front).
python hol_sheet.py -- FITS_JSON OUT_PNG [names filter]"""
import bpy, sys, json, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/kitbash/kits/plates"); sys.path.insert(0, "/home/claude/test")
from hol_common import *; import rend
from PIL import Image, ImageDraw
a = sys.argv[sys.argv.index("--") + 1:]; FITS = json.load(open(a[0])); OUT = a[1]; FILT = a[2] if len(a) > 2 else ""
legs = json.load(open(LIB + AM + "Legs(JumpPack)/Legs/MarFil Assault - Legs 4A.sockets.json"))
SPL = M16([s for s in legs["sockets"] if s["type"] == "Plate L"][0]["matrix"]); FP = M16(plate["fits"]["Plate L"])
WP = SPL @ FP; WH = WP @ SPH
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; cam = rend.setup(sc, 300)
def ob(name, V, T, M, col):
    me = bpy.data.meshes.new(name); me.from_pydata(tf(M, V).tolist(), [], T.tolist()); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.color = col; return o
LV, LT = stl(U + AM + "Legs(JumpPack)/Legs/MarFil Assault - Legs 4A.stl")
ob("legs", LV, LT, np.eye(4), rend.GREY); ob("plate", PV, PT, WP, rend.BLUE)
tiles = []
for rel, r in FITS.items():
    name = rel.split("\\")[-1][:-4]
    if FILT and FILT not in name: continue
    V, T = stl(U + rel.replace("\\", "/")); o = ob(name, V, T, WH @ M16(r["fit"]), rend.ORANGE)
    pts = np.vstack([tf(WH @ M16(r["fit"]), V), tf(WP, PV)]); c = (pts.min(0) + pts.max(0)) / 2; size = np.linalg.norm(pts.max(0) - pts.min(0))
    row = []
    for vn, d in (("side", (-1, 0.25, 0.15)), ("front", (-0.35, 1, 0.1))):
        d = Vector(d).normalized(); u = Vector((0, 0, 1)); y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(Vector(c) + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = size * 1.15; f = f"/home/claude/work/hol/r_{len(tiles)}_{vn}.png"; sc.render.filepath = f; bpy.ops.render.render(write_still=True); row.append(f)
    tiles.append((name, row)); bpy.data.objects.remove(o)
W = 300; cols = 6; rows = (len(tiles) + cols - 1) // cols
img = Image.new("RGB", (cols * W * 2, rows * (W + 16)), "white"); dr = ImageDraw.Draw(img)
for k, (n, fs) in enumerate(tiles):
    x0, y0 = (k % cols) * W * 2, (k // cols) * (W + 16)
    for i, f in enumerate(fs): img.paste(Image.open(f).convert("RGB").resize((W, W)), (x0 + i * W, y0 + 16))
    dr.text((x0 + 4, y0 + 2), f"{k + 1}. {n[:60]}", fill="black")
img.save(OUT); print(len(tiles), "tiles")
