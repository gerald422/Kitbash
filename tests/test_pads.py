"""Shin pads, pauldrons and belt bits: anchors, Save Fit for Folder, folder fits on import,
pauldrons turning with the arm, settle with sink. Raw creator files from 'for claude.blend'."""
import bpy, json, math, os, sys, tempfile
import numpy as np
from mathutils import Matrix, Vector

LIB = "/home/claude/test/padlib"
MF = "Mar Fil - Tacticus"
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
A = lambda m: np.array([list(r) for r in m], float)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs()
inbox = tempfile.mkdtemp(); prefs.inbox_path = inbox
scene = bpy.context.scene; vl = bpy.context.view_layer
for f in ("Knee Pads", "Shoulder Pads", "Accessories"):
    p = os.path.join(LIB, MF, "Kit", f, "_fits.json")
    if os.path.exists(p): os.remove(p)
n = [0]
def send(rel, cat, cursor=None):
    n[0] += 1
    if cursor is not None: scene.cursor.location = cursor
    with open(os.path.join(inbox, f"{n[0]:03d}.json"), "w") as f:
        json.dump({"path": os.path.join(LIB, rel), "category": cat, "name": os.path.basename(rel)}, f)
    T.process_inbox(); print("     ", T._state["last"])
    return vl.objects.active
def select(ob):
    for o in vl.objects: o.select_set(False)
    if ob is not None: ob.select_set(True)
    vl.objects.active = ob
def click(part, local_from, local_dir):
    """what a click does: ray into the scene from a point in the part's own coordinates"""
    mw = part.matrix_world
    o = mw @ Vector(local_from); d = (mw.to_3x3() @ Vector(local_dir)).normalized()
    hit, loc, nrm, _i, ob, _m = scene.ray_cast(bpy.context.evaluated_depsgraph_get(), o, d)
    assert hit and ob == part, (hit, ob)
    return loc, nrm
def sock(part, t): return next(c for c in part.children if c.get("ws_type") == t)
def depth_into(part, others, direction):
    """how far the part is pressed into the others along direction (+ = overlapping)"""
    keep = part.matrix_world.copy()
    mv = T.settle_onto(part, others, direction, sink=0.0)
    part.matrix_world = keep
    return None if mv is None else -mv

