"""Marta: flat legs on TN and Mar Fil torsos (adaptor), loincloth on the belt front, base under the feet, two-armed set on the shoulders."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v112/out"
prefs.adaptor_dir = os.path.join(LIB, "body adaptor"); prefs.adaptor_default = 3
M = "Marta/51 May 2026-20260612T074408Z-3-001/51 May 2026/"
TNT = "Turtle Ninja/TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
roots = []
select(None); t = send(TNT, "Bodies", (0, 0, 0)); roots.append(("tn", t))
l = send(M + "legs-chin pads and base/legs_1.stl", "Legs"); ck("Marta legs on the TN torso's Flat Waist", on(l, "Flat Waist"), T._state["last"])
select(l); lc = send(M + "loincloths/loincloth_1.stl", "Accessories"); ck("loincloth on Belt Front", on(lc, "Belt Front"), T._state["last"])
select(l); b = send(M + "legs-chin pads and base/base_32mm.stl", "Bases"); ck("base on Base", on(b, "Base"), T._state["last"])
select(t); a = send(M + "amrs and weapons/set_arms_1_with_weapon_1.stl", "Weapons"); ck("two-armed set on Shoulder R", on(a, "Shoulder R"), T._state["last"])
select(None); t2 = send(f"{AM}/Chest/22-Torso-1.stl", "Bodies", (40, 0, 0)); roots.append(("mf", t2))
l2 = send(M + "legs-chin pads and base/legs_3.stl", "Legs"); ck("Marta legs on a Mar Fil torso bring the adaptor", on(l2, "Flat Waist") and l2.parent.parent.get("tiow_category") == "Adapters", T._state["last"])
select(l2); lc2 = send(M + "loincloths/loincloth_5.stl", "Accessories"); ck("loincloth 5 on Belt Front", on(lc2, "Belt Front"), T._state["last"])
select(t2); a2 = send(M + "amrs and weapons/set_arms_2_with_weapon_2.stl", "Weapons"); ck("two-armed set 2 on the Mar Fil Shoulder R", on(a2, "Shoulder R"), T._state["last"])
select(t2); h = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
select(t); h2 = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
select(None); t3 = send(TNT, "Bodies", (80, 0, 0)); roots.append(("sit", t3))
l3 = send(M + "legs-chin pads and base/legs_6_sitting.stl", "Legs"); ck("sitting legs on Flat Waist", on(l3, "Flat Waist"), T._state["last"])
select(t3); h3 = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
V = {"front": (0.25, 1, 0.1), "side": (1, 0, 0.05), "back": (-0.3, -1, 0.2)}
for nm, root in roots:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "marta_" + nm, obs, V, [rend.ORANGE if "Marta" in str(o.get("tiow_src", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
