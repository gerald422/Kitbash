import bpy, re
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/actual.blend", load_ui=False)
kw = re.compile(r"umbra|plasma|volkite|carsoran|banestrike|las ?cannon|melta|flamer|grav|disintegrator|archaeotech|kraken|nemesis|combi|pattern[CPS]|heresy|springles|hw |cannon", re.I)
for ob in bpy.data.objects:
    if kw.search(ob.name) or (ob.parent and kw.search(ob.parent.name)):
        print(ob.type, repr(ob.name), "parent", ob.parent.name if ob.parent else None, "coll", [c.name for c in ob.users_collection][:2], "ws_type", ob.get("ws_type"))
