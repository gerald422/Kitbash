import bpy, json
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/query.blend")
out = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.get("tiow_src"):
        out.append({"name": o.name, "src": o["tiow_src"], "cat": o.get("tiow_category"), "variant": o.get("tiow_variant"),
                    "snap": o.get("ws_snap_type"), "M": [list(r) for r in o.matrix_world], "model": o.get("tiow_model")})
json.dump(out, open("/home/claude/twoarm/query/parts.json", "w"), indent=1)
