"""Outriders through the inbox: torso root, seated legs, the bike (rear body on the legs, every other part on its own
socket), base, the handlebar arm + free arm of each pose as assembled, a weapon in the free hand, pauldrons, shin pads,
belt bits; one rider with an IV2 hand holding an Outrider hand-less weapon."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v111/out"
K = "All Mar All the time/Outriders (1)/Outriders"
IV = "Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL"
PAR = json.load(open("/home/claude/kits/or/or_partial.json"))["side"]
TOR = {s['type']: M16(s['matrix']) for s in PAR["Outriders (1)/Outriders/Torsos/RawSTL/1-Torso-A.stl"]["sockets"]}
def fitM(rel, t): return M16(PAR["Outriders (1)/Outriders/" + rel]["fits"][t])
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") in ((want,) if isinstance(want, str) else want)
def put(host, rel, cat, want, label, sel=None, base=K):
    select(sel or host); p = send(f"{base}/{rel}", cat); ck(f"{label}: {os.path.basename(rel)} on {want}", on(p, want), T._state["last"]); return p
def rel_to(label, part, host, M, what, deg=0.05, mm=0.02):
    got = A(frame(host).inverted() @ frame(part)); ck(f"{label}: {what}", close(got, M, deg, mm), f"{ang(got, M):.2f} deg {np.linalg.norm(got[:3,3]-M[:3,3]):.3f} mm"); return got
BIKE = [("Bike/RawSTL/21-Body-2.stl", "Bike Front"), ("Bike/RawSTL/22-FrontWing.stl", "Front Wing"), ("Bike/RawSTL/23-FrontWheel.stl", "Front Wheel"),
        ("Bike/RawSTL/24-RearWheel.stl", "Rear Wheel"), ("Bike/RawSTL/25-ExhaustRight.stl", "Exhaust R"), ("Bike/RawSTL/26-ExhaustLeft.stl", "Exhaust L")]
marines = []
def rider(label, cursor, torso, legs, handle_arm, free_arm, weapon, guns, padR, padL, shin, belt, nohand_iv2=None):
    sd_h = "L" if "Left" in handle_arm else "R"; sd_f = "R" if sd_h == "L" else "L"
    select(None); t = send(f"{K}/Torsos/RawSTL/{torso}", "Bodies", cursor)
    ck(f"{label}: torso sockets", all(sock(t, k) for k in ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist")))
    lg = put(t, f"Legs/{legs}", "Bodies", "Waist", label)
    rel_to(label + " legs", lg, t, TOR["Waist"] @ fitM(f"Legs/{legs}", "Waist"), "seated like Josh's AM legs")
    ck(f"{label} legs: belt anchors", all(sock(lg, k) for k in ("Hip R", "Hip L", "Belt Front", "Belt Back")))
    bk = put(lg, "Bike/RawSTL/19-Body-1.stl", "Vehicles", "Bike", label); rel_to(label + " bike", bk, lg, np.eye(4), "under the rider as exported")
    for rel, want in BIKE + [(f"Bike/RawSTL/{'30-HandleLeft' if sd_h == 'R' else '29-HandleRight'}.stl", "Handle L" if sd_h == "R" else "Handle R"), (f"Bike/RawSTL/{guns}", "Bike Guns")]:
        p = put(lg, rel, "Vehicles", want, label)          # legs selected: each part still finds its own socket on the bike
        if p: rel_to(f"{label} {os.path.basename(rel)}", p, bk, np.eye(4), "as exported")
    bs = put(lg, "Base-90x52mm.stl", "Bases", "Base", label)
    arms = {}
    for rel, sd in ((handle_arm, sd_h), (free_arm, sd_f)):
        a = put(t, rel, "Arms", f"Shoulder {sd}", label); arms[sd] = a
        if a: rel_to(f"{label} {os.path.basename(rel)}", a, lg, np.linalg.inv(M16(PAR['Outriders (1)/Outriders/Legs/' + legs]['fits']['Waist'])) @ np.linalg.inv(TOR['Waist']) @ TOR[f'Shoulder {sd}'] @ fitM(rel, f'Shoulder {sd}'), "as assembled on its legs")
    if arms.get(sd_f):
        ck(f"{label}: free arm has its Hand {sd_f}", sock(arms[sd_f], f"Hand {sd_f}") is not None, T._state["last"])
        if nohand_iv2:
            h = put(arms[sd_f], f"Hands-Raw/{'Hand-Left/274-Hand-2-L' if sd_f == 'L' else '273-Hand-1-R'}.stl", "Hands", f"Hand {sd_f}", label, base=IV)
            if h: put(h, f"Weapons/WeaponsRawSTL(Right)/{nohand_iv2}", "Weapons", f"Grip {sd_f}", label)
        elif weapon: put(arms[sd_f], weapon, "Weapons", f"Hand {sd_f}", label)
    if padR and arms.get("R"): put(arms["R"], f"ShoulderPads/RawSTL/{padR}", "Shoulder Pads", "Pad R", label)
    if padL and arms.get("L"): put(arms["L"], f"ShoulderPads/RawSTL/{padL}", "Shoulder Pads", "Pad L", label)
    for sd in "RL":
        s_ = sock(lg, f"Shin {sd}"); ck(f"{label} legs: Shin {sd} anchor found", s_ is not None)
        if s_ is not None:
            mir = 'RawSTL-Mirrored(Left)/' + shin.replace('.stl', '-Mirrored.stl')
            if sd == 'L' and not os.path.exists(f"{LIB}/{K}/ShinPads/{mir}"): mir = 'RawSTL(Right)/' + shin    # no left copy: the add-on mirrors the right one
            put(lg, f"ShinPads/{'RawSTL(Right)/' + shin if sd == 'R' else mir}", "Knee Pads", f"Shin {sd}", label, sel=s_)
    for rel in belt:
        put(lg, f"Accesories/{rel}", "Accessories", ("Hip R", "Hip L", "Belt Front", "Belt Back"), label)
    marines.append((label, t))
rider("orA", (0, 0, 0), "1-Torso-A.stl", "RawSTL/1-Legs-A.stl", "Arms(WithHandles)/RawSTL(Right)/7-ArmWithHandle-Right-A.stl", "Arms/RawSTL-Mirrored-(Left)/13-Arm-1-Mirrored-A.stl",
      "Weapons/WeaponsRawSTLMirrored(Left)/33-HeavyPistol-Mirrored.stl", "31-BoltersTwins.stl", "1-ShoulderPad-R.stl", "2-ShoulderPad-L.stl", "1-ShinPad-1.stl",
      ("AccesoriesRawSTL/46-Holster-1.stl", "AccesoriesRawSTL/48-Pouch-1.stl", "AccesoriesRawSTL/51-PuritySeal-1.stl"))
rider("orB", (110, 0, 0), "3-Torso-BA.stl", "RawSTL/2-Legs-B.stl", "Arms(WithHandles)/RawSTL(Right)/8-ArmWithHandle-Right-B.stl", "Arms/RawSTL-Mirrored-(Left)/14-Arm-2-Mirrored-B.stl",
      "Weapons/WeaponsRawSTLMirrored(Left)/34-ChainSword-A-Mirrored.stl", "32-PlasmaTwins.stl", "9-ShoulderPad-DW-1.stl", "10-ShoulderPad-DW-2.stl", "2-ShinPad-2.stl",
      ("AccesoriesRawSTL-Mirrored/47-Holster-2-Mirrored.stl", "AccesoriesRawSTL/50-Pouch-3.stl"))
rider("orDm", (220, 0, 0), "6-Torso-DW.stl", "MirroredRawSTL/4-Legs-D-Mirrored.stl", "Arms(WithHandles)/RawSTL-Mirrored(Left)/10-ArmWightHandle-Left-D-2.stl", "Arms/RawSTL(Right)/16-Arm-4.stl",
      "Weapons/WeaponsRawSTL(Right)/40-Axe-A.stl", "31-BoltersTwins.stl", "1-ShoulderPad-R.stl", "12-ShoulderPad-IF-2.stl", "4-ShinPad-4.stl", ("AccesoriesRawSTL/49-Pouch-2.stl",))
rider("orE", (330, 0, 0), "12-Torso-ULTRA.stl", "RawSTL/5-Legs-E.stl", "Arms(WithHandles)/RawSTL(Right)/11-ArmWithHandle-Right-E.stl", "Arms/RawSTL-Mirrored-(Left)/17-Arm-5-Mirrored-A.stl",
      "Weapons/WeaponsRawSTLMirrored(Left)/43-Hammer-A-Mirrored.stl", "32-PlasmaTwins.stl", "1-ShoulderPad-R.stl", "22-ShoulderPad-ULTRA-2.stl", "18-ShinPad-ULTRA.stl", ())
rider("orFm", (440, 0, 0), "8-Torso-IH.stl", "MirroredRawSTL/6-Legs-F-Mirrored.stl", "Arms(WithHandles)/RawSTL-Mirrored(Left)/12-ArmWightHandle-Left-F-1.stl", "Arms/RawSTL(Right)/18-Arm-6.stl",
      None, "31-BoltersTwins.stl", "1-ShoulderPad-R.stl", "14-ShoulderPad-IH-2.stl", "14-ShinPad-IH.stl", ("AccesoriesRawSTL/52-PuritySeal-2.stl",), nohand_iv2="39-SwordNoHand.stl")
rider("orCm", (550, 0, 0), "9-Torso-RG.stl", "MirroredRawSTL/3-Legs-C-Mirrored.stl", "Arms(WithHandles)/RawSTL-Mirrored(Left)/9-ArmWightHandle-Left-C-1.stl", "Arms/RawSTL(Right)/15-Arm-3.stl",
      "Weapons/WeaponsRawSTL(Right)/37-Sword-A.stl", "32-PlasmaTwins.stl", "1-ShoulderPad-R.stl", "16-ShoulderPad-RG-2.stl", "15-ShinPad-RG.stl", ())
V = {"front": (1, 0.15, 0.15), "q": (0.6, 0.75, 0.3), "side": (0, 1, 0.08), "back": (-0.6, -0.75, 0.3)}
for nm, root in marines:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    cols = [rend.ORANGE if str(o.get("tiow_category", "")) in ("Shoulder Pads", "Knee Pads", "Accessories", "Seals") else
            rend.BLUE if str(o.get("tiow_category", "")) in ("Melee", "Pistols", "Hand-less Weapons", "Hands") else
            (0.55, 0.8, 0.5, 1) if str(o.get("tiow_category", "")) in ("Bikes", "Bike Parts") else rend.GREY for o in obs]
    rend.render(scene, OUT, nm, obs, V, cols)
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/or_test.blend")
print("\nFAILS:", fails)
