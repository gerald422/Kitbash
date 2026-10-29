"""BBoosty + CyberBrush on Mar Fil, Turtle Ninja and the CyberBrush torso: arms, wrist sockets, hands, with-hand weapons,
two-hand blades, heads, packs, pauldrons (theirs and Mar Fil's), CyberBrush two-armed guns, legs on the CB torso."""
exec(open("/home/claude/test/v18/common18.py").read().replace('LIB = "/home/claude/test/kitlib"', 'LIB = "/home/claude/test/nclib"'))
import glob
OUT = "/home/claude/test/v114/out"
KL = "/home/claude/test/kitlib/"
MFT = glob.glob(KL + "**/23-Torso-2.stl", recursive=True)[0]
TNT = KL + "Turtle Ninja/TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"
P62 = glob.glob(KL + "**/ShoulderPads/62-ShoulderPad-1.stl", recursive=True)[0]
MFLEGS = KL + "Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/Legs-Raw/22-Legs-6.stl"
TNLEGS = KL + "Turtle Ninja/TurtleNinja's Mk7-8 Builder/Mk7-8/Legs/Lower A 1.stl"
BB = "BBoosty/"; MM = BB + "Medusas Mortals/Medusas Mortals/"; PR = BB + "Praetor with Paragon Blade/Praetor with Paragon Blade/"
CB = "CyberBrush/Space Bugs Hunters/"; CBT = "CyberBrush/Cyberbrush_3D_Pulses_2024_11_Light_armor_Marine_torso_&_Tactical/Light armor Marine torso & Tactical Equipments/Unsupported/Torso.stl"
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def child(p, t): return next((c for c in p.children if c.get("ws_type") == t), None)
roots = []
def put(target, rel, cat, want, label):
    select(target); o = send(rel, cat); ck(f"{label}: {os.path.basename(rel)} on {want}", on(o, want), T._state["last"])
    if cat == "Arms" and rel.startswith("CyberBrush"):
        ck(f"{label}: {os.path.basename(rel)} no wrist complaint (hand built in)", "no Hand" not in T._state["last"], T._state["last"])
    return o
def marine(nm, torso, x, R=None, L=None, pack=None, head=None, hr=None, hl=None, pr=None, pl=None, legs=None, two=None):
    select(None); t = send(torso, "Bodies", (x, 0, 0)); roots.append((nm, t)); out = dict(t=t)
    if R: out['r'] = put(t, R, "Arms", "Shoulder R", nm)
    if L: out['l'] = put(t, L, "Arms", "Shoulder L", nm)
    if two: out['two'] = put(t, two[0], two[1], "Shoulder R", nm)
    if pack: put(t, pack, "Backpacks", "Back", nm)
    if head: put(t, head, "Heads", "Neck", nm)
    if hr: out['hr'] = put(out['r'], hr[0], hr[1], "Hand R", nm)
    if hl: out['hl'] = put(out['l'], hl[0], hl[1], "Hand L", nm)
    if pr: out['pr'] = put(out['r'], pr, "Shoulder Pads", "Pad R", nm)
    if pl: out['pl'] = put(out['l'], pl, "Shoulder Pads", "Pad L", nm)
    if legs: out['legs'] = put(t, legs[0], "Legs", legs[1], nm)
    return out
m = []
m.append(marine("mf1", MFT, 0, MM + "Arms/RArm1.stl", MM + "Arms/LArm2_Bionic.stl", MM + "Backpacks/Backpack1_GearTrim.stl", BB + "Chaplain/Helmet.stl",
                hr=(MM + "Stuff/Hand_Fist.stl", "Hands"), pr=MM + "Stuff/ShoulderPad_Bolts.stl", pl=BB + "IH_Shoulderpads/IH_Shoulderpad_Sign.stl"))
m.append(marine("mf2", MFT, 40, MM + "Arms/RArm3.stl", MM + "Arms/LArm_Bionic_ForHoldingShield.stl", BB + "Chaplain/Backpack.stl", BB + "IronFather/Head.stl",
                hr=(BB + "Consul/PowerAxe.stl", "Melee"), hl=(MM + "Stuff/LHand_Bionic_SergantShield.stl", "Shields"), pr=BB + "Consul/ShoulderPad.stl", pl=P62))
m.append(marine("mf3", MFT, 80, PR + "Rarm_TwoHandedGrip.stl", PR + "LArm.stl", PR + "Backpack.stl", BB + "Chaplain/Head.stl",
                hr=(PR + "Paragon_Gear_TwoHands.stl", "Two-Handed Held"), pr=PR + "ShoulderPad_Logo_Bolts.stl", pl=BB + "IronFather/Shoulderpad.stl", legs=(MFLEGS, "Waist")))
m.append(marine("tn4", TNT, 120, MM + "Arms/RArm4.stl", MM + "Arms/LArm1.stl", MM + "Backpacks/Backpack2_PerpClaw.stl", BB + "Chaplain/Head_Wireless.stl",
                hr=(BB + "Chaplain/CroziusArcanum.stl", "Melee"), pr=BB + "Chaplain/ChaplainShoulderPad.stl", pl=BB + "IH_Shoulderpads/IH_Shoulderpad_ALTBlank.stl"))
