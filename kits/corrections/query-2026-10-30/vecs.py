import bpy, json, math
from mathutils import Matrix
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_enable(module="tiow_inbox")
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/query.blend")
import tiow_inbox as T
tor = next(o for o in bpy.data.objects if o.get("tiow_category") == "Chests")
tW = T._unscaled(tor.matrix_world)
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.get("tiow_src") or o is tor: continue
    sock, tname, gap = T._snap_of(o)
    unit = float(o.get("tiow_unit", 1.0))
    fit = o.get("ws_fit::" + tname)
    want = sock.matrix_world @ Matrix.Translation((0, 0, gap)) @ T._m16(list(fit))
    got = T._unscaled(o.matrix_world)
    dW = (got.translation - want.translation) / unit          # world
    dT = tW.to_3x3().inverted() @ dW                          # torso frame
    dS = sock.matrix_world.to_3x3().normalized().inverted() @ dW
    R = (got.to_3x3() @ want.to_3x3().inverted())
    ax, an = R.to_quaternion().to_axis_angle()
    print("%-44s %-10s torso(%6.2f %6.2f %6.2f) sock(%6.2f %6.2f %6.2f) rot %5.1f axis_torso(%5.2f %5.2f %5.2f) parent=%s" % (o.name[:44], tname, *dT, *dS, math.degrees(an), *(tW.to_3x3().inverted() @ ax).normalized(), o.parent.name if o.parent else None))
