"""Blender with Part Sockets + TIOW Inbox 1.6 over the real-file test library (reallib)."""
import bpy, json, math, os, sys, tempfile, time
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
LIB = "/home/claude/test/reallib"
AM = "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL"
VBS = "All Mar All the time/VeteranBladeSquad/VeteranBladeSquad"
MA = "51 May 2026-20260612T074408Z-3-001/51 May 2026/legs-chin pads and base"
TN = "TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Pauldrons"
A = lambda m: np.array([list(r) for r in m], float)
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
def ang(a, b):
    R = A(a)[:3, :3] @ A(b)[:3, :3].T
    return math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
# forget anchors copied by earlier runs (the add-on saves them beside the arm)
for root, ds, fs in os.walk(LIB):
    for f in fs:
        if f.endswith(".sockets.json"):
            p = os.path.join(root, f); d = json.load(open(p))
            keep = [s for s in d.get("sockets", []) if not str(s.get("type", "")).startswith("Pad ")]
            if len(keep) != len(d.get("sockets", [])):
                d["sockets"] = keep; json.dump(d, open(p, "w"))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
import shutil
addon_dir = bpy.utils.user_resource('SCRIPTS', path="addons", create=True)
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); inbox = tempfile.mkdtemp(); prefs.inbox_path = inbox
scene = bpy.context.scene; vl = bpy.context.view_layer
rend.setup(scene, 620)
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
    for o in list(vl.objects):
        if o is not None: o.select_set(False)
    if ob is not None: ob.select_set(True)
    vl.objects.active = ob
def sock(part, t): return next((c for c in part.children if c.get("ws_type") == t), None)
MX = Matrix.Scale(-1, 4, (1, 0, 0))
def torso_both(cursor=(200, 0, 0)):
    select(None)
    torso = send("_test/Chests/23-Torso-2.stl", "Chests", cursor)
    shR = sock(torso, "Shoulder R")
    L_local = MX @ (torso.matrix_world.inverted() @ shR.matrix_world) @ MX
    shL = bpy.data.objects.new("23-Torso-2_socket_Shoulder L", None); torso.users_collection[0].objects.link(shL)
    shL["ws_type"] = "Shoulder L"; shL.empty_display_type = 'ARROWS'; shL.parent = torso
    shL.matrix_parent_inverse = torso.matrix_world.inverted(); shL.matrix_world = torso.matrix_world @ L_local
    T._part_sockets()[0].ensure_type(scene, "Shoulder L")
    return torso, shR, shL
