"""Headless test of tiow_inbox.py against the bpy 5.1.2 wheel."""
import json, os, shutil, struct, sys, tempfile, time
import bpy

ADDON = "/home/claude/tiow_blender/tiow_inbox.py"
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)

def write_stl(path, lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    with open(path, "wb") as fh:
        fh.write(b"\0" * 80 + struct.pack("<I", len(f)))
        for a, b, c in f:
            fh.write(struct.pack("<3f", 0, 0, 0))
            for i in (a, b, c): fh.write(struct.pack("<3f", *v[i]))
            fh.write(b"\0\0")

def job(inbox, path, category="Arms", name=None, age=0):
    p = os.path.join(inbox, f"{int(time.time()*1000)}-{name or os.path.basename(path)}.json")
    with open(p, "w") as fh:
        json.dump({"schemaVersion": 1, "path": path, "name": os.path.basename(path),
                   "category": category, "itemId": "local-x", "tags": ["tac"]}, fh)
    if age:
        t = time.time() - age; os.utime(p, (t, t))
    return p

tmp = tempfile.mkdtemp()
inbox = os.path.join(tmp, "inbox"); os.makedirs(inbox)
stl = os.path.join(tmp, "Arm_R_03.stl"); write_stl(stl, (35, -3, 0), (45, 3, 30))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_install(filepath=ADDON, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs()
ck("addon enabled, prefs resolve", prefs is not None)
prefs.inbox_path = inbox
ck("timer registered", bpy.app.timers.is_registered(T._timer))

scene = bpy.context.scene
scene.unit_settings.scale_length = 0.001
scene.cursor.location = (5, 5, 0)

print("\n== import into a mm scene, centred on cursor")
j = job(inbox, stl)
n = T.process_inbox()
ck("one import", n == 1, n)
ck("request file consumed", not os.path.exists(j) and not [x for x in os.listdir(inbox) if x.endswith((".json", ".claimed"))], os.listdir(inbox))
ck("heartbeat written", os.path.exists(os.path.join(inbox, ".listening")))
ob = bpy.context.view_layer.objects.active
ck("imported object is active", ob is not None and ob.name.startswith("Arm_R_03"), ob)
ck("and selected", ob.select_get())
ck("in collection 'Arms'", [c.name for c in ob.users_collection] == ["Arms"], [c.name for c in ob.users_collection])
ck("Arms linked to scene", "Arms" in scene.collection.children)
xs = [v.co.x for v in ob.data.vertices]
ck("mm scene: mesh unscaled", abs((max(xs) - min(xs)) - 10) < 1e-4, max(xs) - min(xs))
from mathutils import Vector
centre = ob.matrix_world @ ((Vector(ob.bound_box[0]) + Vector(ob.bound_box[6])) * 0.5)
ck("geometry centred on cursor", (centre - scene.cursor.location).length < 1e-4, centre)
ck("custom props", ob.get("tiow_src") == stl and ob.get("tiow_category") == "Arms" and ob.get("tiow_item") == "local-x")
ck("status message", T._state["last"].startswith("Imported Arm_R_03"), T._state["last"])

print("\n== metre scene scales mesh to mm, origin placement")
scene.unit_settings.scale_length = 1.0
prefs.millimetres = True
prefs.placement = 'ORIGIN'
job(inbox, stl, category="")
T.process_inbox()
ob2 = bpy.context.view_layer.objects.active
xs = [v.co.x for v in ob2.data.vertices]
ck("metre scene: 10 mm -> 0.01 units", abs((max(xs) - min(xs)) - 0.01) < 1e-7, max(xs) - min(xs))
ck("object scale stays 1", tuple(round(s, 6) for s in ob2.scale) == (1, 1, 1))
ck("origin at cursor", (ob2.location - scene.cursor.location).length < 1e-6)
ck("empty category -> fallback collection", ob2.users_collection[0].name == "TIOW Imports")
ck("first part deselected", not ob.select_get())
scene.unit_settings.scale_length = 0.001
prefs.millimetres = False
prefs.placement = 'BOUNDS'

print("\n== default 1:1 in a metre scene (matches hand-imported parts)")
scene.unit_settings.scale_length = 1.0
job(inbox, stl); T.process_inbox(); obd = bpy.context.view_layer.objects.active
xs = [v.co.x for v in obd.data.vertices]
ck("default: 10 STL units -> 10 BU", abs((max(xs)-min(xs)) - 10) < 1e-4, max(xs)-min(xs))
scene.unit_settings.scale_length = 0.001

print("\n== excluded existing collection is brought back")
lc = bpy.context.view_layer.layer_collection.children["Arms"]
lc.exclude = True
job(inbox, stl)
T.process_inbox()
ob3 = bpy.context.view_layer.objects.active
ck("imported into Arms again", ob3 is not None and ob3.users_collection[0].name == "Arms" and ob3 not in (ob, ob2))
ck("Arms no longer excluded", not lc.exclude)
ck("still one Arms collection", len([c for c in bpy.data.collections if c.name.startswith("Arms")]) == 1)

print("\n== bad requests")
count = len(bpy.data.objects)
job(inbox, stl, name="stale", age=600)
T.process_inbox()
ck("stale request dropped", len(bpy.data.objects) == count and "stale" in T._state["last"].lower(), T._state["last"])
with open(os.path.join(inbox, "9-bad.json"), "w") as fh: fh.write("{not json")
T.process_inbox()
ck("bad JSON reported, not fatal", "Could not import 9-bad.json" in T._state["last"], T._state["last"])
job(inbox, os.path.join(tmp, "missing.stl"))
T.process_inbox()
ck("missing file reported", "file not found" in T._state["last"], T._state["last"])
job(inbox, os.path.join(tmp, "notes.txt"))
T.process_inbox()
ck("non-STL refused", "not an STL" in T._state["last"], T._state["last"])
ck("inbox empty after bad requests", not [x for x in os.listdir(inbox) if x != ".listening"], os.listdir(inbox))
ck("no objects added by bad requests", len(bpy.data.objects) == count)

print("\n== edit mode leaves requests waiting")
bpy.context.view_layer.objects.active = ob3
bpy.ops.object.mode_set(mode='EDIT')
j = job(inbox, stl)
ck("nothing imported in edit mode", T.process_inbox() == 0)
ck("request still waiting", os.path.exists(j))
bpy.ops.object.mode_set(mode='OBJECT')
ck("imports after leaving edit mode", T.process_inbox() == 1)

print("\n== listening off")
prefs.listening = False
j = job(inbox, stl)
ck("nothing imported when off", T.process_inbox() == 0 and os.path.exists(j))
prefs.listening = True
T.process_inbox()

print("\n== a request claimed by another Blender is skipped")
j = job(inbox, stl)
os.replace(j, j + ".999.claimed")
ck("no import of claimed request", T.process_inbox() == 0)
os.remove(j + ".999.claimed")

print("\n== unregister")
bpy.ops.preferences.addon_disable(module="tiow_inbox")
ck("timer removed", not bpy.app.timers.is_registered(T._timer))

shutil.rmtree(tmp)
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
