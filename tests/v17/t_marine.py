"""Build Assault Marines from scratch through the inbox: torso, legs, arms, hand weapons both sides, helmet,
jump pack and fins, a two-handed weapon that clears both arms, an arm that replaces it. Checks every placement
against the sidecar maths and renders."""
exec(open("/home/claude/test/v17/common17.py").read())
OUT = "/home/claude/test/v17/out"; os.makedirs(OUT, exist_ok=True)
def rel_pose(child, parent): return A(frame(parent).inverted() @ frame(child))
def expect(label, part, host, sockname, fitname, child_rel):
    s = M16(next(x for x in side(host)['sockets'] if x['type'] == sockname)['matrix'])
    f = M16(side(child_rel)['fits'][fitname])
    got = rel_pose(part, hp)
    want = s @ f
    ck(label, close(got, want, 0.05, 0.01), f"off {ang(got, want):.3f} deg {np.linalg.norm(got[:3,3]-want[:3,3]):.4f} mm")
select(None)
TORSO = f"{AM}/Chest/24-Torso-3.stl"
torso = send(TORSO, "Chests", (0, 0, 0))
ck("torso has Shoulder R/L, Neck, Back, Waist", all(sock(torso, t) for t in ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist")))
parts = {}
def put(host_ob, host_rel, rel, cat, sockname, label):
    global hp
    select(host_ob); p = send(rel, cat); hp = host_ob
    ok = p is not None and p.parent is not None and p.parent.get("ws_type") == sockname
    ck(f"{label}: on {sockname}", ok, T._state["last"])
    if ok: expect(f"{label}: placed by its fit", p, host_rel, sockname, sockname, rel)
    parts[label] = p
    return p
legs = put(torso, TORSO, f"{AM}/Legs/30-Legs-3.stl", "Legs", "Waist", "legs 30")
armR = put(torso, TORSO, f"{AM}/Arms/106-Arm-7-R-A.stl", "Arms", "Shoulder R", "arm 106 R")
armL = put(torso, TORSO, f"{AM}/Arms/109-Arm-7-L-B.stl", "Arms", "Shoulder L", "arm 109 L")
put(armR, f"{AM}/Arms/106-Arm-7-R-A.stl", f"{AM}/Melee/202-PowerSword-A-1-R.stl", "Melee", "Hand R", "sword R")
put(armL, f"{AM}/Arms/109-Arm-7-L-B.stl", f"{AM}/Pistols/LeftOrientated/Weapons-Assault211-BoltPistol-L.stl", "Pistols", "Hand L", "pistol L")
put(torso, TORSO, f"{AM}/Helmet-Heads/3-Helmet-3.stl", "Heads", "Neck", "helmet 3")
pack = put(torso, TORSO, f"{AM}/JumpPacks/56-JumpPack-2.stl", "Jump Packs", "Back", "jump pack 56")
select(pack); f1 = send(f"{AM}/JumpPacks/60-Fin-1.stl", "Jump Packs")
ck("fin 1 on a Pack Fin socket", f1.parent is not None and str(f1.parent.get("ws_type", "")).startswith("Pack Fin"), T._state["last"])
select(pack); f2 = send(f"{AM}/JumpPacks/60-Fin-1.stl", "Jump Packs")
ck("fin 2 on the other Pack Fin socket", f2.parent is not None and f2.parent is not f1.parent, T._state["last"])
ck("one fin mirrored", bool(f1.get("tiow_mirrored")) != bool(f2.get("tiow_mirrored")))
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.25), "side": (1, 0, 0.05), "back": (-0.3, -1, 0.2)}
def snap(name):
    obs = [o for o in vl.objects if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, name, obs, V, [rend.GREY] * len(obs))
