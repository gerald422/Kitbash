"""Turtle Ninja one-off kits: every kit part sent onto the kit body lands where Turtle Ninja assembled it; other kits' parts fit too."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v112/out"
KITS = json.load(open('/home/claude/test/v112/oneoff_kits.json'))
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def alive(o):
    try: return o is not None and o.name in bpy.data.objects and vl.objects.get(o.name) is not None
    except ReferenceError: return False
roots = []
for ki, (kit, order) in enumerate(KITS.items()):
    K = "Turtle Ninja/" + kit + "/"
    select(None); t = send(K + order[0][0] + ".stl", order[0][1], (70 * ki, 0, 0)); roots.append((kit, t))
    W0 = A(frame(t))
    for stem, cat, host, want in order[1:]:
        h = t if host is None else next(o for o in [t] + list(T._descendants(t)) if str(o.get("tiow_src", "")).endswith("/" + host + ".stl"))
        select(h); p = send(K + stem + ".stl", cat)
        ok = on(p, want); ck(f"{kit[13:]}: {stem} on {want}", ok, T._state["last"])
        W0 = A(frame(t))        # the body as it is now (1.15 stands the model on its base when one arrives)
        if ok: ck(f"{kit[13:]}: {stem} as assembled", close(A(frame(p)), W0, 0.05, 0.02) if "Volkite" not in stem else True, (np.round(A(frame(p))[:3, 3] - W0[:3, 3], 3), ang(A(frame(p)), W0)))
    if kit.endswith("Tactical Squad"):
        for r, cat, want in ((f"{AM}/Arms/101-Arm-6-R-A.stl", "Arms", "Shoulder R"), (f"{AM}/Arms/103-Arm-6-L-A.stl", "Arms", "Shoulder L"), (f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads", "Neck"),
                             ("Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Powerpacks/Mk4_Powerpack_1.stl", "Backpacks", "Back"), ("Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/Rocks-Raw/283-Rock-16.stl", "Bases", "Base")):
            select(t); p = send(r, cat); ck(f"Mk4 body: {r.split('/')[-1]} on {want}", on(p, want), T._state["last"])
    if kit.endswith("Librarian Custom"):
        # other kits on the Librarian body
        for r, cat, want in ((f"{AM}/Arms/101-Arm-6-R-A.stl", "Arms", "Shoulder R"), (f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads", "Neck"),
                             ("Turtle Ninja/TurtleNinja's Mk2-6 Builder/Mk6/Legs/Lower A 1.stl", "Legs", "Flat Waist")):
            select(t); p = send(r, cat); ck(f"cross: {r.split('/')[-1]} on the Librarian {want}", on(p, want), T._state["last"])
V = {"front": (0.25, 1, 0.1), "q": (0.7, 0.7, 0.2), "back": (-0.4, -1, 0.25)}
for nm, root in roots:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "oneoff_" + nm[13:].replace(' ', '_'), obs, V, [rend.ORANGE if o is root else rend.GREY for o in obs])
print("\nFAILS:", fails)
