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
ck("Pad R anchor from the sidecar", child(r, "Pad R") is not None, [c.get("ws_type") for c in r.children])
ck("Hand R socket from the sidecar (cup)", child(r, "Hand R") is not None, [c.get("ws_type") for c in r.children])
select(t); l = send(CL, "Arms"); ck("Springles left arm on Shoulder L", on(l, "Shoulder L"), T._state["last"])
ck("left arm has Hand L", child(l, "Hand L") is not None, [c.get("ws_type") for c in l.children])
W = {}
def weapon(rel, cat, target, sock="Hand R"):
    select(target); o = send(SP + rel, cat); W[rel] = dict(ob=o, rel=SP + rel)
    ck(f"{os.path.basename(rel)} on {sock}", on(o, sock), T._state["last"]); return o
g = weapon("umbra bolters/bolter/umbra bolter.stl", "Weapons", r)
ck("bolter dome sits in the cup (<0.02)", dome_in_cup(W["umbra bolters/bolter/umbra bolter.stl"], r) < 0.02, dome_in_cup(W["umbra bolters/bolter/umbra bolter.stl"], r))
ck("bolter scaled by its sidecar", abs(float(g.get("tiow_scale", 0)) - 1.1) < 1e-9, g.get("tiow_scale"))
def off_gap(w, arm_l):
    oh = np.array(side(w["rel"])["offHand"]).reshape(4, 4)
    p = A(w["ob"].matrix_world) @ oh; s = child(arm_l, "Hand L")
    return float(np.linalg.norm(p[:3, 3] - A(s.matrix_world)[:3, 3]))
ck("bolter turned so the left hand meets the left wrist (<2.5 mm)", off_gap(W["umbra bolters/bolter/umbra bolter.stl"], l) < 2.5, (off_gap(W["umbra bolters/bolter/umbra bolter.stl"], l), T._state["last"]))
ck("the grip dome still sits in the right cup after the turn", dome_in_cup(W["umbra bolters/bolter/umbra bolter.stl"], r) < 0.02, dome_in_cup(W["umbra bolters/bolter/umbra bolter.stl"], r))
select(t); h = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
select(r); pr = send(f"{AM}/ShoulderPads/62-ShoulderPad-1.stl", "Shoulder Pads"); ck("Mar Fil pauldron on the Springles arm's Pad R", on(pr, "Pad R"), T._state["last"])
if pr is not None:
    Mexp = A(child(r, "Pad R").matrix_world) @ np.array(_j.load(open(os.path.join(LIB, AM, "ShoulderPads/_fits.json")))["Pad R"]["m"]).reshape(4, 4)
    ck("pauldron exactly at anchor @ fit", np.abs(A(pr.matrix_world) - Mexp).max() < 2e-3, np.abs(A(pr.matrix_world) - Mexp).max())
select(l); pl_ = send(f"{AM}/ShoulderPads/62-ShoulderPad-1.stl", "Shoulder Pads"); ck("pauldron mirrored onto the left arm's Pad L", on(pl_, "Pad L") and pl_.get("tiow_mirrored"), T._state["last"])
pk = None
for p in ["heavy weapons/backpacks/hw backpack.stl"]:
    select(t); pk = send(SP + p, "Backpacks"); ck("hw backpack on Back", on(pk, "Back"), T._state["last"])
# TN torso, Springles melee arms + axe, Mar Fil bolt pistol in a Springles cup
select(None); t2 = send(TNT, "Bodies", (40, 0, 0)); roots.append(("tn", t2))
r2 = send(SP + "patternS arms/melee arms/patternS melee Rarm 2.stl", "Arms"); ck("pattern S arm on the TN Shoulder R", on(r2, "Shoulder R"), T._state["last"])
select(t2); l2 = send(SP + "patternS arms/melee arms/patternS Larm melee 2.stl", "Arms"); ck("pattern S left arm on the TN Shoulder L", on(l2, "Shoulder L"), T._state["last"])
ax = weapon("carsoran power axes/carsoran power axe A/carsoran power axe A v1.stl", "Weapons", r2)
ck("axe dome in the cup", dome_in_cup(W["carsoran power axes/carsoran power axe A/carsoran power axe A v1.stl"], r2) < 0.02, "")
select(l2); mp = send(f"{AM}/Pistols/211-BoltPistol-R.stl", "Pistols")
ck("Mar Fil bolt pistol in the Springles right cup (replaces the axe)", mp is not None and on(mp, "Hand R"), T._state["last"])
select(t2); h2 = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
# Mar Fil torso + Mar Fil arm + Springles pistol in the Mar Fil hand; Springles P arm with a heavy weapon
select(None); t3 = send(f"{AM}/Chest/22-Torso-1.stl", "Bodies", (80, 0, 0)); roots.append(("mix", t3))
ma = send(f"{AM}/Arms/101-Arm-6-R-A.stl", "Arms"); ck("Mar Fil arm on Shoulder R", on(ma, "Shoulder R"), T._state["last"])
pp = weapon("special weapons/plasma pistol/plasma pistol.stl", "Pistols", ma)
select(t3); pl = send(SP + "patternP arms/heavy weapons/patternP heavy Larm 2.stl", "Arms"); ck("pattern P heavy left arm on Shoulder L", on(pl, "Shoulder L"), T._state["last"])
ck("P arm Hand L carried from pattern C", child(pl, "Hand L") is not None, "")
select(t3); h3 = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
# heavy weapon on a heavy arm pair
select(None); t4 = send(f"{AM}/Chest/22-Torso-1.stl", "Bodies", (120, 0, 0)); roots.append(("heavy", t4))
hr = send(SP + "patternC arms/heavy weapons/patternC heavy Rarm 1.stl", "Arms")
select(t4); hl = send(SP + "patternC arms/heavy weapons/patternC heavy Larm 1.stl", "Arms")
hw = weapon("heavy weapons/heavy bolter/heavy bolter.stl", "Heavy Weapons", hr)
ck("heavy bolter's other hand meets the heavy left arm (<2.5 mm)", off_gap(W["heavy weapons/heavy bolter/heavy bolter.stl"], hl) < 2.5, off_gap(W["heavy weapons/heavy bolter/heavy bolter.stl"], hl))
ck("heavy bolter grip dome in the right cup", dome_in_cup(W["heavy weapons/heavy bolter/heavy bolter.stl"], hr) < 0.02, "")
select(t4); pk4 = send(SP + "heavy weapons/backpacks/hw heavy bolter backpack.stl", "Backpacks"); ck("hw heavy bolter pack on Back", on(pk4, "Back"), T._state["last"])
select(t4); h4 = send(f"{AM}/Helmet-Heads/1-Helmet-1.stl", "Heads")
V = {"front": (0.25, 1, 0.1), "side": (1, 0, 0.05), "top": (0.1, 0.4, 1)}
for nm, root in roots:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "spr_" + nm, obs, V, [rend.ORANGE if "Springles" in str(o.get("tiow_src", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
