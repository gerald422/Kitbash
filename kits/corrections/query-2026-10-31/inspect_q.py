import bpy, json, sys, math
from mathutils import Matrix
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/kitbash/addons/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/query.blend")
import tiow_inbox as T
co = T._part_sockets()[1]
rows = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.get("tiow_src"): continue
    try:
        sock, tname, gap = T._snap_of(o)
    except Exception as e:
        rows.append((o.name, o.get("tiow_category"), None, None, str(e)[:60])); continue
    unit = float(o.get("tiow_unit", 1.0)) or 1.0
    fit = o.get("ws_fit::" + tname)
    want = sock.matrix_world @ Matrix.Translation((0, 0, gap)) @ T._scaled(T._m16(list(fit)), 1.0) if fit is not None else None
    got = T._unscaled(o.matrix_world)
    if want is not None:
        D = want.inverted_safe() @ got
        d = D.translation.length / unit; ang = math.degrees(D.to_quaternion().angle)
    else: d = ang = float('nan')
    rows.append((o.name, o.get("tiow_category"), tname, sock.parent.name if sock.parent else None, "%.2f mm %.1f deg" % (d, ang), o.get("tiow_model"), o.get("tiow_src")))
for r in rows: print(" | ".join(str(x) for x in r))
