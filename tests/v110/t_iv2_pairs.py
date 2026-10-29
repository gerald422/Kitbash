"""Intercessors V2 marines through the inbox: chest root, seated legs, arms + separate hands + hand-less weapons on the
Grip, hand-held parts on the kit wrist, arm-with-bolter pieces, two-handers, heavy weapons + cables, helmet, backpack,
pads, rocks. Renders each."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v110/out"; os.makedirs(OUT, exist_ok=True)
K = "Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL"
SEAT = {k[3:]: v for k, v in json.load(open("/home/claude/kits/iv2/legs_seat.json")).items()}
WkR = np.array([[1, 0, 0, -1.13], [0, 1, 0, 2.77], [0, 0, 1, 1.20], [0, 0, 0, 1.0]]); MXm = np.diag([-1.0, 1, 1, 1]); WkL = MXm @ WkR @ MXm
WbR = np.array([[-1, 0, 0, 0.82], [0, -1, 0, -8.43], [0, 0, 1, -2.94], [0, 0, 0, 1.0]])
WbL = np.array([[-1, 0, 0, -0.845], [0, -1, 0, -8.42], [0, 0, 1, -2.855], [0, 0, 0, 1.0]])
RZ90 = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def put(host, rel, cat, want, label):
    select(host); p = send(f"{K}/{rel}", cat); ck(f"{label}: on {want}", on(p, want), T._state["last"]); return p
def rel_to(label, part, host, M, what):
    got = A(frame(host).inverted() @ frame(part)); ck(f"{label}: {what}", close(got, M, 0.05, 0.02), f"{ang(got, M):.2f} deg {np.linalg.norm(got[:3,3]-M[:3,3]):.3f} mm")
def kitpos(label, part, root): rel_to(label, part, root, np.eye(4), "in kit position on the chest")
marines = []
def marine(label, cursor, chest, legs, rock=None, armR=None, wR=None, gR=None, armL=None, wL=None, gL=None, two=None, heavy=None, cable=None, head=None, pack=None, padR=None, padL=None, shinR=None, shinL=None):
    select(None); t = send(f"{K}/Chest-Raw/{chest}", "Bodies", cursor)
    ck(f"{label}: chest has its sockets", all(sock(t, k) for k in ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist")))
    lg = put(t, legs, "Bodies", "Waist", f"{label} legs")
    rel_to(f"{label} legs", lg, t, np.array(SEAT[f"{K}/{legs}"]["M"]), "seated like Josh's AM legs")
    ck(f"{label} legs: hips", all(sock(lg, k) for k in ("Hip R", "Hip L")))
    if rock: rk = put(lg, rock, "Bases", "Base", f"{label} rock"); rel_to(f"{label} rock", rk, lg, np.eye(4), "under the legs as exported")
    aR = aL = None
    for sd, arm, w, g in (("R", armR, wR, gR), ("L", armL, wL, gL)):
        if not arm: continue
        a = put(t, arm, "Arms", f"Shoulder {sd}", f"{label} arm {sd}")
        if sd == "R": aR = a
        else: aL = a
        if w:
            cat = w[1]; h = put(a, w[0], cat, f"Hand {sd}", f"{label} {cat} in the {sd} hand")
            if g:
                gp = put(h, g, "Weapons", f"Grip {sd}", f"{label} hand-less weapon in the {sd} hand")
                Wk = WkR if sd == "R" else WkL; Wb = WbR if sd == "R" else WbL
                M = Wk @ np.linalg.inv(Wb) @ RZ90 if "Bolter" in g else np.eye(4)
                rel_to(f"{label} {sd} grip", gp, h, M, "held as in the kit")
    if two: tw = put(t, two, "Weapons", "Shoulder R", f"{label} two-hander"); kitpos(f"{label} two-hander", tw, t)
    if heavy:
        hv = put(t, heavy, "Heavy Weapons", "Shoulder R", f"{label} heavy weapon"); kitpos(f"{label} heavy", hv, t)
        if cable: cb = put(hv, cable, "Heavy Weapons", "Cable", f"{label} cable"); kitpos(f"{label} cable", cb, t)
    elif cable and aR:
        cb = put(aR, cable, "Heavy Weapons", "Cable", f"{label} cable on the arm"); rel_to(f"{label} cable", cb, aR, np.eye(4), "with its arm as exported")
    if head: put(t, head, "Heads", "Neck", f"{label} head")
    if pack: pk = put(t, pack, "Backpacks", "Back", f"{label} backpack"); kitpos(f"{label} backpack", pk, t)
    if padR and aR: put(aR, padR, "Shoulder Pads", "Pad R", f"{label} pauldron R")
    if padL and aL: put(aL, padL, "Shoulder Pads", "Pad L", f"{label} pauldron L")
    if shinR: select(sock(lg, "Shin R")); p = send(f"{K}/{shinR}", "Knee Pads"); ck(f"{label} shin pad R", on(p, "Shin R"), T._state["last"])
    if shinL: select(sock(lg, "Shin L")); p = send(f"{K}/{shinL}", "Knee Pads"); ck(f"{label} shin pad L", on(p, "Shin L"), T._state["last"])
    marines.append((label, t)); return t
HL = "Hands-Raw/Hand-Left/"
B = "Bolter-Individual-Raw/"; BL = B + "Bolter-Individual-Left/"; PI = "PlasmaIncinerator-Raw/"; PY = "Pyreblaster-Raw/"
marine("p1", (0, 0, 0), "12-Chest-1.stl", "Legs-Raw/17-Legs-1.stl", armR=B + "125-Bolter-A-1-R.stl", armL=BL + "125-Bolter-A-1-L.stl", head="Helmets-Heads-Raw/1-Helmet-1.stl", padR="ShoulderPad-Raw/49-ShoulderPad-1.stl", padL="ShoulderPad-Raw/49-ShoulderPad-1.stl")
marine("p2", (60, 0, 0), "13-Chest-2.stl", "Legs-Raw/19-Legs-3.stl", armR=B + "131-Bolter-A-2-Individual-R.stl", armL=BL + "131-Bolter-A-2-Individual-L.stl", head="Helmets-Heads-Raw/2-Helmet-2.stl", padR="ShoulderPad-Raw/50-ShoulderPad-2.stl", padL="ShoulderPad-Raw/50-ShoulderPad-2.stl")
marine("p3", (120, 0, 0), "14-Chest-3.stl", "Legs-Raw/24-Legs-8.stl", armR=B + "137-Bolter-A-3-R.stl", armL=BL + "137-Bolter-A-3-L.stl", head="Helmets-Heads-Raw/5-Helmet-5.stl", padR="ShoulderPad-Raw/52-ShoulderPad-4.stl", padL="ShoulderPad-Raw/52-ShoulderPad-4.stl")
marine("p4", (180, 0, 0), "15-Chest-4.stl", "Legs-Raw/30-Legs-14.stl", armR=PI + "188-PlasmaIncinerator-4-A-R.stl", armL=PI + "PlasmaIncinerator-Left/189-PlasmaIncinerator-4-B-L.stl", cable=PI + "190-Cable-PlasmaIncinerator-4.stl", head="Helmets-Heads-Raw/1-Helmet-1.stl", pack="BackPacks-Raw/266-BackPack-1.stl")
marine("p5", (240, 0, 0), "16-Chest-5.stl", "Legs-Raw/40-Legs-24.stl", armR=PY + "201-Pyreblaster-7.stl", armL=PY + "Pyreblaster-Left/201-Pyreblaster-7-L.stl", head="Helmets-Heads-Raw/2-Helmet-2.stl", pack="BackPacks-Raw/266-BackPack-1.stl")
marine("p6", (300, 0, 0), "12-Chest-1.stl", "Legs-Raw/37-Legs-21.stl", armR=PY + "203-Pyreblaster-9-A.stl", armL=PY + "204-Pyreblaster-9-B.stl", head="Helmets-Heads-Raw/5-Helmet-5.stl", pack="BackPacks-Raw/266-BackPack-1.stl")
marine("p7", (360, 0, 0), "13-Chest-2.stl", "Legs-Raw/28-Legs-12.stl", armR=PI + "193-PlasmaIncinerator-6.stl", armL=PY + "202-Pyreblaster-8.stl", cable=PI + "194-Cable-PlasmaIncinerator-6.stl", head="Helmets-Heads-Raw/8-Head-1.stl", pack="BackPacks-Raw/266-BackPack-1.stl")
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05), "back": (-0.4, -1, 0.25)}
for nm, root in marines:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    cols = [rend.ORANGE if str(o.get("tiow_category", "")) in ("Shoulder Pads", "Knee Pads") else
            rend.BLUE if str(o.get("tiow_category", "")) in ("Melee", "Pistols", "Shields", "Hand-less Weapons", "Two-Handed Guns", "Heavy Weapons", "Heavy Weapon Cables") else rend.GREY for o in obs]
    rend.render(scene, OUT, "pair_" + nm, obs, V, cols)
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/iv2_pairs.blend")
print("\nFAILS:", fails)