m.append(marine("cb5", CBT, 160, CB + "Space Bug Hunter Axe/2.stl", CB + "Space Bug Hunters Claw/Space Bug Hunters Claw 1 (2).stl", CB + "Space Bug hunters Backpacks/1.stl",
                CB + "Space Bug Hunters Heads/Head 1.stl", pr=CB + "Space Bug Hunters Shoulder Pad/Space Bug Hunters Shoulder Pad set 1 (1).stl",
                pl=CB + "Space Bug Hunters Shoulder Pad/Space Bug Hunters Shoulder Pad set 2 (2).stl", legs=(TNLEGS, "Flat Waist")))
m.append(marine("mf6", MFT, 200, pack=CB + "Space Bug hunters Backpacks/3.stl", head=CB + "Broken Helmets/2.stl", two=(CB + "Space Bug Hunters Guns/1.stl", "Two-Handed Guns")))
m.append(marine("cb7", CBT, 240, MM + "Arms/RArm2.stl", MM + "Arms/LArm3.stl", MM + "Backpacks/Backpack1.stl", glob.glob(KL + "**/Helmet-Heads/1-Helmet-1.stl", recursive=True)[0],
                pr=P62, pl=MM + "Stuff/ShoulderPad_Logo_Studs.stl", legs=(MFLEGS, "Waist")))
m.append(marine("mf8", MFT, 280, CB + "Space Bug Hunters Fist/Space Bug Hunters Fist 4 (4).stl", CB + "Space Bug Hunters Knife/2.stl", CB + "Space Bug hunters Backpacks/5.stl",
                CB + "Space Bug Hunters Heads/Head 3.stl", pr=CB + "Space Bug Hunters Shoulder Pad/Space Bug Hunters Shoulder Pad set 1 (3).stl",
                pl=CB + "Space Bug Hunters Shoulder Pad/Space Bug Hunters Shoulder Pad set 2 (4).stl"))
# forearm armour: Josh's Forearm 3 placement on Mar Fil's 77 (own Forearm R socket), a mirrored one on 78 (own Forearm L),
# and on a CyberBrush arm and a BBoosty arm, whose Forearm sockets come from their Hand sockets
AMA = KL + "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/"
FA = CB + "Space Bug Hunters Forearms/Forearm %d.stl"
m.append(marine("mf9", MFT, 320, AMA + "77-Arm-1-R-B.stl", AMA + "78-Arm-1-L-A.stl"))
m[-1]['fr'] = put(m[-1]['r'], FA % 3, "Forearm Armour", "Forearm R", "mf9")
m[-1]['fl'] = put(m[-1]['l'], FA % 1, "Forearm Armour", "Forearm L", "mf9")
ck("mf9: left forearm mirrored", m[-1]['fl'] is not None and m[-1]['fl'].get("tiow_mirrored"))
m.append(marine("cb10", CBT, 360, MM + "Arms/RArm2.stl", MM + "Arms/LArm_Bionic_ForHoldingShield.stl"))
m[-1]['fr'] = put(m[-1]['r'], FA % 2, "Forearm Armour", "Forearm R", "cb10")
m[-1]['fl'] = put(m[-1]['l'], FA % 3, "Forearm Armour", "Forearm L", "cb10")
ck("cb10: BBoosty arm forearm socket is a rule one", m[-1]['fr'] is not None and m[-1]['fr'].parent.get("tiow_anchor") == "rule")
# the CyberBrush arms placed by the weakest sibling matches, and the four with no shoulder face (placed from a sibling)
def arm_side(rel):
    d = json.load(open(os.path.join(LIB, rel[:-4] + ".sockets.json")))
    return "R" if "Shoulder R" in d["fits"] else "L"
for nm, x, torso, rels in (("cb11", 400, CBT, ["Space Bug Hunters Chainsword/2.stl", "Space Bug Hunters Knife/1.stl"]),
                           ("mf12", 440, MFT, ["Space Bug Hunters Chainsword/4.stl", "Space Bug Hunters Knife/6.stl"]),
                           ("cb13", 480, CBT, ["Space Bug Hunters Sword/Unsupported/4.stl", "Space Bug Hunters Spears/Unsupported/4.stl"]),
                           ("mf14", 520, MFT, ["Space Bug Hunters Guns/3.stl", "Space Bug Hunters Knife/2.stl"]),
                           ("cb15", 560, CBT, ["Space Bug Hunters Fist/Space Bug Hunters Fist 4 (5).stl", "Space Bug Hunters Spears/Unsupported/1.stl"])):
    select(None); t = send(torso, "Bodies", (x, 0, 0)); roots.append((nm, t))
    for r in rels:
        sd = arm_side(CB + r); put(t, CB + r, "Arms", f"Shoulder {sd}", nm)
V = {"front": (0.25, 1, 0.1), "side": (1, 0, 0.05), "back": (-0.3, -1, 0.15), "top": (0.1, 0.4, 1)}
for nm, root in roots:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "nc_" + nm, obs, V, [rend.ORANGE if "BBoosty" in str(o.get("tiow_src", "")) else rend.BLUE if "CyberBrush" in str(o.get("tiow_src", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
