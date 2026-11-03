"""Render TN legs with the seated plates (L file, R mirror image), buckle and trophy spots, in torso coordinates.
python tn_render.py -- SEAT_JSON OUT_PNG"""
import bpy, sys, json, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/kitbash/kits/plates"); sys.path.insert(0, "/home/claude/test")
from hol_common import stl, tf, M16, U, LIB, AM; import rend
from PIL import Image, ImageDraw
a = sys.argv[sys.argv.index("--") + 1:]; R = json.load(open(a[0])); OUT = a[1]
TT = json.load(open(LIB + "Turtle Ninja - Heresy/Mk7-8 Builder/Mk7-8/Chests/TN Mk7-8 - Mk8 Torso A1.sockets.json"))
UP, FW = M16(TT["upright"]), M16([s for s in TT["sockets"] if s["type"] == "Flat Waist"][0]["matrix"])
PV, PT = stl(U + AM + "Hip Plates/MarFil Assault - Hip Plate L.stl"); BV, BT = stl(U + AM + "Buckles/MarFil Assault - Buckle.stl")
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; cam = rend.setup(sc, 420)
def ob(name, V, T, M, col):
    me = bpy.data.meshes.new(name); me.from_pydata(tf(M, V).tolist(), [], T.tolist()); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.color = col; return o
def marker(M, col):
    bpy.ops.mesh.primitive_cone_add(radius1=0.45, depth=1.4, location=(0, 0, 0)); o = bpy.context.active_object
    o.matrix_world = Matrix((M @ np.diag([1, 1, 1, 1.0])).tolist()) @ Matrix.Translation((0, 0, 0.7)); o.color = col; return o
rows = []
for rel, r in R.items():
    sk = json.load(open(LIB + rel + ".sockets.json")); M = UP @ FW @ M16(sk["fits"]["Flat Waist"])
    V, T = stl(U + rel + ".stl"); obs = [ob("legs", V, T, M, rend.GREY)]
    obs += [ob("pL", PV, PT, M @ M16(r["parts"]["L"]), rend.BLUE), ob("pR", PV, PT, M @ M16(r["parts"]["R"]), rend.BLUE), ob("b", BV, BT, M @ M16(r["parts"]["B"]), (0.6, 0.45, 0.85, 1))]
    obs += [marker(M @ M16(r["sockets"][t]), rend.ORANGE) for t in ("Trophy R", "Trophy L")]
    fs = rend.render(sc, "/home/claude/work/tn", "seat_" + rel.split(" - ")[-1].replace(" ", "_"), obs, {"front": (0.1, 1, 0.25), "left": (-1, 0.3, 0.2), "right": (1, 0.3, 0.2)}, [o.color for o in obs], pad=0.75)
    rows.append((rel.split("/")[-1], fs))
    for o in obs: bpy.data.objects.remove(o)
W = 420; img = Image.new("RGB", (3 * W, len(rows) * (W + 18)), "white"); d = ImageDraw.Draw(img)
for i, (n, fs) in enumerate(rows):
    for j, v in enumerate(("front", "left", "right")): img.paste(Image.open(fs[v]).convert("RGB"), (j * W, i * (W + 18) + 18))
    d.text((6, i * (W + 18) + 3), n + "   (front | left | right)   blue = hip plates, purple = Mar Fil buckle, orange = trophy spots", fill="black")
img.save(OUT)
