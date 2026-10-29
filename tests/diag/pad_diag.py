import bpy, json, math, os, sys, tempfile
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
OUT = "/home/claude/test/diag"
LIB = "/home/claude/test/padlib"; MF = "Mar Fil - Tacticus"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); inbox = tempfile.mkdtemp(); prefs.inbox_path = inbox
scene = bpy.context.scene; vl = bpy.context.view_layer
rend.setup(scene, 500)
n = [0]
def send(rel, cat, cursor=(0, 0, 0)):
    n[0] += 1; scene.cursor.location = cursor
    with open(os.path.join(inbox, f"{n[0]:03d}.json"), "w") as f:
        json.dump({"path": os.path.join(LIB, rel), "category": cat, "name": os.path.basename(rel)}, f)
    T.process_inbox(); print("   ", T._state["last"]); return vl.objects.active
def select(ob):
    for o in vl.objects: o.select_set(False)
    if ob is not None: ob.select_set(True)
    vl.objects.active = ob
def sock(part, t): return next(c for c in part.children if c.get("ws_type") == t)
select(None)
torso = send(f"{MF}/AssaultMarines-V2/Chests/23-Torso-2.stl", "Chests", (200, 0, 0))
shR = sock(torso, "Shoulder R")
select(torso)
arm = send(f"{MF}/AssaultMarines-V2/Arms/111-Arm-8-R-A.stl", "Arms", (230, 0, 0))
padA = sock(arm, "Pad R")
S = shR.matrix_world; P = padA.matrix_world
print("shoulder socket", S.translation, "pad anchor", P.translation)
inv = S.inverted()
print("pad anchor in shoulder frame:", (inv @ P.translation))
# arm extent in shoulder frame
deps = bpy.context.evaluated_depsgraph_get()
av, at = T._world_tris(arm, deps)
Si = np.array(inv); L = av @ Si[:3, :3].T + Si[:3, 3]
print("arm bbox in shoulder frame lo", L.min(0).round(2), "hi", L.max(0).round(2))
tv, tt = T._world_tris(torso, deps)
Lt = tv @ Si[:3, :3].T + Si[:3, 3]
print("torso bbox in shoulder frame lo", Lt.min(0).round(2), "hi", Lt.max(0).round(2))
# how much of the arm sits inside the torso? (x < 0 side = toward torso)
for x0 in (-3, -2, -1, 0, 1, 2, 3, 4, 6, 8):
    m = (L[:, 0] > x0 - 0.5) & (L[:, 0] < x0 + 0.5)
    if m.any(): print(f"  arm slice x={x0:3d}: top z {L[m, 2].max():6.2f}  y {L[m,1].min():6.2f}..{L[m,1].max():6.2f}")
for x0 in (-6, -4, -2, 0, 2):
    m = (Lt[:, 0] > x0 - 0.5) & (Lt[:, 0] < x0 + 0.5) & (np.abs(Lt[:, 1]) < 4)
    if m.any(): print(f"  torso slice x={x0:3d}: top z {Lt[m, 2].max():6.2f}")
# the pad with the stand-in used by the test
select(torso)
p = send(f"{MF}/Kit/Shoulder Pads/56-ShoulderPad-1.stl", "Shoulder Pads", (260, 0, 0))
cup = Vector((0.0, 0.55, 0.33))
F = padA.matrix_world.to_3x3().normalized()
R3 = Matrix((-(F @ Vector((0, 1, 0))), F @ Vector((1, 0, 0)), F @ Vector((0, 0, 1)))).transposed()
p.matrix_world = Matrix.Translation(shR.matrix_world.translation - R3 @ cup) @ R3.to_4x4()
pv, pt = T._world_tris(p, deps); Lp = pv @ Si[:3, :3].T + Si[:3, 3]
print("pad before settle (shoulder frame) lo", Lp.min(0).round(2), "hi", Lp.max(0).round(2))
mv = T.settle_onto(p, [arm], -(F @ Vector((0, 0, 1))), sink=0.1)
print("settle moved", mv)
pv, pt = T._world_tris(p, deps); Lp = pv @ Si[:3, :3].T + Si[:3, 3]
print("pad after settle (shoulder frame) lo", Lp.min(0).round(2), "hi", Lp.max(0).round(2))
# where is the contact: pad verts nearest to the arm
from mathutils.bvhtree import BVHTree
tb = BVHTree.FromPolygons(av.tolist(), at.tolist())
d = np.array([tb.find_nearest(Vector(q))[3] for q in pv[::7]])
idx = np.argsort(d)[:30]
C = Lp[::7][idx]
print("contact points (shoulder frame):", C.mean(0).round(2), "spread", C.std(0).round(2))
json.dump({"S": [list(r) for r in S], "pad": [list(r) for r in p.matrix_world]}, open(f"{OUT}/pad_diag.json", "w"))
fr = shR.matrix_world
rend.render(scene, OUT, "diag111", [arm, p], {"front": (0, 1, 0), "side": (1, 0, 0), "back": (0, -1, 0)}, [rend.BLUE, rend.ORANGE], frame=fr, up=(0, 0, 1))
rend.render(scene, OUT, "diag111t", [torso, arm, p], {"front": (0, 1, 0), "side": (1, 0, 0)}, [rend.GREY, rend.BLUE, rend.ORANGE], frame=fr, up=(0, 0, 1))
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/pad_diag.blend")
# dump geometry in the shoulder frame for slicing
pv, pt = T._world_tris(p, deps); Lp = pv @ Si[:3, :3].T + Si[:3, 3]
np.savez("/home/claude/test/diag/slices.npz", arm_v=L, arm_t=at, torso_v=Lt, torso_t=tt, pad_v=Lp, pad_t=pt,
         padA=np.array(inv @ padA.matrix_world))
