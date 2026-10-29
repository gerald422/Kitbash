"""Whole marines through the inbox, everything on: torso, legs + base-less, both arms with weapons, helmet,
jump pack + fins, pauldrons on both arms, shin pads on both legs. Plus a two-hander marine with pads."""
exec(open("/home/claude/test/v17/common17.py").read())
OUT = "/home/claude/test/v17/out"; os.makedirs(OUT, exist_ok=True)
def on(p, tname):
    return p is not None and p.parent is not None and p.parent.get("ws_type") == tname
def send_to(host, rel, cat, want, label):
    select(host); p = send(rel, cat)
    ck(f"{label}: on {want}", on(p, want) if isinstance(want, str) else (p.parent is not None and p.parent.get("ws_type") in want), T._state["last"])
    return p
def marine(label, cursor, torso_rel, legs_rel, armR, wR, armL, wL, head, pack, fin, padR, padL, shinR, shinL):
    select(None); t = send(torso_rel, "Chests", cursor)
    lg = send_to(t, legs_rel, "Legs", "Waist", f"{label} legs")
    aR = send_to(t, armR, "Arms", "Shoulder R", f"{label} arm R")
    aL = send_to(t, armL, "Arms", "Shoulder L", f"{label} arm L")
    if wR: send_to(aR, wR, "Melee", "Hand R", f"{label} right hand")
    if wL: send_to(aL, wL, "Melee", "Hand L", f"{label} left hand")
    send_to(t, head, "Heads", "Neck", f"{label} head")
    pk = send_to(t, pack, "Jump Packs", "Back", f"{label} pack")
    for i in range(2): send_to(pk, fin, "Jump Packs", ("Pack Fin R", "Pack Fin L"), f"{label} fin {i+1}")
    send_to(aR, padR, "Shoulder Pads", "Pad R", f"{label} pauldron R")
    send_to(aL, padL, "Shoulder Pads", "Pad L", f"{label} pauldron L")
    select(sock(lg, "Shin R")); p = send(shinR, "Knee Pads"); ck(f"{label} shin pad R", on(p, "Shin R"), T._state["last"])
    select(sock(lg, "Shin L")); p = send(shinL, "Knee Pads"); ck(f"{label} shin pad L", on(p, "Shin L"), T._state["last"])
    return t
SP, SH = f"{AM}/ShoulderPads", f"{AM}/ShinPads"
m1 = marine("m1", (0, 0, 0), f"{AM}/Chest/24-Torso-3.stl", f"{AM}/Legs/30-Legs-3.stl",
            f"{AM}/Arms/106-Arm-7-R-A.stl", f"{AM}/Melee/202-PowerSword-A-1-R.stl",
            f"{AM}/Arms/109-Arm-7-L-B.stl", f"{AM}/Pistols/LeftOrientated/Weapons-Assault211-BoltPistol-L.stl",
            f"{AM}/Helmet-Heads/3-Helmet-3.stl", f"{AM}/JumpPacks/56-JumpPack-2.stl", f"{AM}/JumpPacks/60-Fin-1.stl",
            f"{SP}/62-ShoulderPad-1.stl", f"{SP}/62-ShoulderPad-1.stl", f"{SH}/68-ShinPad-1.stl", f"{SH}/68-ShinPad-1.stl")
m2 = marine("m2", (80, 0, 0), f"{AM}/Chest/23-Torso-2.stl", f"{AM}/Legs(JumpPack)/47-Legs-8-A.stl",
            f"{AM}/Arms/126-Arm-11-R-A.stl", f"{AM}/Melee/195-PowerHammer-A-3-R.stl",
            f"{AM}/Arms/128-Arm-11-L-A.stl", f"{AM}/Melee/LeftOrientated/190-PowerAxe-C-1-L.stl",
            f"{AM}/Helmet-Heads/12-Head-4.stl", f"{AM}/JumpPacks/57-JumpPack-3.stl", f"{AM}/JumpPacks/61-Fin-2.stl",
            f"{SP}/63-ShoulderPad-2.stl", f"{SP}/63-ShoulderPad-2.stl", f"{SH}/72-ShinPad-5.stl", f"{SH}/LeftOrientated/Mirrored-72-ShinPad-5.stl")
m3 = marine("m3", (160, 0, 0), f"{AM}/Chest/26-Torso-5.stl", f"{AM}/Legs(JumpPack)/Mirrored/Mirrored-39-Legs-4-A.stl",
            f"{AM}/PowerFist/163-PowerFist-A-2.stl", None,
            f"{AM}/PowerFist/Mirrored/Mirrored-170-PowerFist-B-4.stl", None,
            f"{AM}/Helmet-Heads/7-Helmet-7.stl", f"{AM}/JumpPacks/59-JumpPack-5.stl", f"{AM}/JumpPacks/60-Fin-1.stl",
            f"{SP}/66-ShoulderPad-5.stl", f"{SP}/67-ShoulderPad-6.stl", f"{SH}/69-ShinPad-2.stl", f"{SH}/69-ShinPad-2.stl")
m4 = marine("m4", (240, 0, 0), f"{AM}/Chest/22-Torso-1.stl", f"{AM}/Legs/31-Legs-4.stl",
            f"{AM}/Arms/86-Arm-3-R-A.stl", f"{AM}/Melee/188-PowerAxe-B-2-R.stl",
            f"{AM}/Arms/88-Arm-3-L-A.stl", f"{AM}/Melee/LeftOrientated/205-PowerSword-B-1-L.stl",
            f"{AM}/Helmet-Heads/1-Helmet-1.stl", f"{AM}/JumpPacks/55-JumpPack-1.stl", f"{AM}/JumpPacks/61-Fin-2.stl",
            f"{SP}/64-ShoulderPad-3.stl", f"{SP}/65-ShoulderPad-4.stl", f"{SH}/70-ShinPad-3.stl", f"{SH}/LeftOrientated/Mirrored-70-ShinPad-3.stl")
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05), "back": (-0.4, -1, 0.25)}
def shoot(nm, root):
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    cols = []
    for o in obs:
        cat = str(o.get("tiow_category", ""))
        cols.append(rend.ORANGE if cat in ("Shoulder Pads", "Knee Pads") else rend.BLUE if cat in ("Melee", "Pistols", "Shields", "Two-Handed Melee") else rend.GREY)
    rend.render(scene, OUT, "full_" + nm, obs, V, cols)
    up = [(o, c) for o, c in zip(obs, cols) if str(o.get("tiow_category", "")) in ("Chests", "Arms", "Shoulder Pads", "Heads")]
    rend.render(scene, OUT, "upper_" + nm, [o for o, c in up], {"front": (0, 1, 0.25), "q": (0.8, 0.5, 0.35), "qb": (-0.8, -0.5, 0.35)}, [c for o, c in up])
    lw = [(o, c) for o, c in zip(obs, cols) if str(o.get("tiow_category", "")) in ("Legs", "Knee Pads")]
    rend.render(scene, OUT, "lower_" + nm, [o for o, c in lw], {"front": (0.3, 1, 0.15)}, [c for o, c in lw])
for nm, ob in (("m1", m1), ("m2", m2), ("m3", m3), ("m4", m4)): shoot(nm, ob)
print("\nFAILS:", fails)
