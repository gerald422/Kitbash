"""Check sheet for a kit: every legs with its seated plates (blue), Mar Fil buckle (purple) and trophy spots (orange),
front-left and front-right views each, numbered; rows flagged in the log when a seat looks off.
python tn_sheet.py -- SEAT_JSON STL_ROOT OUT_PNG [kit filter]"""
import bpy, sys, json, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/kitbash/kits/plates"); sys.path.insert(0, "/home/claude/test")
from hol_common import stl, tf, M16, U, LIB, AM; import rend
from PIL import Image, ImageDraw
a = sys.argv[sys.argv.index("--") + 1:]; R = json.load(open(a[0])); ROOT = a[1]; OUT = a[2]; F = a[3] if len(a) > 3 else ""
from legs_frame import legs as legs_geo
PV, PT = stl(U + AM + "Hip Plates/MarFil Assault - Hip Plate L.stl"); BV, BT = stl(U + AM + "Buckles/MarFil Assault - Buckle.stl")
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; cam = rend.setup(sc, 260)
def ob(V, T, M, col):
    me = bpy.data.meshes.new("m"); me.from_pydata(tf(M, V).tolist(), [], T.tolist()); me.update()
    o = bpy.data.objects.new("m", me); sc.collection.objects.link(o); o.color = col; return o
def cone(M):
    bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=1.5); o = bpy.context.active_object
    o.matrix_world = Matrix(M.tolist()) @ Matrix.Translation((0, 0, 0.75)); o.color = rend.ORANGE; return o
legs = sorted(k for k in R if F in k); tiles = []
for i, rel in enumerate(legs):
    r = R[rel]; _, V, T, M = legs_geo(rel, ROOT)
    obs = [ob(V, T, M, rend.GREY), ob(PV, PT, M @ M16(r["parts"]["L"]), rend.BLUE), ob(PV, PT, M @ M16(r["parts"]["R"]), rend.BLUE),
           ob(BV, BT, M @ M16(r["parts"]["B"]), (0.6, 0.45, 0.85, 1))] + [cone(M @ M16(r["sockets"][t])) for t in ("Trophy R", "Trophy L")]
    pts = np.vstack([tf(M @ M16(r["parts"][k]), V_) for k, V_ in (("L", PV), ("R", PV), ("B", BV))]); c = (pts.min(0) + pts.max(0)) / 2
    size = np.ptp(pts, 0).max(); f = []
    for side, dv in (("l", Vector((-0.75, 1, 0.3))), ("r", Vector((0.75, 1, 0.3)))):
        dv = dv.normalized(); u = Vector((0, 0, 1)); yv = (u - dv * u.dot(dv)).normalized(); xv = yv.cross(dv)
        cam.matrix_world = Matrix.LocRotScale(Vector(c) + dv * 300, Matrix((xv, yv, dv)).transposed().to_quaternion(), None); cam.data.ortho_scale = size * 1.6
        f.append("/home/claude/work/tn/sheet/t%03d%s.png" % (i, side)); sc.render.filepath = f[-1]; bpy.ops.render.render(write_still=True)
    tiles.append((rel.split("/")[-1].split("#")[0] + (" (mirror)" if "#v" in rel else ""), f))
    for o in obs: bpy.data.objects.remove(o)
W = 260; cols = 6; rows = (len(tiles) + cols - 1) // cols
img = Image.new("RGB", (cols * 2 * W, rows * (W + 14)), "white"); d = ImageDraw.Draw(img)
for k, (n, f) in enumerate(tiles):
    x, y = (k % cols) * 2 * W, (k // cols) * (W + 14)
    for j, ff in enumerate(f): img.paste(Image.open(ff).convert("RGB"), (x + j * W, y + 14))
    d.text((x + 3, y + 1), "%d %s" % (k + 1, n[:60]), fill="black")
img.save(OUT); print(len(tiles), "legs on", OUT)
