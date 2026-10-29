"""Blender with Part Sockets + TIOW Inbox 1.7 over the kit test library (kitlib)."""
import bpy, json, math, os, sys, tempfile, time
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
LIB = "/home/claude/test/kitlib"
AM = "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL"
A = lambda m: np.array([list(r) for r in m], float)
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
def ang(a, b):
    R = A(a)[:3, :3] @ A(b)[:3, :3].T
    return math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
def close(a, b, deg=0.05, mm=0.01):
    a, b = A(a), A(b); return ang(a, b) < deg and np.linalg.norm(a[:3, 3] - b[:3, 3]) < mm
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); inbox = tempfile.mkdtemp(); prefs.inbox_path = inbox
scene = bpy.context.scene; vl = bpy.context.view_layer
rend.setup(scene, 620)
_n = [0]
def send(rel, cat="Weapons", cursor=None):
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
def side(rel):
    p = os.path.join(LIB, os.path.splitext(rel)[0] + ".sockets.json")
    return json.load(open(p))
def M16(m): return np.array(m, float).reshape(4, 4)
def frame(ob):
    l, r, _ = ob.matrix_world.decompose(); return Matrix.LocRotScale(l, r, Vector((1, 1, 1)))
