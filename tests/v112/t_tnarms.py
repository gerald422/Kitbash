"""TN arms on TN and Mar Fil torsos (disc rule), the wrist rule on TN arms, TN and Mar Fil hand weapons in them."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v112/out"
prefs.adaptor_dir = os.path.join(LIB, "body adaptor"); prefs.adaptor_default = 3
TN = "Turtle Ninja/"
TNT = TN + "TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl"
AMT = f"{AM}/Chest/22-Torso-1.stl"; AML = f"{AM}/Legs/29-Legs-2.stl"
ARMS = json.load(open('/home/claude/kits/tn/arms/sample_arm_fits.json'))
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
models = []
for ti, torso in enumerate((TNT, AMT)):
    for k, (rel, v) in enumerate(ARMS.items()):
        if v['side'] != 'R': continue
        select(None); t = send(torso, "Bodies", (ti * 300 + k * 30, 0, 0)); send(AML, "Legs"); select(t)
        a = send(TN + rel, "Arms")
        ck(f"{['TN', 'MF'][ti]} torso: {rel.split('/')[-1]} on Shoulder R", on(a, "Shoulder R"), T._state["last"])
        hs = sock(a, "Hand R") if a else None
        ck(f"{['TN', 'MF'][ti]} torso: {rel.split('/')[-1]} wrist found by the rule", hs is not None, T._state["last"])
        if hs is not None:
            select(a); w = send(TN + "TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Hands/Mk10 Assault Pistol 1.stl", "Pistols")
            ck(f"   TN pistol in its hand", on(w, "Hand R"), T._state["last"])
        # matching left arm of the same set, if any
        models.append((f"{['TN', 'MF'][ti]}_{k}", t))
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2)}
for nm, root in models:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "arms_" + nm, obs, V, [rend.ORANGE if 'Turtle' in str(o.get("tiow_src", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
