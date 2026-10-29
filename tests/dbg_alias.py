import bpy, sys
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/actual.blend", load_ui=False)
ob = bpy.data.objects
c = ob["115-CombiWeapon-3-B"]
co = next(m for n, m in sys.modules.items() if n.endswith("part_sockets.core"))
print("hide", c.hide_get(), "hide_viewport", c.hide_viewport, "in vl", c.name in bpy.context.view_layer.objects)
print("parent", c.parent and c.parent.name, "ref", c.ws_snap_sock_ref, "str", c.get("ws_snap_sock"), "type", c.get("ws_snap_type"))
print("snap_socket_of", co.snap_socket_of(c))
for k in ("1-Helmet-1", "55-JumpPack-1", "Backpack2"):
    o = ob[k]; print(k, "hide", o.hide_get(), "sock", co.snap_socket_of(o) and co.snap_socket_of(o).name)