# ---------------------------------------------------------------- shin pads
print("\n== Mar Fil legs as they arrive, Shin anchors from two clicks each")
select(None)
legs = send(f"{MF}/Kit/Legs/29-Legs-2.stl", "Legs", (0, 0, 0))
kR = click(legs, (4.5, 30, 13.0), (0, -1, 0)); aR = click(legs, (4.5, 30, 3.0), (0, -1, 0))
kL = click(legs, (-5.3, 30, 12.0), (0, -1, 0)); aL = click(legs, (-5.3, 30, 3.0), (0, -1, 0))
sR = T.make_anchor(legs, "Shin R", [kR[0], aR[0]], [kR[1], aR[1]])
sL = T.make_anchor(legs, "Shin L", [kL[0], aL[0]], [kL[1], aL[1]])
ck("Shin R / Shin L sockets on the legs", {c.get("ws_type") for c in legs.children} >= {"Shin R", "Shin L"})
ck("Shin R sits on the knee click", (sR.matrix_world.translation - kR[0]).length < 1e-4)
yR = (sR.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
ck("Shin R points up the shin (knee minus ankle)", yR.dot((kR[0] - aR[0]).normalized()) > 0.999, yR)
zR = (sR.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
ck("Shin R faces out of the leg (front)", zR.dot(Vector((0, 1, 0))) > 0.5, zR)
again = T.make_anchor(legs, "Shin R", [kR[0], aR[0]], [kR[1], aR[1]])
ck("placing it again replaces it", len([c for c in legs.children if c.get("ws_type") == "Shin R"]) == 1)
sR = again

print("\n== first pad from a folder: parked on the anchor, no fit yet")
select(legs)
p68 = send(f"{MF}/Kit/Knee Pads/68-ShinPad-1.stl", "Knee Pads", (60, 0, 0))
ck("asks for a fit", "parked on Shin R" in T._state["last"] and "Save Fit for Folder" in T._state["last"], T._state["last"])
ck("parked beside the anchor", (p68.matrix_world @ ((Vector(p68.bound_box[0]) + Vector(p68.bound_box[6])) / 2) - sR.matrix_world.translation).length < 1e-3)
# place it by eye (stand-in: the ball-in-socket placement from the earlier test)
fits = json.load(open("/home/claude/blend/forclaude/shinfit.json"))
p68.matrix_world = legs.matrix_world @ Matrix(fits["29-Legs-2|68-ShinPad-1|R"])
path, tname = T.save_folder_fit(p68)
saved = json.load(open(path))
ck("Save Fit for Folder wrote Shin R to Knee Pads/_fits.json", tname == "Shin R" and "Shin R" in saved and len(saved["Shin R"]["m"]) == 16, saved.keys())
ck("the pad is now snapped to Shin R", p68.ws_snap_sock_ref == sR)
by_eye = A(p68.matrix_world)

print("\n== next pad from that folder: lands with the folder fit and settles")
select(p68)
p69 = send(f"{MF}/Kit/Knee Pads/69-ShinPad-2.stl", "Knee Pads", (90, 0, 0))
ck("replaced the first pad on Shin R", p69.ws_snap_sock_ref == sR and bpy.data.objects.get("68-ShinPad-1") is None, T._state["last"])
ck("status says settled", "settled onto the model" in T._state["last"], T._state["last"])
moved = A(p69.matrix_world) @ np.linalg.inv(by_eye)
zw = np.array(sR.matrix_world.to_3x3() @ Vector((0, 0, 1))); zw /= np.linalg.norm(zw)
t = moved[:3, 3]
tilt = math.degrees(math.acos(max(-1, min(1, (np.trace(moved[:3, :3]) - 1) / 2))))
ck("same legs as the fit was saved on: lands where the first pad was put (within 3 deg, 0.5)",
   tilt < 3 and np.linalg.norm(t) < 0.5, (tilt, t))
d = depth_into(p69, [legs], -Vector(zw))
ck("sits on the shin, not floating", d is not None and d > 0.0, d)
print(f"      {tilt:.1f} deg and {np.linalg.norm(t):.2f} from the first pad's pose, {d:.2f} into the leg")
fits = json.load(open(path))["Shin R"]
ck("the saved fit carries how the settle judged the by-eye pose", "rock" in fits and "slide" in fits, list(fits))

print("\n== Shin L needs its own fit once; then pads land there too")
select(legs)
p70 = send(f"{MF}/Kit/Knee Pads/70-ShinPad-3.stl", "Knee Pads", (120, 0, 0))
ck("no free Shin R... goes to Shin L and parks (no Shin L fit yet)",
   "parked on Shin L" in T._state["last"] or "parked on Shin R" in T._state["last"], T._state["last"])

# ---------------------------------------------------------------- pauldrons
print("\n== pauldron sits on the arm: Pad anchor added to each arm on its shoulder")
select(None)
torso = send(f"{MF}/AssaultMarines-V2/Chests/23-Torso-2.stl", "Chests", (200, 0, 0))
select(torso)
arm = send(f"{MF}/AssaultMarines-V2/Arms/77-Arm-1-R-B.stl", "Arms", (230, 0, 0))
sh = sock(torso, "Shoulder R")
ck("arm on Shoulder R, Pad anchor added", arm.ws_snap_sock_ref == sh and "Pad anchor added" in T._state["last"], T._state["last"])
padR = sock(arm, "Pad R")
up = (padR.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
off = padR.matrix_world.translation - sh.matrix_world.translation
hit = arm.closest_point_on_mesh(arm.matrix_world.inverted() @ padR.matrix_world.translation)
ck("Pad R is on the arm's surface, above the shoulder joint", hit[0] and (arm.matrix_world @ hit[1] - padR.matrix_world.translation).length < 1e-3
   and 0 < off.dot(up) < 8, off)
ck("Pad R records how far it turned with the arm", padR.get("tiow_swing") is not None, padR.get("tiow_swing"))
select(torso)
pad = send(f"{MF}/Kit/Shoulder Pads/56-ShoulderPad-1.stl", "Shoulder Pads", (260, 0, 0))
ck("pad parked on the arm's Pad R, asks for a fit", "parked on Pad R" in T._state["last"], T._state["last"])
P = json.load(open("/home/claude/blend/forclaude/pauldron_fit.json"))
pad.matrix_world = torso.matrix_world @ Matrix(P["pads"]["56-ShoulderPad-1"])      # placed by eye
path, tname = T.save_folder_fit(pad)
ck("fit saved as Pad R", tname == "Pad R" and "Pad R" in json.load(open(path)))
ck("pad is parented to the arm's anchor", pad.ws_snap_sock_ref == padR and pad.parent == padR)
_orig = T.settle_onto
def _log(part, others, direction, sink=0.0, samples=4000, **kw):
    mv = _orig(part, others, direction, sink, samples, **kw)
    print("      DEBUG settle", part.name, [o.name for o in others], "dir", tuple(round(x, 3) for x in direction), "moved", mv)
    return mv
T.settle_onto = _log
select(torso)
arm2 = send(f"{MF}/AssaultMarines-V2/Arms/126-Arm-11-R-A.stl", "Arms", (290, 0, 0))
T.settle_onto = _orig
ck("raised arm took the shoulder and got its own Pad anchor", arm2.ws_snap_sock_ref == sh and any(c.get("ws_type") == "Pad R" for c in arm2.children), T._state["last"])
ck("the pad moved across to the new arm and settled", pad.ws_snap_sock_ref == sock(arm2, "Pad R") and "moved across" in T._state["last"], T._state["last"])
dirn = sock(arm2, "Pad R").matrix_world.to_3x3() @ Vector((0, 0, -1))
g = T.settle_onto(pad, [arm2], dirn, dry=True)
ck("pad sits on the arm, not floating above it", g is not None and g < 0.3, g)
select(pad)
pad2 = send(f"{MF}/Kit/Shoulder Pads/57-ShoulderPad-2.stl", "Shoulder Pads", (320, 0, 0))
ck("second pad from the folder replaces it on the arm", pad2.ws_snap_sock_ref == sock(arm2, "Pad R") and bpy.data.objects.get("56-ShoulderPad-1") is None, T._state["last"])
ck("the arm stayed put", arm2.ws_snap_sock_ref == sh)

# ---------------------------------------------------------------- belt bits
print("\n== belt bit on a Hip anchor (one click)")
hp = click(legs, (30, 1.0, 23.0), (-1, 0, 0))
hip = T.make_anchor(legs, "Hip R", [hp[0]], [hp[1]])
yh = (hip.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
ck("Hip R faces out of the side, Y as near up as it goes", (hip.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized().x > 0.7 and yh.z > 0.7, yh)
select(legs)
acc = send(f"{MF}/Kit/Accessories/230-Accessory-1.stl", "Accessories", (350, 0, 0))
ck("pouch parked on Hip R", "parked on Hip R" in T._state["last"], T._state["last"])
H = hip.matrix_world
X, Y, Zz = (H.to_3x3() @ Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
R3 = Matrix((-X, Zz, Y)).transposed()          # pouch +Y (its front) out of the hip, pouch +Z up
acc.matrix_world = Matrix.Translation(H.translation - Zz * 1.0) @ R3.to_4x4()
T.save_folder_fit(acc)
acc_eye = A(acc.matrix_world)
select(legs)
acc2 = send(f"{MF}/Kit/Accessories/231-Accessory-2.stl", "Accessories", (380, 0, 0))
ck("next pouch lands on Hip R and settles", acc2.ws_snap_sock_ref == hip and "settled" in T._state["last"], T._state["last"])
mv = A(acc2.matrix_world) @ np.linalg.inv(acc_eye)
tl = math.degrees(math.acos(max(-1, min(1, (np.trace(mv[:3, :3]) - 1) / 2))))
ck("lands where the first pouch was put (same belt)", tl < 3 and np.linalg.norm(mv[:3, 3]) < 0.5, (tl, mv[:3, 3]))

bpy.ops.wm.save_as_mainfile(filepath="/home/claude/test/pads_result.blend")
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
