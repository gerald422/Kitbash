"""Hands are hands: arms and hand-held parts with no saved sockets or fits get them from the wrist rules,
across kits (Assault Marines V2 <-> Veteran Squad), both sides, swaps carry the held weapon, cached on re-import."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v18/out"; os.makedirs(OUT, exist_ok=True)
VSB = "All Mar All the time/VeteranSquad/VeteranSquad"
PROTO = json.load(open("/home/claude/kits/vs_rules.json"))
def proto_arm(rel): return M16(PROTO["arms"][rel.split("All Mar All the time/")[1]]["M"])
def local(child, parent): return A(frame(parent).inverted() @ frame(child))
def sidecar(rel):
    p = os.path.join(LIB, os.path.splitext(rel)[0] + ".sockets.json")
    return json.load(open(p)) if os.path.exists(p) else None
import glob
import subprocess; subprocess.run(["python3", "/home/claude/kits/vet/make_vetlib.py"], check=True)   # clean start for VS: kit sidecars only (Shoulder fits, categories), no rule results cached
select(None)
TORSO = f"{AM}/Chest/22-Torso-1.stl"
torso = send(TORSO, "Chests", (0, 0, 0))
# 1. a Veteran Squad arm, no sidecar: Hand R from the rule
select(torso); ARM_VS = f"{VSB}/Arms/Arms-RawSTL/142-Arm-A.stl"
t0 = time.time(); arm = send(ARM_VS, "Arms"); dt = time.time() - t0
ck("VS arm 142 on Shoulder R", arm.parent is not None and arm.parent.get("ws_type") == "Shoulder R", T._state["last"])
h = sock(arm, "Hand R")
ck("VS arm 142 got a Hand R socket from the rule", h is not None and h.get("tiow_anchor") == "rule", T._state["last"])
if h is not None:
    ck("  ...where the prototype put it", close(local(h, arm), proto_arm(ARM_VS), 0.1, 0.005), f"{ang(local(h, arm), proto_arm(ARM_VS)):.3f} deg")
sc = sidecar(ARM_VS)
ck("  ...and saved in its sidecar", bool(sc) and any(s["type"] == "Hand R" and s["props"].get("tiow_anchor") == "rule" for s in sc["sockets"]), sc)
print(f"      import with wrist rule took {dt:.1f}s")
# 2. an Assault Marines weapon (Josh's fit) on the VS arm
select(arm); w1 = send(f"{AM}/Melee/175-ChainSword-1-R.stl", "Melee")
ck("AM-V2 chainsword on the VS arm's Hand R", w1.parent is h, T._state["last"])
want = A(h.matrix_world) @ M16(side(f"{AM}/Melee/175-ChainSword-1-R.stl")["fits"]["Hand R"])
ck("  ...placed by its own fit", close(A(w1.matrix_world), want, 0.05, 0.01), f"{ang(A(w1.matrix_world), want):.3f}")
snapA = {"wide": A(w1.matrix_world)}
# 3. a VS weapon with no side in its name and no fit: side and fit from the fist
select(arm); t0 = time.time(); w2 = send(f"{VSB}/Melee/Melee-RawSTL/130-ChainSword-B.stl", "Melee"); dt = time.time() - t0
ck("VS chainsword B (no side, no fit) on Hand R", w2.parent is h, T._state["last"])
ck("  ...swapped out the AM-V2 chainsword", "175-ChainSword-1-R" not in bpy.data.objects or T._part_sockets()[1].snap_socket_of(bpy.data.objects["175-ChainSword-1-R"]) is None)
sc = sidecar(f"{VSB}/Melee/Melee-RawSTL/130-ChainSword-B.stl")
ck("  ...fit saved in its sidecar, marked ruled", bool(sc) and "Hand R" in sc.get("fits", {}) and sc.get("ruled", {}).get("Hand R") == T.WRIST_RULE, sc)
print(f"      import with hand rule (both sides tried) took {dt:.1f}s")
# 4. lefts: VS mirrored arm, VS mirrored sword
select(torso); armL = send(f"{VSB}/Arms/Arms-Mirrored/142-Arm-A-Mirrored.stl", "Arms")
ck("VS arm 142 mirrored on Shoulder L", armL.parent is not None and armL.parent.get("ws_type") == "Shoulder L", T._state["last"])
hL = sock(armL, "Hand L")
ck("  ...Hand L from the rule, turned as its right-hand twin", hL is not None and hL.get("tiow_anchor") == "rule" and "mirrored" in T._state["last"], T._state["last"])
select(armL); wL = send(f"{VSB}/Melee/Melee-Mirrored/132-Sword-B-Mirrored.stl", "Melee")
ck("VS sword B mirrored on Hand L", wL.parent is hL, T._state["last"])
# mirror check: the left build is the mirror image of the right one (same arm, same make of hand)
select(arm); wR = send(f"{VSB}/Melee/Melee-RawSTL/132-Sword-B.stl", "Melee")
MXm = np.diag([-1.0, 1, 1, 1])
l = local(wL, torso); r = local(wR, torso)
ck("left sword is the mirror image of the right sword (arm twin rule)", close(l, MXm @ r @ MXm, 2.0, 0.4), f"{ang(l, MXm @ r @ MXm):.2f} deg {np.linalg.norm(l[:3,3]-(MXm@r@MXm)[:3,3]):.3f} mm")
snap_vs = [o for o in vl.objects if o.type == 'MESH' and not o.hide_get()]
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.25), "side": (1, 0, 0.05)}
rend.render(scene, OUT, "vs_arms_rule", snap_vs, V, [rend.GREY] * len(snap_vs))
# 5. swap the VS arm for an AM-V2 arm (Josh's Hand R): the held sword moves across
select(torso); arm2 = send(f"{AM}/Arms/77-Arm-1-R-B.stl", "Arms")
ck("AM-V2 arm 77 replaces the VS arm", arm2.parent is not None and arm2.parent.get("ws_type") == "Shoulder R", T._state["last"])
h2 = sock(arm2, "Hand R")
ck("  ...its own Hand R (Josh's), not a rule one", h2 is not None and h2.get("tiow_anchor") != "rule")
held = [o for o in vl.objects if o.type == 'MESH' and T._part_sockets()[1].snap_socket_of(o) is h2]
ck("  ...the VS sword moved across", len(held) == 1 and held[0].name.startswith("132-Sword-B"), [o.name for o in held])
# 6. an AM-V2 arm whose sidecar Hand socket is taken away: rule socket instead, AM-V2 pistol on it
p = os.path.join(LIB, f"{AM}/Arms/92-Arm-4-R-B.sockets.json"); keep = open(p).read()
d = json.loads(keep); josh_hand = M16(next(s for s in d["sockets"] if s["type"] == "Hand R")["matrix"])
d["sockets"] = [s for s in d["sockets"] if s["type"] != "Hand R"]; json.dump(d, open(p, "w"))
try:
    select(torso); a92 = send(f"{AM}/Arms/92-Arm-4-R-B.stl", "Arms")
    h92 = sock(a92, "Hand R")
    ck("AM-V2 arm 92 without its Hand R gets one from the rule", h92 is not None and h92.get("tiow_anchor") == "rule", T._state["last"])
    if h92 is not None:
        L = local(h92, a92)
        Rj = josh_hand[:3, :3] / np.linalg.norm(josh_hand[:3, :3], axis=0)
        ck("  ...within 3 deg / 0.3 mm of Josh's", ang(L[:3, :3], Rj) < 3 and np.linalg.norm(L[:3, 3] - josh_hand[:3, 3]) < 0.3, f"{ang(L[:3,:3], Rj):.2f} deg {np.linalg.norm(L[:3,3]-josh_hand[:3,3]):.3f} mm")
    select(a92); pi = send(f"{AM}/Pistols/211-BoltPistol-R.stl", "Pistols")
    ck("bolt pistol on the rule Hand R", pi.parent is h92, T._state["last"])
finally:
    open(p, "w").write(keep)
    forget = os.path.join(LIB, f"{AM}/Arms/92-Arm-4-R-B.sockets.json")
# 7. re-import: the VS chainsword's fit now comes from its sidecar (fast)
select(a92); t0 = time.time(); w3 = send(f"{VSB}/Melee/Melee-RawSTL/130-ChainSword-B.stl", "Melee"); dt = time.time() - t0
ck("re-import uses the saved fit", w3.parent is h92 and dt < 2.5, f"{dt:.1f}s {T._state['last']}")
ck("  ...the same placement as the rule gave", "ws_fit::Hand R" in w3.keys())
obs = [o for o in vl.objects if o.type == 'MESH' and not o.hide_get()]
rend.render(scene, OUT, "mixed_rule", obs, V, [rend.GREY] * len(obs))
print("FAILS:", fails)
