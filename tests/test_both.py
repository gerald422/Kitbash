"""Both sides: shin pads (fit saved on one legs piece, used on another), belt bits on both
hips, pauldrons on both arms through arm swaps. Renders images of every stage."""
import bpy, json, math, os, sys, tempfile, time
import numpy as np
from mathutils import Matrix, Vector

LIB = "/home/claude/test/padlib"; MF = "Mar Fil - Tacticus"
OUT = "/home/claude/test/both"; os.makedirs(OUT, exist_ok=True)
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
A = lambda m: np.array([list(r) for r in m], float)
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
for root, ds, fs in os.walk(LIB):
    for f in fs:
        if f == "_fits.json": os.remove(os.path.join(root, f))
n = [0]
def send(rel, cat, cursor=None):
    n[0] += 1
    if cursor is not None: scene.cursor.location = cursor
    with open(os.path.join(inbox, f"{n[0]:03d}.json"), "w") as f:
        json.dump({"path": os.path.join(LIB, rel), "category": cat, "name": os.path.basename(rel)}, f)
    t = time.time(); T.process_inbox()
    print(f"      [{time.time() - t:4.1f}s]", T._state["last"])
    return vl.objects.active
def select(ob):
    for o in vl.objects: o.select_set(False)
    if ob is not None: ob.select_set(True)
    vl.objects.active = ob
def sock(part, t): return next(c for c in part.children if c.get("ws_type") == t)
def depth_into(part, others, direction):
    keep = part.matrix_world.copy()
    mv = T.settle_onto(part, others, direction, sink=0.0)
    part.matrix_world = keep
    return None if mv is None else -mv

# ---- renderer (Workbench, works headless)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'OBJECT'; scene.display.shading.show_cavity = True
scene.render.resolution_x = scene.render.resolution_y = 620
scene.world = bpy.data.worlds.new("w")
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 5000
def render(name, obs, views, colors):
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
        if o.type == 'EMPTY': o.hide_render = True
    for o, c in zip(obs, colors): o.color = c
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; size = (hi - lo).length
    for vname, d in views.items():
        d = Vector(d).normalized(); up = Vector((0, 0, 1))
        y = (up - d * up.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 50), Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = size * 1.02
        scene.render.filepath = f"{OUT}/{name}_{vname}.png"; bpy.ops.render.render(write_still=True)
GREY, BLUE, ORANGE, GREEN, PURPLE = (0.8, 0.8, 0.76, 1), (0.45, 0.65, 0.88, 1), (0.9, 0.58, 0.35, 1), (0.55, 0.8, 0.5, 1), (0.75, 0.55, 0.85, 1)
LEGVIEWS = {"front": (0, 1, 0.12), "right": (1, 0, 0.08), "left": (-1, 0, 0.08), "threequarter": (0.8, 1, 0.35)}

# ---------------------------------------------------------------- shin pads
C = json.load(open("/home/claude/test/shin_clicks.json"))
def shin_anchors(legs, name):
    out = {}
    for side in ("R", "L"):
        c = C[name][side]; mw = legs.matrix_world
        k, a = (mw @ Vector(c["knee"][0]), (mw.to_3x3() @ Vector(c["knee"][1])).normalized()), \
               (mw @ Vector(c["ankle"][0]), (mw.to_3x3() @ Vector(c["ankle"][1])).normalized())
        out[side] = T.make_anchor(legs, f"Shin {side}", [k[0], a[0]], [k[1], a[1]])
    return out
print("\n== shin pads: fits saved on 29-Legs-2 (both legs)")
select(None)
legs29 = send(f"{MF}/Kit/Legs/29-Legs-2.stl", "Legs", (0, 0, 0))
a29 = shin_anchors(legs29, "29-Legs-2")
pads29 = {}
for side in ("R", "L"):
    select(a29[side])
    p = send(f"{MF}/Kit/Knee Pads/68-ShinPad-1.stl", "Knee Pads", (40, 0, 0))
    ck(f"first pad parked on Shin {side}", f"parked on Shin {side}" in T._state["last"], T._state["last"])
    p.matrix_world = legs29.matrix_world @ Matrix(C["29-Legs-2"][side]["seated"])     # placed by eye
    T.save_folder_fit(p)
    pads29[side] = p
