"""Tilt shield by-eye blend: Mar Fil Assault Torso 1 + Arm 1A R + Shoulder Pad 1 (built by TIOW 1.17.7), Tilt Shield 1
on the right upper chest (moved from the VitalyKhan captain, scaled to Mar Fil) and a second Tilt Shield 1 near the right pad."""
import bpy, json, os, sys, tempfile, struct
import numpy as np
from mathutils import Matrix
sys.path.insert(0, "/home/claude/test"); import rend
W = "/home/claude/work/tilt/lib"; TIOW = "/home/claude/kitbash/addons/tiow_inbox.py"; OUT = sys.argv[sys.argv.index("--") + 1]
D = W + "/Mar Fil - Tacticus/AssaultMarines-V2/"
TORSO, ARM, PAD = D + "Chests/MarFil Assault - Torso 1.stl", D + "Arms/MarFil Assault - Arm 1A R.stl", D + "Shoulder Pads/MarFil Assault - Shoulder Pad 1.stl"
TS = W + "/Tilt Shields/Tilt Shield 1.stl"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True); bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox()
for n, (p, cat, sock) in enumerate([(TORSO, "Chests", None), (ARM, "Arms", "Shoulder R"), (PAD, "Shoulder Pads", "Pad R")]):
    r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": "m0"}
    if sock: r["socket"] = sock
    else: r["at"] = [0, 0, 0]
    json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
T._state["beat"] = {}; T.process_inbox()
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
for o in obs: print(o.name, o.get("tiow_category"), o.get("ws_snap_type"), [round(v, 3) for v in o.matrix_world.translation])
torso = [o for o in obs if o.get("tiow_category") == "Chests"][0]; pad = [o for o in obs if o.get("tiow_category") == "Shoulder Pads"][0]
arm = [o for o in obs if o.get("tiow_category") == "Arms"][0]
Mt = np.array(torso.matrix_world)
def stl_obj(p, name):
    d = open(p, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    V = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].reshape(-1, 3)
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
    me.loops.add(len(V)); me.loops.foreach_set("vertex_index", np.arange(len(V)))
    me.polygons.add(n); me.polygons.foreach_set("loop_start", np.arange(0, len(V), 3)); me.polygons.foreach_set("loop_total", np.full(n, 3))
    me.update(); me.validate(); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=1e-5); bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False); return ob
P = np.load("/home/claude/work/tilt/ts1_chest_R.npy"); Mts = np.load("/home/claude/work/tilt/mts.npy")
# origin of each shield object at its back centre, in the shield's own frame (X wide, Y out, Z up), so moving/rotating is natural
bc = np.array([31.32, -40.13, 115.73]); O = Mts.copy(); O[:3, 3] = bc; Oi = np.linalg.inv(O)
def shield(name, Mworld_of_frame):
    ob = stl_obj(TS, name); ob.data.transform(Matrix(Oi.tolist())); ob.matrix_world = Matrix(Mworld_of_frame.tolist()); return ob
Vt = np.array([torso.matrix_world @ v.co for v in torso.data.vertices]); Lt = (Vt - Mt[:3, 3]) @ Mt[:3, :3]
cd = np.array([np.sin(np.radians(25)), np.cos(np.radians(25)), 0]); sel = (Lt[:, 2] > 33) & (Lt[:, 2] < 36) & (Lt[:, 0] > 2.5) & (Lt[:, 0] < 5)
kc = np.argmax(np.where(sel, Lt @ cd, -1e9)); C = np.eye(4); C[:3, 1] = Mt[:3, :3] @ cd; C[:3, 2] = Mt[:3, 2]; C[:3, 0] = np.cross(C[:3, 1], C[:3, 2])
C[:3, 3] = Vt[kc] + 0.4 * C[:3, 1]
chest = shield("Tilt Shield - chest R (adjust)", C)
# a start on the pad: the pad's most forward-outward point, shield facing forward-out 30 deg, upright
Vp = np.array([pad.matrix_world @ v.co for v in pad.data.vertices]); dirn = np.array([np.sin(np.radians(30)), np.cos(np.radians(30)), 0])
dirw = Mt[:3, :3] @ dirn; k = np.argmax(Vp @ dirw); up = Mt[:3, 2]
F = np.eye(4); F[:3, 1] = dirw; F[:3, 2] = up; F[:3, 0] = np.cross(dirw, up); F[:3, 3] = Vp[k] + 0.3 * dirw
padsh = shield("Tilt Shield - on the pad R (place)", F)
for ob, c in ((torso, rend.GREY), (arm, rend.GREY), (pad, rend.BLUE), (chest, rend.ORANGE), (padsh, rend.GREEN)): ob.color = c
bpy.context.view_layer.update()
for ob in (chest, padsh): ob.data.update(); ob.update_tag()
bpy.context.evaluated_depsgraph_get().update()
cam = rend.setup(bpy.context.scene, 560)
views = {"front": (0, 1, 0), "right": (1, 0, 0), "top": (0, 0.3, 1), "frontright": (0.7, 0.7, 0.15)}
f = rend.render(bpy.context.scene, OUT, "ts", [torso, arm, pad, chest, padsh], views, [rend.GREY, rend.GREY, rend.BLUE, rend.ORANGE, rend.GREEN], frame=torso.matrix_world)
for c in ("cam",): bpy.data.objects.remove(bpy.data.objects[c])
bpy.context.scene.unit_settings.scale_length = 0.001; bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
bpy.ops.object.select_all(action='DESELECT'); chest.select_set(True); bpy.context.view_layer.objects.active = chest
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/Tilt shields - place by eye.blend", compress=True)
print("saved", f)
