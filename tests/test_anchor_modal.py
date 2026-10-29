"""The Place Anchor click loop, driven with fake clicks (no screen here)."""
import bpy, sys, types
from mathutils import Vector
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else f"  {d}")); c or fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=False)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
cube = bpy.data.objects["Cube"]
ck("operator registered", hasattr(bpy.ops.tiow, "place_anchor") and hasattr(bpy.ops.tiow, "save_folder_fit"))
Op = T.TIOW_OT_place_anchor
msgs = []
fake = types.SimpleNamespace(anchor="Shin R", report=lambda k, m: msgs.append(m))
ck("started outside the 3D View: refused with a message", Op.invoke(fake, types.SimpleNamespace(area=None), None) == {'CANCELLED'} and "3D View" in msgs[0], msgs)
def run(anchor, hits):
    st = types.SimpleNamespace(anchor=anchor, pts=[], nrms=[], part=None, msgs=[])
    seq = iter(hits)
    st._hit = lambda ctx, ev: next(seq)
    st._prompt = lambda ctx: None
    st._done = lambda ctx: None
    st.report = lambda kind, msg: st.msgs.append(msg)
    res = None
    for _ in hits:
        ev = types.SimpleNamespace(type='LEFTMOUSE', value='PRESS')
        res = Op.modal(st, bpy.context, ev)
    return res, st
# Shin: ankle circle, other ankle circle, top of the hole (cube's front face, y = -1)
r, st = run("Shin R", [(cube, Vector((0.5, -1, -0.8)), Vector((0, -1, 0))), (cube, Vector((-0.5, -1, -0.8)), Vector((0, -1, 0))),
                       (cube, Vector((0, -1, 0.6)), Vector((0, -1, 0)))])
s = next((c for c in cube.children if c.get("ws_type") == "Shin R"), None)
ck("three clicks make a Shin R socket", r == {'FINISHED'} and s is not None, (r, st.msgs))
M = s.matrix_world if s else None
ck("on the third (hole top) click, Y up the shin, Z out of its front", s and (M.translation - Vector((0, -1, 0.6))).length < 1e-5
   and (M.to_3x3() @ Vector((0, 1, 0))).z > 0.99 and (M.to_3x3() @ Vector((0, 0, 1))).y < -0.99, M)
r, st = run("Shin R", [(cube, Vector((0.5, -1, -0.8)), Vector((0, -1, 0))), (cube, Vector((-0.5, -1, -0.8)), Vector((0, -1, 0)))])
ck("two clicks only: still waiting for the hole", r == {'RUNNING_MODAL'})
# Pad: front corner, back corner, top by the joint (cube's +X face; the cube's own Y is forward)
r, st = run("Pad R", [(cube, Vector((1, 0.6, 0.0)), Vector((1, 0, 0))), (cube, Vector((1, -0.6, 0.2)), Vector((1, 0, 0))),
                      (cube, Vector((0.6, 0.0, 1.0)), Vector((0, 0, 1)))])
s = next((c for c in cube.children if c.get("ws_type") == "Pad R"), None)
ck("three clicks make a Pad R socket", r == {'FINISHED'} and s is not None, (r, st.msgs))
M = s.matrix_world if s else None
ck("Pad: origin on the top point, Y forward along the corners, X out", s and (M.translation - Vector((0.6, 0, 1))).length < 1e-5
   and (M.to_3x3() @ Vector((0, 1, 0))).y > 0.9 and (M.to_3x3() @ Vector((1, 0, 0))).x > 0.4, M)
ck("Pad: the clicked points are kept with it", s and len(__import__("json").loads(s["tiow_points"])) == 3)
r, st = run("Hip R", [None, (cube, Vector((1, 0, 0)), Vector((1, 0, 0)))])
ck("a miss is ignored, the next click places Hip R", r == {'FINISHED'} and any(c.get("ws_type") == "Hip R" for c in cube.children), st.msgs)
ev = types.SimpleNamespace(type='ESC', value='PRESS')
st = types.SimpleNamespace(anchor="Shin L", pts=[], nrms=[], part=None, _done=lambda c: None)
ck("Esc cancels", Op.modal(st, bpy.context, ev) == {'CANCELLED'})
print(f"\n{len(fails)} failure(s)"); sys.exit(1 if fails else 0)
