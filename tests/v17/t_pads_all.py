"""Every Assault arm and power fist: does its Pad anchor copy on import?"""
exec(open("/home/claude/test/v17/common17.py").read())
import glob
prefs.auto_snap = False
files = sorted(glob.glob(os.path.join(LIB, AM, "Arms", "*.stl"))) + sorted(glob.glob(os.path.join(LIB, AM, "PowerFist", "*.stl"))) + sorted(glob.glob(os.path.join(LIB, AM, "PowerFist", "Mirrored", "*.stl")))
bad = []
for f in files:
    rel = os.path.relpath(f, LIB)
    select(None); p = send(rel, "Arms", (0, 0, 0))
    has = [c.get("ws_type") for c in p.children if str(c.get("ws_type", "")).startswith("Pad ")]
    if not has: bad.append(os.path.basename(f))
    for o in [p] + list(p.children): bpy.data.objects.remove(o)
print("\nNO ANCHOR:", len(bad), bad)
