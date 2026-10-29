"""Vet and Bladeguard marines through the inbox: chest root, legs, arms with weapons (hands by rule), two-handers,
heavy weapon + cable, helmet, backpack + topper, pauldrons, shin pads. Renders each."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v19/out"; os.makedirs(OUT, exist_ok=True)
VS = "All Mar All the time/VeteranSquad/VeteranSquad"; BG = "All Mar All the time/VeteranBladeSquad/VeteranBladeSquad"
def on(p, want): return p is not None and p.parent is not None and (p.parent.get("ws_type") in want if isinstance(want, tuple) else p.parent.get("ws_type") == want)
def put(host, rel, cat, want, label):
    select(host); p = send(rel, cat); ck(f"{label}: on {want}", on(p, want), T._state["last"]); return p
def kitpos(label, part, root):
    """part sits where Mar Fil exported it relative to the chest (kit position)"""
    got = A(frame(root).inverted() @ frame(part)); ck(f"{label}: in kit position on the chest", close(got, np.eye(4), 0.05, 0.02), f"{ang(got, np.eye(4)):.2f} deg {np.linalg.norm(got[:3,3]):.3f} mm")
marines = []
SEAT = json.load(open("/home/claude/kits/vet/legs_seat.json"))
def marine(label, cursor, chest, legs, armR=None, wR=None, armL=None, wL=None, two=None, heavy=None, cable=None, head=None, pack=None, topper=None, padR=None, padL=None, shinR=None, shinL=None, cats=None):
    select(None); t = send(chest, "Bodies", cursor)
    ck(f"{label}: chest has its sockets", all(sock(t, k) for k in ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist")))
    lg = put(t, legs, "Bodies", "Waist", f"{label} legs")
    Ms = np.array(SEAT[legs.split("All Mar All the time/", 1)[1]]["M"]); got = A(frame(t).inverted() @ frame(lg))
    ck(f"{label} legs: seated like Josh's AM legs", close(got, Ms, 0.05, 0.02), f"{ang(got, Ms):.2f} deg {np.linalg.norm(got[:3,3]-Ms[:3,3]):.3f} mm")
    ck(f"{label} legs: hips", all(sock(lg, k) for k in ("Hip R", "Hip L")))
    aR = aL = None
    if armR: aR = put(t, armR, "Arms", "Shoulder R", f"{label} arm R")
    if armL: aL = put(t, armL, "Arms", "Shoulder L", f"{label} arm L")
    if wR: put(aR, wR, "Weapons", "Hand R", f"{label} right hand")
    if wL: put(aL, wL, "Weapons", "Hand L", f"{label} left hand")
    if two: tw = put(t, two, "Weapons", "Shoulder R", f"{label} two-hander"); kitpos(f"{label} two-hander", tw, t)
    if heavy:
        hv = put(t, heavy, "Heavy Weapons", "Shoulder R", f"{label} heavy weapon"); kitpos(f"{label} heavy", hv, t)
        if cable: cb = put(hv, cable, "Heavy Weapons", "Cable", f"{label} cable"); kitpos(f"{label} cable", cb, t)
    if head: put(t, head, "Heads", "Neck", f"{label} head")
    if pack:
        pk = put(t, pack, "Backpacks", "Back", f"{label} backpack"); kitpos(f"{label} backpack", pk, t)
        if topper: tp = put(pk, topper, "Backpacks", "Back Top", f"{label} topper"); kitpos(f"{label} topper", tp, t)
    if padR and aR: put(aR, padR, "Shoulder Pads", "Pad R", f"{label} pauldron R")
    if padL and aL: put(aL, padL, "Shoulder Pads", "Pad L", f"{label} pauldron L")
    if shinR:
        select(sock(lg, "Shin R")); p = send(shinR, "Knee Pads"); ck(f"{label} shin pad R", on(p, "Shin R"), T._state["last"])
    if shinL:
        select(sock(lg, "Shin L")); p = send(shinL, "Knee Pads"); ck(f"{label} shin pad L", on(p, "Shin L"), T._state["last"])
    marines.append((label, t))
    return t
marine("vs1", (0, 0, 0), f"{VS}/Body/Body-RawSTL/12-Chest-A.stl", f"{VS}/Body/Body-RawSTL/17-Body-A.stl",
       armR=f"{VS}/Arms/Arms-RawSTL/142-Arm-A.stl", wR=f"{VS}/Melee/Melee-RawSTL/132-Sword-B.stl",
       armL=f"{VS}/Arms/Arms-Mirrored/143-Arm-B-Mirrored.stl", wL=f"{VS}/Weapons/Weapons-Mirrored/100-Gun-5-B-Mirrored.stl",
       head=f"{VS}/Helmets/Helmet-RawStl/1-Helmet-A.stl", pack=f"{VS}/Backpacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/1.stl", topper=f"{VS}/Backpacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/7.stl",
       padR=f"{VS}/ShoulderPads/ShoulderPads-RawSTL/44-ShoulderPad-R-A.stl", padL=f"{VS}/ShoulderPads/ShoulderPads-RawSTL/57-ShoulderPad-L-A.stl",
       shinR=f"{VS}/ShinPads/ShinPads-RawSTL/31-ShinPad-A.stl", shinL=f"{VS}/ShinPads/ShinPads-Mirrored/31-ShinPad-A-Mirrored.stl")
marine("vs2", (60, 0, 0), f"{VS}/Body/Body-RawSTL/13-Chest-B.stl", f"{VS}/Body/Body-RawSTL/20-Body-D.stl",
       heavy=f"{VS}/HeavyWeapons/HeavyWeapons-RawSTL/121-HeavyGun-A.stl", cable=f"{VS}/HeavyWeapons/HeavyWeapons-RawSTL/122-HeavyGun-Cable-A.stl",
       head=f"{VS}/Helmets/Helmet-RawStl/9-Head-A.stl", pack=f"{VS}/Backpacks/BackPacks-RawSTL/23-Backpack-A.stl",
       shinR=f"{VS}/ShinPads/ShinPads-RawSTL/34-ShinPad-D.stl", shinL=f"{VS}/ShinPads/ShinPads-Mirrored/34-ShinPad-D-Mirrored.stl")
marine("vs3", (120, 0, 0), f"{VS}/Body/Body-RawSTL/14-Chest-C.stl", f"{VS}/Body/Body-Mirrored/21-Body-E-Mirrored.stl",
       two=f"{VS}/Weapons/Weapons-RawSTL/70-Gun-1-A.stl", head=f"{VS}/Helmets/Helmet-RawStl/2-Helmet-B.stl", pack=f"{VS}/Backpacks/BackPacks-RawSTL/26-Backpack-D.stl")
marine("bg1", (180, 0, 0), f"{BG}/Body/Body-RawSTL/17-Chest-1.stl", f"{BG}/Body/Body-RawSTL/19-Legs-1-A.stl",
       armR=f"{BG}/Arms/Arms-RawSTL/37-Arm-1-B.stl", wR=f"{BG}/Melee/Melee-RawSTL/Swords/73-Sword-1-A.stl",
       armL=f"{BG}/Arms/Arms-Mirrored/38-Arm-2-A-Mirrored.stl", wL=f"{BG}/Shields/Shields-Mirrored/133-Mirrored.stl",
       head=f"{BG}/Helmets/Helmets-RawSTL/1-Helmet-1-A.stl", pack=f"{BG}/BackPacks/Backpacks-RawSTL/61-Backpack-1.stl",
       padR=f"{BG}/ShoulderPads/ShoulderPads-RawSTL/56-ShoulderPad-1.stl", padL=f"{BG}/ShoulderPads/ShoulderPads-Mirrored/56-ShoulderPad-1-Mirrored.stl",
       shinR=f"{BG}/Shin-Pads/Shin-Pads-RawSTL/29-Shin-Pad-1.stl", shinL=f"{BG}/Shin-Pads/Shin-Pads-Mirrored/29-Shin-Pad-1-Mirrored.stl")
marine("bg2", (240, 0, 0), f"{BG}/Body/Body-RawSTL/18-Chest-2.stl", f"{BG}/Body/Body-RawSTL/21-Legs-2-A.stl",
       two=f"{BG}/DoubleHandedMelee/DoubleHandedMelee-RawSTL/145-GreatSword-A.stl", head=f"{BG}/Helmets/Helmets-RawSTL/3-Helmet-2-A.stl",
       pack=f"{BG}/BackPacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/2.stl", topper=f"{BG}/BackPacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/10.stl",
       shinR=f"{BG}/Shin-Pads/Shin-Pads-RawSTL/31-Shin-Pad-3.stl", shinL=f"{BG}/Shin-Pads/Shin-Pads-Mirrored/31-Shin-Pad-3-Mirrored.stl")
marine("bg3", (300, 0, 0), f"{BG}/Body/Body-RawSTL/17-Chest-1.stl", f"{BG}/Body/Body-Mirrored/24-Mirrored.stl",
       armR=f"{BG}/Arms/Arms-RawSTL/40-Arm-3-A.stl", wR=f"{BG}/Melee/Melee-RawSTL/Hammers-Mace/109-Hammer-1-A.stl",
       armL=f"{BG}/Additional/159-SwordHandled-A.stl", head=f"{BG}/Helmets/Helmets-RawSTL/12-Head-1-B.stl", pack=f"{BG}/BackPacks/Backpacks-RawSTL/63-Backpack-3.stl",
       padR=f"{BG}/ShoulderPads/ShoulderPads-RawSTL/57-ShoulderPad-2.stl", padL=f"{BG}/ShoulderPads/ShoulderPads-Mirrored/57-ShoulderPad-2-Mirrored.stl")
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05), "back": (-0.4, -1, 0.25)}
for nm, root in marines:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    cols = [rend.ORANGE if str(o.get("tiow_category", "")) in ("Shoulder Pads", "Knee Pads") else rend.BLUE if str(o.get("tiow_category", "")) in ("Melee", "Pistols", "Shields", "Two-Handed Melee", "Two-Handed Guns", "Heavy Weapons", "Heavy Weapon Cables") else rend.GREY for o in obs]
    rend.render(scene, OUT, "vet_" + nm, obs, V, cols)
print("\nFAILS:", fails)
