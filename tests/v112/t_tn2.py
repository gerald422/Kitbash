"""TIOW Inbox 1.12.1 / Turtle Ninja extras: pack toppers on Back Top (TN and Mar Fil packs both ways), the merged Mk6 pack,
Mk7 power fists (left arms, no side in the name), the Mk4 lightning claws over their arm, jump-pack terrain on its anchor."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v112/out"
TN = "Turtle Ninja/"
T6 = TN + "TurtleNinja's Mk2-6 Builder/Mk6/Powerpacks/"; T4 = TN + "TurtleNinja's Mk4 Tactical Squad/Powerpacks/"
TOR = TN + "TurtleNinja's Mk7-8 Assault Intercessors Addon 1/Torsos/Mk7_Torso_Jumppack_A_9.stl"
ARMS7 = TN + "TurtleNinja's Mk7-8 Assault Intercessors Addon 1/Arms/"
SA = TN + "TurtleNinja's Mk4 Tactical Squad/Weapons/Single Arm/"
JL = TN + "TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Jumppack Intercessor/"
VET = "All Mar All the time/VeteranSquad/VeteranSquad/Backpacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/"
AMT = f"{AM}/Chest/22-Torso-1.stl"
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def alive(o):
    try: return o is not None and o.name in bpy.data.objects and vl.objects.get(o.name) is not None
    except ReferenceError: return False
def sc_of(ob): return json.load(open(os.path.splitext(ob["tiow_src"])[0] + ".sockets.json"))
def expect(part, host_sock_ob, fit_type): return A(host_sock_ob.matrix_world) @ M16(sc_of(part)['fits'][fit_type])
def at(part, E, deg=0.05, mm=0.01): return close(A(frame(part)), E, deg, mm)
# 1 TN torso + Mk6 pack + toppers
select(None); t = send(TOR, "Bodies", (0, 0, 0))
pk = send(T6 + "Mk6 Powerpack 1.stl", "Backpacks")
ck("1 Mk6 pack on Back", on(pk, "Back"), T._state["last"])
ck("1 the pack has a Back Top", sock(pk, "Back Top") is not None)
select(pk); b = send(T6 + "Powerpack Banner 1.stl", "Backpacks")
ck("1 banner on the pack's Back Top", on(b, "Back Top") and b.parent.parent is pk, T._state["last"])
if on(b, "Back Top"): ck("1 banner where its fit puts it", at(b, expect(b, b.parent, "Back Top")))
select(pk); v = send(T4 + "Mk4_Powerpack_Voxcaster.stl", "Backpacks")
ck("1 vox caster replaces the banner", on(v, "Back Top") and not alive(b), T._state["last"])
select(pk); m7 = send(VET + "7.stl", "Backpacks")
ck("1 Mar Fil topper 7 on the TN pack's Back Top", on(m7, "Back Top") and m7.parent.parent is pk and not alive(v), T._state["last"])
# 2 Mk4 pack + its vox caster: exactly as Turtle Ninja exported them together (0.15 mm by the rule)
select(None); t2 = send(TOR, "Bodies", (40, 0, 0)); p4 = send(T4 + "Mk4_Powerpack_1.stl", "Backpacks")
select(p4); v4 = send(T4 + "Mk4_Powerpack_Voxcaster.stl", "Backpacks")
ck("2 Mk4 vox on the Mk4 pack", on(v4, "Back Top"), T._state["last"])
if on(v4, "Back Top"): ck("2 vox as exported with the pack", close(A(frame(v4)), A(frame(p4)), 0.1, 0.15), (np.round(A(frame(v4))[:3, 3] - A(frame(p4))[:3, 3], 3), ang(A(frame(v4)), A(frame(p4)))))
# 3 TN banner on Mar Fil Vet pack 1 on the AM torso
select(None); t3 = send(AMT, "Bodies", (80, 0, 0)); vp = send(VET + "1.stl", "Backpacks")
select(vp); b3 = send(T6 + "Powerpack Banner 1.stl", "Backpacks")
ck("3 TN banner on the Mar Fil pack's Back Top", on(b3, "Back Top") and b3.parent.parent is vp, T._state["last"])
# 4 the merged Mk6 pack (pack + vox, 0.92 scale) on Back, like Mk6 Powerpack 1
select(t); pp = send(T6 + "Powerpack 1.stl", "Backpacks")
ck("4 Powerpack 1 on Back, replacing the Mk6 pack", on(pp, "Back") and not alive(pk), T._state["last"])
# 5 Mk7 power fists: left arms (no side in the name)
for n in ("Mk7_Powerfist_A_1", "Mk7_Powerfist_B_11"):
    select(t); f = send(ARMS7 + n + ".stl", "Arms")
    ck(f"5 {n} on Shoulder L", on(f, "Shoulder L"), T._state["last"])
    if on(f, "Shoulder L"): ck(f"5 {n} where its fit puts it", at(f, expect(f, f.parent, "Shoulder L")))
select(t); ar = send(ARMS7 + "Mk7_Arm_Single_A_1.stl", "Arms")
ck("5 Mk7 arm single on Shoulder R (its fit's side)", on(ar, "Shoulder R"), T._state["last"])
select(t); ar2 = send(SA + "Mk4_Lightning_Powerfist_A.stl", "Arms")
ck("5 a second R-only arm swaps the right arm, never parks on the left", on(ar2, "Shoulder R") and not alive(ar), T._state["last"])
fl = [o for o in vl.objects if o is not None and str(o.get("tiow_src", "")).endswith("Mk7_Powerfist_B_11.stl")]
ck("5 the power fist stays on the left", len(fl) == 1 and on(fl[0], "Shoulder L"))
# 6 Mk4 lightning claws over the open hand of their arm
select(t2); la = send(SA + "Mk4_Lightning_Powerfist_A.stl", "Arms")
ck("6 claw arm on Shoulder R", on(la, "Shoulder R"), T._state["last"])
ck("6 claw arm has its Hand R", sock(la, "Hand R") is not None)
select(la); cl = send(SA + "Mk4_Lightning_Claws.stl", "Weapons")
ck("6 claws on the arm's Hand R", on(cl, "Hand R") and cl.parent.parent is la, T._state["last"])
if on(cl, "Hand R"):
    CA = np.array(json.load(open('/home/claude/kits/tn/lc/wrist_axis.json'))['CA'])
    ck("6 claws where Turtle Ninja's merged arm has them", at(cl, A(frame(la)) @ CA, 0.05, 0.02), np.round(A(frame(cl))[:3, 3] - (A(frame(la)) @ CA)[:3, 3], 3))
# 7 jump-pack terrain on its anchor, exactly where it was exported with the legs; a round base on the usual Base
select(t2); jl = send(JL + "Legs/Mk10_Assault_Booster_Legs_Jumping_Pose_1_A_1.stl", "Legs")
ck("7 jump legs on Flat Waist", on(jl, "Flat Waist"), T._state["last"])
select(jl); tr = send(JL + "Terrain/Jumppack_Terrain_1.stl", "Bases")
print("anchor", tr.parent.name, dict(tr.parent.items()).keys()); ck("7 terrain on the legs' terrain anchor", on(tr, "Base") and "Jumppack_Terrain_1" in str(tr.parent.get("tiow_holds", "")), T._state["last"])
if on(tr, "Base"): ck("7 terrain as exported with the legs", at(tr, A(frame(jl)), 0.05, 0.01), np.round(A(frame(tr))[:3, 3] - A(frame(jl))[:3, 3], 3))
select(jl); rk = send("Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/Rocks-Raw/283-Rock-16.stl", "Bases")
ck("7 a round base goes on the usual Base, terrain stays", on(rk, "Base") and not rk.parent.get("tiow_holds") and alive(tr), T._state["last"])
select(jl); tr2 = send(JL + "Terrain/Jumppack_Terrain_2.stl", "Bases")
ck("7 another terrain swaps the terrain, not the base", on(tr2, "Base") and not alive(tr) and alive(rk), T._state["last"])
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "back": (-0.4, -1, 0.25)}
for nm, root in (("toppers_fists", t), ("mk4_claw_terrain", t2), ("mf_pack_tn_banner", t3)):
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "tn2_" + nm, obs, V, [rend.ORANGE if "Turtle Ninja" in str(o.get("tiow_src", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
