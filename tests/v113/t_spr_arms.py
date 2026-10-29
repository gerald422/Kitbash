"""Springles: heresy-scale arms (sidecar scale, no Pad anchor, wrist cup Hand socket), hand-held weapons (wrist dome in the cup),
two-handed guns, packs; across Mar Fil / Turtle Ninja torsos and Mar Fil arms/weapons."""
exec(open("/home/claude/test/v18/common18.py").read())
import json as _j
OUT = "/home/claude/test/v113/out"
SP = "Springles/"
TNT = "Turtle Ninja/TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def side(rel): return _j.load(open(os.path.join(LIB, rel[:-4] + ".sockets.json")))
def child(p, t): return next((c for c in p.children if c.get("ws_type") == t), None)
def scl(p): return float(np.linalg.norm(A(p.matrix_world)[:3, 0]))
def dome_in_cup(w, arm, sd="R"):
    """the weapon's grip dome apex vs the arm cup floor (0.55 below the lip on the cup axis)"""
    s = child(arm, "Hand " + sd)
    if s is None: return 99
    F = np.linalg.inv(np.array(side(w["rel"])["fits"]["Hand " + sd]).reshape(4, 4))     # hand frame in scaled part coords
    apex = A(w["ob"].matrix_world) @ (F @ np.array([0, 0.55, 0, 1.0]))
    floor = A(s.matrix_world) @ np.array([0, 0.55, 0, 1.0])
    return float(np.linalg.norm(apex[:3] - floor[:3]))
roots = []
CR = SP + "patternC arms/tactical arms/patternC ranged Rarm 1.stl"; CL = SP + "patternC arms/tactical arms/patternC ranged Larm 1.stl"
select(None); t = send(f"{AM}/Chest/22-Torso-1.stl", "Bodies", (0, 0, 0)); roots.append(("mf", t))
r = send(CR, "Arms"); ck("Springles right arm on Shoulder R", on(r, "Shoulder R"), T._state["last"])
ck("arm scaled 1.1002", abs(scl(r) - 1.0) < 1e-6 and abs(float(r.get("tiow_scale", 0)) - 1.1002) < 1e-9, (scl(r), r.get("tiow_scale")))
F = np.array(side(CR)["fits"]["Shoulder R"]).reshape(4, 4)
ck("arm exactly at socket @ fit", np.abs(A(r.matrix_world) - A(r.parent.matrix_world) @ F).max() < 2e-3, np.abs(A(r.matrix_world) - A(r.parent.matrix_world) @ F).max())
ck("no Pad anchor on a heresy arm", not any(str(c.get("ws_type", "")).startswith("Pad") for c in r.children), [c.get("ws_type") for c in r.children])
ck("Hand R socket from the sidecar (cup)", child(r, "Hand R") is not None, [c.get("ws_type") for c in r.children])
select(t); l = send(CL, "Arms"); ck("Springles left arm on Shoulder L", on(l, "Shoulder L"), T._state["last"])
ck("left arm has Hand L", child(l, "Hand L") is not None, [c.get("ws_type") for c in l.children])
select(t); h = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
select(r); mp = send(f"{AM}/Pistols/211-BoltPistol-R.stl", "Pistols")
ck("Mar Fil bolt pistol in the Springles cup", mp is not None and on(mp, "Hand R"), T._state["last"])
select(None); t2 = send(TNT, "Bodies", (40, 0, 0)); roots.append(("tn", t2))
r2 = send(SP + "patternS arms/melee arms/patternS melee Rarm 2.stl", "Arms"); ck("pattern S arm on the TN Shoulder R", on(r2, "Shoulder R"), T._state["last"])
select(t2); l2 = send(SP + "patternP arms/heavy weapons/patternP heavy Larm 2.stl", "Arms"); ck("pattern P left arm on the TN Shoulder L", on(l2, "Shoulder L"), T._state["last"])
select(t2); sl = send(SP + "patternC arms/unique/patternC slung arm+hand.stl", "Arms"); ck("slung arm+hand replaces the right arm", on(sl, "Shoulder R"), T._state["last"])
ck("slung arm+hand: no Hand socket, no complaint", child(sl, "Hand R") is None and "no Hand" not in str(T._state["last"]), T._state["last"])
select(t2); hh = send(SP + "patternC arms/unique/patternC helmet hold arm.stl", "Arms"); ck("helmet hold arm (a left arm) on Shoulder L", on(hh, "Shoulder L"), T._state["last"])
V = {"front": (0.25, 1, 0.1), "side": (1, 0, 0.05), "top": (0.1, 0.4, 1)}
for nm, root in roots:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "sprarms_" + nm, obs, V, [rend.ORANGE if "Springles" in str(o.get("tiow_src", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
