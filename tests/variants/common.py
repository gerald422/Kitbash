"""Shared set-up for the variant tests: Blender with Part Sockets + TIOW Inbox, a send() that
goes through the real inbox, shin anchors from emulated clicks, by-eye stand-ins."""
import bpy, json, math, os, sys, tempfile, time
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
LIB = "/home/claude/test/padlib"; MF = "Mar Fil - Tacticus"; MA = "Marta PunkGirl - Mk10"
A = lambda m: np.array([list(r) for r in m], float)
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
def ang(a, b):
    R = A(a)[:3, :3] @ A(b)[:3, :3].T
    return math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); inbox = tempfile.mkdtemp(); prefs.inbox_path = inbox
scene = bpy.context.scene; vl = bpy.context.view_layer
rend.setup(scene, 620)
for root, ds, fs in os.walk(LIB):
    for f in fs:
        if f == "_fits.json": os.remove(os.path.join(root, f))
_n = [0]
def send(rel, cat, cursor=None):
    _n[0] += 1
    if cursor is not None: scene.cursor.location = cursor
    with open(os.path.join(inbox, f"{_n[0]:03d}.json"), "w") as f:
        json.dump({"path": os.path.join(LIB, rel), "category": cat, "name": os.path.basename(rel)}, f)
    t = time.time(); T.process_inbox()
    print(f"      [{time.time() - t:4.1f}s]", T._state["last"])
    return vl.objects.active
def select(ob):
    for o in vl.objects: o.select_set(False)
    if ob is not None: ob.select_set(True)
    vl.objects.active = ob
def sock(part, t): return next(c for c in part.children if c.get("ws_type") == t)
CLICKS = json.load(open("/home/claude/test/shin_clicks.json"))
def shin_anchors(legs, name):
    out = {}
    for side in ("R", "L"):
        c = CLICKS[name][side]; mw = legs.matrix_world
        k = (mw @ Vector(c["knee"][0]), (mw.to_3x3() @ Vector(c["knee"][1])).normalized())
        a = (mw @ Vector(c["ankle"][0]), (mw.to_3x3() @ Vector(c["ankle"][1])).normalized())
        out[side] = T.make_anchor(legs, f"Shin {side}", [k[0], a[0]], [k[1], a[1]])
    return out
def bbox_local(ob):
    lo = Vector(ob.bound_box[0]); hi = Vector(ob.bound_box[6]); return lo, hi
# ---- by-eye stand-ins for a first shin pad from a folder (what you'd do by hand: pad upright on the
# shin, outer face out, top level with where the Mar Fil pads sit, then pushed on until it touches)
SHIN_TOP = Vector((0.0, 2.9, 3.0))        # top-front of a seated pad, in the Shin anchor's frame (from the 68 pads)
FAMILY = {   # pad axes -> anchor axes (columns: where pad X, Y, Z go), and the pad's top-front point
    "marfilB": (Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0))), lambda lo, hi: Vector(((lo.x + hi.x) / 2, hi.y, hi.z))),
    "marta":   (Matrix.Identity(3),                          lambda lo, hi: Vector(((lo.x + hi.x) / 2, hi.y, hi.z))),
    "marfil68": (Matrix(((0, 1, 0), (0, 0, 1), (1, 0, 0))),  lambda lo, hi: Vector((hi.x, (lo.y + hi.y) / 2, hi.z))),
}
def byeye_shin(pad, legs, anchor, family, touch=20.0):
    """By eye: the pad upright along the shin (knee-to-ankle line), outer face out, its top where
    the Mar Fil pads' tops sit, then pushed straight in until a fifth of its inside touches and
    pressed 0.2 further."""
    Rm, refp = FAMILY[family]
    lo, hi = bbox_local(pad)
    M = Matrix.Translation(SHIN_TOP - Rm @ refp(lo, hi)) @ Rm.to_4x4()
    loc, rot, _s = anchor.matrix_world.decompose(); Aw = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))
    pad.matrix_world = Aw @ M
    return T.settle_onto(pad, [legs], Aw.to_3x3() @ Vector((0, 0, -1)), sink=0.2, touch=touch, frame=Aw)

# ---- torso with both shoulders (Shoulder L = the mirror of Shoulder R) and the pauldron by-eye stand-in
MX = Matrix.Scale(-1, 4, (1, 0, 0))
def torso_both(cursor=(200, 0, 0)):
    select(None)
    torso = send(f"{MF}/AssaultMarines-V2/Chests/23-Torso-2.stl", "Chests", cursor)
    shR = sock(torso, "Shoulder R")
    L_local = MX @ (torso.matrix_world.inverted() @ shR.matrix_world) @ MX
    shL = bpy.data.objects.new("23-Torso-2_socket_Shoulder L", None); torso.users_collection[0].objects.link(shL)
    shL["ws_type"] = "Shoulder L"; shL.empty_display_type = 'ARROWS'; shL.parent = torso
    shL.matrix_parent_inverse = torso.matrix_world.inverted(); shL.matrix_world = torso.matrix_world @ L_local
    T._part_sockets()[0].ensure_type(scene, "Shoulder L")
    t_sl = next(t for t in scene.ws_types if t.name == "Shoulder L"); t_r = next(t for t in scene.ws_types if t.name == "Shoulder R")
    t_sl.mat = list(t_r.mat); t_sl.captured = True
    return torso, shR, shL
CUP_CEIL = Vector((0.0, 0.54, 0.34 + 2.8))      # top of the cup inside a Mar Fil 56-60 pauldron, pad frame
def byeye_pauldron(pad, arm, shoulder, cx=1.25, flare=5.0):
    """By eye, right arm: pad upright (Mar Fil's own frame: dome out, open side to the torso), its top
    leaning in a touch, the inside of the dome resting on the top of the arm a little out from the joint."""
    pa = next(c for c in arm.children if c.get("ws_type") == "Pad R")
    loc, rot, _ = shoulder.matrix_world.decompose()
    F = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1))) @ Matrix.Rotation(math.radians(pa.get("tiow_swing", 0.0)), 4, 'X')
    Rp = Matrix(((0, 1, 0), (-1, 0, 0), (0, 0, 1)))                 # F x = pad y, F y = -pad x, F z = pad z
    Rl = Matrix.Rotation(math.radians(-flare), 3, 'Y') @ Rp
    start = F @ Vector((cx, 0.0, 30.0)); down = F.to_3x3() @ Vector((0, 0, -1))
    inv = arm.matrix_world.inverted()
    ok, hit, _n, _i = arm.ray_cast(inv @ start, (inv.to_3x3() @ down).normalized())
    assert ok
    top_w = arm.matrix_world @ hit
    Rw = F.to_3x3() @ Rl
    pad.matrix_world = Matrix.Translation(top_w - Rw @ CUP_CEIL) @ Rw.to_4x4()
