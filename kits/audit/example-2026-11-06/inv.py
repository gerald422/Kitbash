import bpy, json, sys
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/example issues.blend")
print("SCENE unit", bpy.context.scene.unit_settings.scale_length, "objects", len(bpy.data.objects))
out = []
for o in bpy.data.objects:
    d = {"name": o.name, "type": o.type, "parent": o.parent.name if o.parent else None,
         "hide": o.hide_get() if o.name in bpy.context.view_layer.objects else None,
         "coll": [c.name for c in o.users_collection], "M": [list(r) for r in o.matrix_world]}
    for k in o.keys():
        if k.startswith("tiow_") or k.startswith("ws_"):
            v = o[k]
            try: json.dumps(v); d[k] = v
            except TypeError: d[k] = list(v) if hasattr(v, "__len__") else str(v)
    out.append(d)
json.dump(out, open("objs.json", "w"), indent=1)
for d in out:
    if d["type"] == "MESH":
        print("%-55s %-16s snap=%-14s tgt=%-28s model=%s hide=%s" % (d["name"][:55], d.get("tiow_category"), d.get("ws_snap_type"), d.get("tiow_target"), d.get("tiow_model"), d["hide"]))
print("--- empties")
for d in out:
    if d["type"] != "MESH":
        print("%-40s %-6s parent=%s" % (d["name"][:40], d["type"], d["parent"]))