print("\n== the next pads from that folder land on both legs of 29-Legs-2")
for side in ("R", "L"):
    select(pads29[side])
    q = send(f"{MF}/Kit/Knee Pads/69-ShinPad-2.stl", "Knee Pads", (60, 0, 0))
    ck(f"69 replaced 68 on Shin {side}", q.ws_snap_sock_ref == a29[side], T._state["last"])
    d = depth_into(q, [legs29], a29[side].matrix_world.to_3x3() @ Vector((0, 0, -1)))
    ck(f"  pressed into the leg (0.2-1.0)", d is not None and 0.15 < d < 1.0, d)
    print(f"      off the by-eye pose by {ang(q.matrix_world, legs29.matrix_world @ Matrix(C['29-Legs-2'][side]['seated'])):.1f} deg")
    pads29[side] = q
print("\n== same folder on a different legs piece (jump legs), both legs")
select(None)
legs35 = send(f"{MF}/Kit/Legs/35-Legs-2-A.stl", "Legs", (80, 0, 0))
a35 = shin_anchors(legs35, "35-Legs-2-A")
pads35 = {}
for side in ("R", "L"):
    select(a35[side])
    q = send(f"{MF}/Kit/Knee Pads/69-ShinPad-2.stl", "Knee Pads", (120, 0, 0))
    ck(f"pad on the jump legs' Shin {side}", q.ws_snap_sock_ref == a35[side], T._state["last"])
    seated = legs35.matrix_world @ Matrix(C["35-Legs-2-A"][side]["seated"])
    e = ang(q.matrix_world, seated)
    print(f"      off the best-seated pose by {e:.1f} deg")
    ck(f"  within 6 deg of the best-seated pose", e < 6.0, e)
    pads35[side] = q
render("shins_29", [legs29, pads29["R"], pads29["L"]], LEGVIEWS, [GREY, ORANGE, BLUE])
render("shins_35", [legs35, pads35["R"], pads35["L"]], LEGVIEWS, [GREY, ORANGE, BLUE])

# ---------------------------------------------------------------- belt
print("\n== belt bits on both hips")
def click(part, local_from, local_dir):
    mw = part.matrix_world
    hit, loc, nrm, _i, ob, _m = scene.ray_cast(bpy.context.evaluated_depsgraph_get(), mw @ Vector(local_from), (mw.to_3x3() @ Vector(local_dir)).normalized())
    assert hit and ob == part, (hit, ob); return loc, nrm
hips = {}
for side, sx in (("R", 1), ("L", -1)):
    p, nn = click(legs29, (30 * sx, 1.0, 23.0), (-sx, 0, 0))
    hips[side] = T.make_anchor(legs29, f"Hip {side}", [p], [nn])
