"""TIOW Inbox 1.12: flat waists. Mar Fil torso + flat legs brings the body adaptor; Next Adaptor swaps it; Mar Fil legs replace
adaptor + legs; a Turtle Ninja torso takes flat legs on Flat Waist and Mar Fil legs on Waist, one replacing the other; Mar Fil
arms/helmet/pack on a TN torso; everything where the conventions put it."""
exec(open("/home/claude/test/v18/common18.py").read())
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr')
OUT = "/home/claude/test/v112/out"
prefs.adaptor_dir = os.path.join(LIB, "body adaptor"); prefs.adaptor_default = 3
AMT = f"{AM}/Chest/22-Torso-1.stl"; AML = f"{AM}/Legs/29-Legs-2.stl"
TNT = "Turtle Ninja/TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl"
TNL = ["Turtle Ninja/TurtleNinja's Mk2-6 Builder/Mk6/Legs/Lower A 1.stl", "Turtle Ninja/TurtleNinja's Mk10 Leg (Update 1)/Mk10_2.0_Legs_Pose_2_C_6.stl",
       "Turtle Ninja/TurtleNinja's Mk6 Assault Addon 1/Legs/Mk6_Pose_1_Running_4.stl"]
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def alive(o):
    try: return o is not None and o.name in bpy.data.objects and vl.objects.get(o.name) is not None
    except ReferenceError: return False
def adaptors(): return [o for o in vl.objects if o is not None and o.get("tiow_category") == "Adapters"]
def rel(p, h): return A(frame(h).inverted() @ frame(p))
def expect(part, host, host_sock, fit_type):
    """where the part should be: host socket world @ part fit"""
    S = A(sock(host, host_sock).matrix_world); F = M16(side_of(part)['fits'][fit_type]); return S @ F
def side_of(ob):
    p = os.path.splitext(ob["tiow_src"])[0] + ".sockets.json"; return json.load(open(p))
# 1 Mar Fil torso + TN legs -> adaptor 3, legs on its Flat Waist
select(None); t = send(AMT, "Bodies", (0, 0, 0))
legs = send(TNL[0], "Legs"); ad = adaptors()
ck("1 one adaptor came with the flat legs", len(ad) == 1, len(ad))
ck("1 it is adaptor 3", ad and ad[0]["tiow_src"].endswith("lower_body_(torso)_3.stl"), ad and ad[0]["tiow_src"])
ck("1 adaptor on the torso's Waist", ad and on(ad[0], "Waist"))
ck("1 legs on the adaptor's Flat Waist", on(legs, "Flat Waist") and legs.parent.parent is ad[0], legs.parent and legs.parent.name)
if ad:
    ck("1 adaptor where its Waist fit puts it", close(A(frame(ad[0])), expect(ad[0], t, "Waist", "Waist"), 0.05, 0.01))
    ck("1 legs where the Flat Waist fit puts them", close(A(frame(legs)), expect(legs, ad[0], "Flat Waist", "Flat Waist"), 0.05, 0.01))
