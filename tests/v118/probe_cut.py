exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out2"; os.makedirs(OUT, exist_ok=True)
rend.setup(scene, 640)
VW = {"front": (0, 1, 0.05), "side": (1, 0, 0.05), "q": (0.7, 0.7, 0.2)}
def shot(name, root, extra=()):
    vl.update()
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get() and o.display_type != 'WIRE']
    cols = [rend.ORANGE if o.get("tiow_bionic_role") == "plug" else rend.BLUE if o.get("tiow_bionic") else rend.GREY for o in obs]
    rend.render(scene, OUT, name, obs, VW, cols)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
select(torso); send(f"{AM}/Arms/106-Arm-7-R-A.stl", "Arms")
select(legs); bpy.ops.tiow.bionic_leg(side='R'); print("BELT:", T._state["last"]); shot("m29_belt", torso)
P = T.bio_parts(legs, "R"); P["thigh"].hide_set(True); P["shin"].hide_set(True); P["foot"].hide_set(True); shot("m29_belt_cut", legs)
for r in ("thigh", "shin", "foot"): P[r].hide_set(False)
select(legs); bpy.ops.tiow.bionic_cut(side='R', where="thigh"); print("THIGH:", T._state["last"]); shot("m29_thigh", torso)
select(legs); bpy.ops.tiow.bionic_cut(side='R', where="belt"); bpy.ops.tiow.bionic_leg(side='L'); print("BELT L:", T._state["last"]); shot("m29_both", torso)
# jump legs
select(None); t2 = send(f"{AM}/Chest/23-Torso-2.stl", "Chests", (60, 0, 0))
select(t2); l2 = send(f"{AM}/Legs(JumpPack)/37-Legs-3-A.stl", "Legs")
select(l2); bpy.ops.tiow.bionic_leg(side='R'); print("JUMP:", T._state["last"]); shot("m37_belt", t2)
# Springles legs: cut, and the one-legged piece's ball
SPR = "/home/claude/test/v118/spr"
for i, (f, side) in enumerate([("mk6 UA patternH R melee 1", "L"), ("mk6 UA patternH L ranged 1", "R"), ("mk6 UA patternP R step up", "L"), ("mk6 UA bionic joint R melee 1", "R")]):
    select(None); scene.cursor.location = (0, 80 + 40 * i, 0)
    with open(os.path.join(inbox, f"s{i}.json"), "w") as fh:
        json.dump({"path": os.path.join(SPR, f + ".stl"), "category": "Legs", "name": f}, fh)
    T.process_inbox(); sl = vl.objects.active
    select(sl)
    try:
        r = bpy.ops.tiow.bionic_leg(side=side)
    except RuntimeError as exc:
        r = str(exc)
    print("SPRINGLES", f, side, r, T._state["last"])
    shot(f"spr_{i}", sl)