pouches = {}
for side in ("R", "L"):
    select(hips[side])
    a = send(f"{MF}/Kit/Accessories/230-Accessory-1.stl", "Accessories", (150, 0, 0))
    H = hips[side].matrix_world
    X, Y, Z = (H.to_3x3() @ Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    a.matrix_world = Matrix.Translation(H.translation - Z * 1.0) @ Matrix((-X, Z, Y)).transposed().to_4x4()   # by eye
    T.save_folder_fit(a)
    select(hips[side])
    b = send(f"{MF}/Kit/Accessories/231-Accessory-2.stl", "Accessories", (170, 0, 0))
    ck(f"pouch on Hip {side}", b.ws_snap_sock_ref == hips[side], T._state["last"])
    pouches[side] = b
render("belt_29", [legs29, pouches["R"], pouches["L"], pads29["R"], pads29["L"]],
       {"front": (0, 1, 0.12), "right": (1, 0, 0.08), "left": (-1, 0, 0.08), "back": (0, -1, 0.12)}, [GREY, GREEN, PURPLE, ORANGE, BLUE])

# ---------------------------------------------------------------- pauldrons
print("\n== pauldrons on both arms")
select(None)
torso = send(f"{MF}/AssaultMarines-V2/Chests/23-Torso-2.stl", "Chests", (200, 0, 0))
shR = sock(torso, "Shoulder R")
MX = Matrix.Scale(-1, 4, (1, 0, 0))
L_local = MX @ (torso.matrix_world.inverted() @ shR.matrix_world) @ MX
shL = bpy.data.objects.new("23-Torso-2_socket_Shoulder L", None); torso.users_collection[0].objects.link(shL)
shL["ws_type"] = "Shoulder L"; shL.empty_display_type = 'ARROWS'; shL.parent = torso
shL.matrix_parent_inverse = torso.matrix_world.inverted(); shL.matrix_world = torso.matrix_world @ L_local
T._part_sockets()[0].ensure_type(scene, "Shoulder L")
t_sl = next(t for t in scene.ws_types if t.name == "Shoulder L"); t_r = next(t for t in scene.ws_types if t.name == "Shoulder R")
t_sl.mat = list(t_r.mat); t_sl.captured = True
arms = {}
for side in ("R", "L"):
    select(torso)
    arms[side] = send(f"{MF}/AssaultMarines-V2/Arms/111-Arm-8-{side}-A.stl", "Arms", (230, 0, 0))
    ck(f"arm on Shoulder {side} with a Pad anchor", arms[side].ws_snap_sock_ref == (shR if side == "R" else shL)
       and any(c.get("ws_type") == f"Pad {side}" for c in arms[side].children), T._state["last"])
pads = {}
cup = Vector((0.0, 0.55, 0.33))
Tm = torso.matrix_world @ MX @ torso.matrix_world.inverted()        # mirror across the torso's middle
for side, rel in (("R", "Shoulder Pads/56-ShoulderPad-1.stl"), ("L", "Shoulder Pads Mirrored/56-ShoulderPad-1-L.stl")):
    select(torso)
    p = send(f"{MF}/Kit/{rel}", "Shoulder Pads", (260, 0, 0))
    ck(f"first pad parked on Pad {side}", f"parked on Pad {side}" in T._state["last"], T._state["last"])
    if side == "R":
        # by eye: pad upright (dome out, open side to the torso), top leaning in a touch, the inside
        # of the dome resting on the top of the arm a little out from the joint
        pa = sock(arms["R"], "Pad R")
        loc, rot, _ = shR.matrix_world.decompose()
        F = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1))) @ Matrix.Rotation(math.radians(pa.get("tiow_swing", 0.0)), 4, 'X')
        Rl = Matrix.Rotation(math.radians(-5.0), 3, 'Y') @ Matrix(((0, 1, 0), (-1, 0, 0), (0, 0, 1)))
        inv = arms["R"].matrix_world.inverted()
        ok, hit, _n, _i = arms["R"].ray_cast(inv @ (F @ Vector((1.25, 0, 30))), (inv.to_3x3() @ (F.to_3x3() @ Vector((0, 0, -1)))).normalized())
        Rw = F.to_3x3() @ Rl
        p.matrix_world = Matrix.Translation(arms["R"].matrix_world @ hit - Rw @ Vector((0, 0.54, 3.14))) @ Rw.to_4x4()
        PR = p.matrix_world.copy()
    else:
        p.matrix_world = Tm @ PR @ MX            # the mirror image of the right one
    T.save_folder_fit(p)
    pads[side] = p
render("pads_111", [torso, arms["R"], arms["L"], pads["R"], pads["L"]],
       {"front": (0, 1, 0.25), "right": (1, 0, 0.15), "left": (-1, 0, 0.15), "top": (0.2, 0.6, 1.0)}, [GREY, BLUE, BLUE, ORANGE, ORANGE])
for arm_id in ("126-Arm-11", "131-Arm-12", "101-Arm-6"):
    print(f"\n== swap both arms for {arm_id}: the pads follow")
    for side in ("R", "L"):
        select(torso)
        a = send(f"{MF}/AssaultMarines-V2/Arms/{arm_id}-{side}-A.stl", "Arms", (300, 0, 0))
        ck(f"{arm_id} {side} on the shoulder, pad carried across",
           pads[side].ws_snap_sock_ref == sock(a, f"Pad {side}") and "moved across" in T._state["last"], T._state["last"])
        arms[side] = a
    render(f"pads_{arm_id.split('-')[0]}", [torso, arms["R"], arms["L"], pads["R"], pads["L"]],
           {"front": (0, 1, 0.25), "right": (1, 0, 0.15), "left": (-1, 0, 0.15), "top": (0.2, 0.6, 1.0)}, [GREY, BLUE, BLUE, ORANGE, ORANGE])
    for side in ("R", "L"):
        sw = sock(arms[side], f"Pad {side}").get("tiow_swing")
        print(f"      {side}: pad follows the arm {sw} deg")

print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
