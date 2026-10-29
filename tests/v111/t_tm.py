"""Techmarine through the inbox: chest root, seated legs + rock, each arm set as posed (cables on their arms), the separate
hand holding an Outrider hand-less sword, cog axes / grav pistol, the axe double arms, helmet, backpack with forge gun,
servo arm (ball in its seat) and mechadendrite, pads, belt bits on Mar Fil's spots."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v111/out"
K = "All Mar All the time/Techmarine (2)/Techmarine"
ORK = "All Mar All the time/Outriders (1)/Outriders"
PAR = json.load(open("/home/claude/kits/tm/tm_partial.json"))["side"]
BALLS = json.load(open("/home/claude/kits/tm/balls.json")); SEAT = np.array(json.load(open("/home/claude/kits/tm/servo_seat.json"))["seat"])
TOR = {s['type']: M16(s['matrix']) for s in PAR["Techmarine (2)/Techmarine/Chest/Chest-Raw-STL/2-Chest.stl"]["sockets"]}
def fitM(rel, t): return M16(PAR["Techmarine (2)/Techmarine/" + rel]["fits"][t])
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") in ((want,) if isinstance(want, str) else want)
def put(host, rel, cat, want, label, sel=None, base=K):
    select(sel or host); p = send(f"{base}/{rel}", cat); ck(f"{label}: {os.path.basename(rel)} on {want}", on(p, want), T._state["last"]); return p
def rel_to(label, part, host, M, what, deg=0.05, mm=0.02):
    got = A(frame(host).inverted() @ frame(part)); ck(f"{label}: {what}", close(got, M, deg, mm), f"{ang(got, M):.2f} deg {np.linalg.norm(got[:3,3]-M[:3,3]):.3f} mm"); return got
marines = []
def tm(label, cursor, legs, armR=None, wR=None, armL=None, cableL=None, handL=None, wL=None, gripL=None, double=None, cable2=None, gun=None, servo=None, mech=None, belt=(), rock=False):
    select(None); t = send(f"{K}/Chest/Chest-Raw-STL/2-Chest.stl", "Bodies", cursor)
    lg = put(t, f"Legs/Legs-Raw-STL/{legs}", "Bodies", "Waist", label); rel_to(label + " legs", lg, t, TOR["Waist"] @ fitM(f"Legs/Legs-Raw-STL/{legs}", "Waist"), "seated like Josh's AM legs")
    if rock: put(lg, "Accesories/Raw-STL/42-TacticalRock.stl", "Bases", "Base", label)
    arms = {}
    for sd, rel in (("R", armR), ("L", armL)):
        if not rel: continue
        a = put(t, f"Arms/Arms-Raw-STL/{rel}", "Arms", f"Shoulder {sd}", label); arms[sd] = a
        if a: rel_to(f"{label} arm {sd}", a, t, TOR[f"Shoulder {sd}"] @ fitM(f"Arms/Arms-Raw-STL/{rel}", f"Shoulder {sd}"), "posed as its set")
    if cableL and arms.get("L"): put(arms["L"], f"Arms/Arms-Raw-STL/{cableL}", "Arms", "Cable", label)
    if wR and arms.get("R"):
        ck(f"{label}: arm R has a Hand R", sock(arms["R"], "Hand R") is not None, T._state["last"]); w = put(arms["R"], f"Weapons/Weapons-Raw-STL/{wR}", "Weapons", "Hand R", label)
        if w: rel_to(f"{label} {wR}", w, arms["R"], np.eye(4), "in the hand as Mar Fil exported it", deg=0.5, mm=0.5)
    if arms.get("L") and (handL or wL):
        ck(f"{label}: arm L has a Hand L", sock(arms["L"], "Hand L") is not None, T._state["last"])
        if handL:
            h = put(arms["L"], "Accesories/Raw-STL/38-Hand.stl", "Accessories", "Hand L", label)
            if h: rel_to(f"{label} hand 38", h, arms["L"], np.eye(4), "on arm 12 as Mar Fil exported it", deg=0.5, mm=0.5)
            if h and gripL: put(h, gripL, "Weapons", "Grip L", label, base=ORK)
        if wL: put(arms["L"], f"Weapons/Weapons-Raw-STL/{wL}", "Weapons", "Hand L", label)
    if double:
        d = put(t, f"DoubleArms/DoubleArms-Raw-STL/{double}", "Weapons", "Shoulder R", label)
        if d and cable2: put(d, f"DoubleArms/DoubleArms-Raw-STL/{cable2}", "Weapons", "Cable", label)
    put(t, "Helmet/Helmet-Raw-STL/1-Helmet.stl", "Heads", "Neck", label)
    bp = put(t, "Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl", "Backpacks", "Back", label)
    if bp:
        if gun: g = put(bp, f"Weapons/Weapons-Raw-STL/{gun}", "Weapons", "Back Top", label); g and rel_to(f"{label} forge gun", g, bp, np.eye(4), "as exported on the backpack")
        if servo:
            s = put(bp, f"MechanicArms/MechanicArm-Raw-STL/{servo}", "Servo Arms", "Servo Arm", label)
            if s:
                ball = A(frame(s)) @ np.r_[BALLS[servo]["c"], 1]; seat = A(frame(bp)) @ np.r_[SEAT, 1]
                ck(f"{label}: servo arm ball in its seat", np.linalg.norm(ball[:3] - seat[:3]) < 0.02, f"{np.linalg.norm(ball[:3]-seat[:3]):.3f} mm")
        if mech: put(bp, f"ExtensibleArms/ExtensibleArm-Raw-STL/{mech}", "Mechadendrites", "Mechadendrite", label)
    if arms.get("R"): put(arms["R"], "ShoulderPads/Shoulderpad-Raw-STL/10-ShoulderPad-R.stl", "Shoulder Pads", "Pad R", label)
    if arms.get("L"): put(arms["L"], "ShoulderPads/Shoulderpad-Raw-STL/9-ShoulderPad-L.stl", "Shoulder Pads", "Pad L", label)
    for sd, f in (("R", "7-Shinpad-R.stl"), ("L", "8-Shinpad-L.stl")):
        s_ = sock(lg, f"Shin {sd}"); ck(f"{label} legs: Shin {sd} anchor found", s_ is not None)
        if s_ is not None: put(lg, f"Shinpads/Shinpads-Raw-STL/{f}", "Knee Pads", f"Shin {sd}", label, sel=s_)
    for a_ in belt:
        p = put(lg, f"Accesories/Raw-STL/{a_}", "Accessories", ("Hip R", "Hip L", "Belt Front", "Belt Back"), label)
        if p and T._holds(p.parent): rel_to(f"{label} {a_}", p, lg, np.eye(4), "exactly where Mar Fil put it")
    marines.append((label, t))
tm("tm1", (0, 0, 0), "3-Legs-1.stl", armR="18-Arm-4-R.stl", wR="33-CogAxe-1.stl", armL="12-Arm-1-L.stl", cableL="13-Arm-1-L-Cable.stl", handL=True, gripL="Weapons/WeaponsRawSTL(Right)/39-SwordNoHand.stl",
   gun="36-ForgeBolter.stl", servo="24-MechanicArm-1.stl", mech="29-ExtensibleArm-1.stl", belt=("39-PistolHolster-1.stl", "41-Pouch.stl"), rock=True)
tm("tm2", (70, 0, 0), "4-Legs-2.stl", armR="19-Arm-5-R.stl", wR="34-CogAxe-2.stl", armL="16-Arm-3-L.stl", cableL="17-Arm-3-L-Cable.stl", wL="35-GravPistol.stl",
   gun="37-ForgePlasma.stl", servo="26-MechanicArm-3.stl", mech="30-ExtensibleArm-2.stl", belt=("41-Pouch.stl",))
tm("tm3", (140, 0, 0), "5-Legs-3.stl", double="20-DoubleArm-1.stl", cable2="21-DoubleArm-1-Cable.stl", gun="36-ForgeBolter.stl", servo="27-MechanicArm-4.stl", mech="31-ExtensibleArm-3.stl")
tm("tm4", (210, 0, 0), "6-Legs-4.stl", double="22-DoubleArm-2.stl", cable2="23-DoubleArm-2-Cable.stl", servo="28-MechanicArm-5.stl", mech="32-ExtensibleArm-4.stl",
   belt=("40-PistolHolster-2.stl", "41-Pouch.stl"))
tm("tm5", (280, 0, 0), "4-Legs-2.stl", armR="18-Arm-4-R.stl", armL="14-Arm-2-L.stl", cableL="15-Arm-2-L-Cable.stl", servo="25-MechanicArm-2.stl")
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05), "back": (-0.4, -1, 0.25)}
for nm, root in marines:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    cols = [rend.ORANGE if str(o.get("tiow_category", "")) in ("Shoulder Pads", "Knee Pads", "Accessories") else
            rend.BLUE if str(o.get("tiow_category", "")) in ("Melee", "Pistols", "Hand-less Weapons", "Hands", "Two-Handed Melee", "Backpack Toppers") else
            (0.55, 0.8, 0.5, 1) if str(o.get("tiow_category", "")) in ("Servo Arms", "Mechadendrites", "Cables") else rend.GREY for o in obs]
    rend.render(scene, OUT, nm, obs, V, cols)
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/tm_test.blend")
print("\nFAILS:", fails)