snap("marine_a")
# two-handed weapon: takes Shoulder R and clears Shoulder L
select(torso); tw = send(f"{AM}/TwoHandedWeapons/148-PowerAxe-2-1-A.stl", "Weapons")
ck("2H on Shoulder R", tw.parent is not None and tw.parent.get("ws_type") == "Shoulder R", T._state["last"])
gone = [n for n in ("106-Arm-7-R-A", "109-Arm-7-L-B") if n in bpy.data.objects and not bpy.data.objects[n].hide_get() and T._part_sockets()[1].snap_socket_of(bpy.data.objects[n]) is not None]
ck("both arms off the torso", not gone, gone)
snap("marine_b")
# an arm on Shoulder L replaces the two-hander
select(torso); aL = send(f"{AM}/Arms/79-Arm-1-L-B.stl", "Arms")
ck("arm 79 L on Shoulder L", aL.parent is not None and aL.parent.get("ws_type") == "Shoulder L", T._state["last"])
ck("two-hander gone", "148-PowerAxe-2-1-A" not in bpy.data.objects or T._part_sockets()[1].snap_socket_of(bpy.data.objects["148-PowerAxe-2-1-A"]) is None)
# second marine: jump legs 47 (Josh's example) - torso to legs must match his file
select(None); t2 = send(f"{AM}/Chest/23-Torso-2.stl", "Chests", (80, 0, 0))
put(t2, f"{AM}/Chest/23-Torso-2.stl", f"{AM}/Legs(JumpPack)/47-Legs-8-A.stl", "Legs", "Waist", "jump legs 47")
lg = parts["jump legs 47"]
J = json.load(open("/home/claude/kits/legs_josh.json"))["legs"]["AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/47-Legs-8-A.stl"]["M"]
got = A(t2.matrix_world.inverted() @ lg.matrix_world)
ck("47: torso on the legs exactly as in posing for claude.blend", close(got, M16(J), 0.05, 0.01), f"{ang(got, M16(J)):.3f} deg")
put(t2, f"{AM}/Chest/23-Torso-2.stl", f"{AM}/Arms/126-Arm-11-R-A.stl", "Arms", "Shoulder R", "arm 126 R")
put(t2, f"{AM}/Chest/23-Torso-2.stl", f"{AM}/Arms/128-Arm-11-L-A.stl", "Arms", "Shoulder L", "arm 128 L")
put(parts["arm 126 R"], f"{AM}/Arms/126-Arm-11-R-A.stl", f"{AM}/Melee/195-PowerHammer-A-3-R.stl", "Melee", "Hand R", "hammer R (shared grip)")
put(parts["arm 128 L"], f"{AM}/Arms/128-Arm-11-L-A.stl", f"{AM}/Melee/LeftOrientated/190-PowerAxe-C-1-L.stl", "Melee", "Hand L", "axe L")
put(t2, f"{AM}/Chest/23-Torso-2.stl", f"{AM}/Helmet-Heads/12-Head-4.stl", "Heads", "Neck", "head 12")
p2 = put(t2, f"{AM}/Chest/23-Torso-2.stl", f"{AM}/JumpPacks/57-JumpPack-3.stl", "Jump Packs", "Back", "jump pack 57")
for i in range(2):
    select(p2); send(f"{AM}/JumpPacks/61-Fin-2.stl", "Jump Packs")
# third: mirrored jump legs and power fists
select(None); t3 = send(f"{AM}/Chest/26-Torso-5.stl", "Chests", (160, 0, 0))
put(t3, f"{AM}/Chest/26-Torso-5.stl", f"{AM}/Legs(JumpPack)/Mirrored/Mirrored-39-Legs-4-A.stl", "Legs", "Waist", "mirrored jump legs 39")
put(t3, f"{AM}/Chest/26-Torso-5.stl", f"{AM}/PowerFist/163-PowerFist-A-2.stl", "Weapons", "Shoulder R", "power fist R")
put(t3, f"{AM}/Chest/26-Torso-5.stl", f"{AM}/PowerFist/Mirrored/Mirrored-170-PowerFist-B-4.stl", "Weapons", "Shoulder L", "power fist L")
put(t3, f"{AM}/Chest/26-Torso-5.stl", f"{AM}/Helmet-Heads/7-Helmet-7.stl", "Heads", "Neck", "helmet 7")
put(t3, f"{AM}/Chest/26-Torso-5.stl", f"{AM}/JumpPacks/59-JumpPack-5.stl", "Jump Packs", "Back", "jump pack 59")
for nm, ob in (("m1", torso), ("m2", t2), ("m3", t3)):
    root = ob
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "kit_" + nm, obs, {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05), "back": (-0.4, -1, 0.25)}, [rend.GREY] * len(obs))
print("\nFAILS:", fails)