ck("1 status says the adaptor was added", "adaptor lower_body_(torso)_3 added" in T._state["last"], T._state["last"])
# 2 Next Adaptor: adaptor 4, legs stay put
w0 = A(frame(legs)); select(legs)
msg = T.next_adaptor(legs, prefs); vl.update(); ad = adaptors()
ck("2 Next Adaptor gives adaptor 4", len(ad) == 1 and ad[0]["tiow_src"].endswith("_4.stl"), msg)
ck("2 legs moved across to it, same place", alive(legs) and on(legs, "Flat Waist") and close(A(frame(legs)), w0, 0.05, 0.01), (msg, alive(legs) and legs.parent and legs.parent.name, alive(legs) and np.round(A(frame(legs))[:3, 3] - w0[:3, 3], 3)))
ck("2 adaptor 4 is now the one flat legs bring", prefs.adaptor_default == 4)
# 3 another flat legs: swap on the same adaptor
select(legs); legs2 = send(TNL[1], "Legs")
ck("3 new flat legs replace the old on the adaptor", on(legs2, "Flat Waist") and not alive(legs) and len(adaptors()) == 1, T._state["last"])
# 4 Mar Fil legs replace adaptor + flat legs
select(t); ml = send(AML, "Legs")
ck("4 Mar Fil legs on Waist", on(ml, "Waist"), T._state["last"])
ck("4 adaptor and flat legs gone", not adaptors() and not alive(legs2), [o.name for o in adaptors()])
ck("4 Mar Fil legs where Josh seats them", close(A(frame(ml)), expect(ml, t, "Waist", "Waist"), 0.05, 0.01))
# 5 flat legs again on the Mar Fil torso: adaptor comes back (4 now), Mar Fil legs go
select(t); l3 = send(TNL[2], "Legs")
ck("5 flat legs bring the adaptor back", len(adaptors()) == 1 and adaptors()[0]["tiow_src"].endswith("_4.stl") and on(l3, "Flat Waist"), T._state["last"])
ck("5 Mar Fil legs replaced", not alive(ml))
marine1 = t
# 6 TN torso: flat legs on Flat Waist (no adaptor), Mar Fil legs on Waist, each replacing the other
select(None); tt = send(TNT, "Bodies", (40, 0, 0))
tl = send(TNL[0], "Legs")
ck("6 TN legs on the TN torso's Flat Waist, no adaptor", on(tl, "Flat Waist") and tl.parent.parent is tt and len(adaptors()) == 1, T._state["last"])
ck("6 TN legs where the fit puts them", close(A(frame(tl)), expect(tl, tt, "Flat Waist", "Flat Waist"), 0.05, 0.01))
select(tt); m2 = send(AML, "Legs")
ck("6 Mar Fil legs on the TN torso's Waist", on(m2, "Waist") and m2.parent.parent is tt, T._state["last"])
ck("6 they replace the flat legs (one waist at a time)", not alive(tl), T._state["last"])
ck("6 Mar Fil legs where the cross rule puts them", close(A(frame(m2)), expect(m2, tt, "Waist", "Waist"), 0.05, 0.01))
select(tt); tl2 = send(TNL[1], "Legs")
ck("6 flat legs replace the Mar Fil legs again", on(tl2, "Flat Waist") and not alive(m2), T._state["last"])
# 7 Mar Fil arms, helmet, pack on the TN torso
for r, cat, want in ((f"{AM}/Arms/101-Arm-6-R-A.stl", "Arms", "Shoulder R"), (f"{AM}/Arms/103-Arm-6-L-A.stl", "Arms", "Shoulder L"),
                     (f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads", "Neck"), (f"{AM}/JumpPacks/55-JumpPack-1.stl", "Jump Packs", "Back")):
    select(tt); p = send(r, cat)
    ck(f"7 {r.split('/')[-1]} on the TN torso's {want}", on(p, want) and p.parent.parent is tt, T._state["last"])
    if on(p, want): ck(f"7 {r.split('/')[-1]} where its fit puts it", close(A(frame(p)), expect(p, tt, want, want), 0.15, 0.01), (np.round(A(frame(p))[:3, 3] - expect(p, tt, want, want)[:3, 3], 3), ang(A(frame(p)), expect(p, tt, want, want))))
# 8 the TN torso on Mar Fil legs: its bottom sits on the belt line (24.8 above the legs' torso-frame origin)
select(tt); m3 = send(AML, "Legs")
S_w = A(sock(tt, "Waist").matrix_world); B = A(sock(tt, "Flat Waist").matrix_world)
SWAM = np.eye(4); SWAM[:3, 3] = (0, 0.571273, 29.307301); KB = np.eye(4); KB[:3, 3] = (0, 0.571273, 24.8)
kb = S_w @ np.linalg.inv(SWAM) @ KB      # where the bottom should be
ck("8 TN torso bottom on the Mar Fil belt line", close(B, kb, 0.05, 0.01), np.round(B[:3, 3] - kb[:3, 3], 3))
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05)}
for nm, root in (("mf_adaptor", marine1), ("tn_torso", tt)):
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "flat_" + nm, obs, V, [rend.ORANGE if o.get("tiow_category") in ("Adapters", "Bodies") else rend.GREY for o in obs])
print("\nFAILS:", fails)
