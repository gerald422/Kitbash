"""BBoosty phase 1 on Mar Fil and Turtle Ninja torsos: arms (shoulder disc), wrist sockets, hands, with-hand weapons,
two-handed swords (meet the other hand), heads, packs."""
exec(open("/home/claude/test/v18/common18.py").read().replace('LIB = "/home/claude/test/kitlib"', 'LIB = "/home/claude/test/nclib"'))
import glob
OUT = "/home/claude/test/v114/out"
KL = "/home/claude/test/kitlib/"
MFT = glob.glob(KL + "**/23-Torso-2.stl", recursive=True)[0]
TNT = KL + "Turtle Ninja/TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"
BB = "BBoosty/"; MM = BB + "Medusas Mortals/Medusas Mortals/"; PR = BB + "Praetor with Paragon Blade/Praetor with Paragon Blade/"
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def child(p, t): return next((c for c in p.children if c.get("ws_type") == t), None)
roots = []
def marine(torso, x, R, L, pack, head, hand_r=None, hand_l=None, nm=""):
    select(None); t = send(torso, "Bodies", (x, 0, 0)); roots.append((nm, t))
    r = send(R, "Arms"); ck(f"{nm}: {os.path.basename(R)} on Shoulder R", on(r, "Shoulder R"), T._state["last"])
    select(t); l = send(L, "Arms"); ck(f"{nm}: {os.path.basename(L)} on Shoulder L", on(l, "Shoulder L"), T._state["last"])
    select(t); p = send(pack, "Backpacks"); ck(f"{nm}: pack on Back", on(p, "Back"), T._state["last"])
    select(t); h = send(head, "Heads"); ck(f"{nm}: head on Neck", on(h, "Neck"), T._state["last"])
    out = [t, r, l, p, h]
    if hand_r:
        select(r); w = send(hand_r[0], hand_r[1]); ck(f"{nm}: {os.path.basename(hand_r[0])} on Hand R", on(w, "Hand R"), T._state["last"]); out.append(w)
    if hand_l:
        select(l); w = send(hand_l[0], hand_l[1]); ck(f"{nm}: {os.path.basename(hand_l[0])} on Hand L", on(w, "Hand L"), T._state["last"]); out.append(w)
    return out
m1 = marine(MFT, 0, MM + "Arms/RArm1.stl", MM + "Arms/LArm2_Bionic.stl", MM + "Backpacks/Backpack1_GearTrim.stl", BB + "Chaplain/Helmet.stl",
            hand_r=(MM + "Stuff/Hand_Fist.stl", "Hands"), nm="mf1")
m2 = marine(MFT, 40, MM + "Arms/RArm3.stl", MM + "Arms/LArm_Bionic_ForHoldingShield.stl", BB + "Chaplain/Backpack.stl", BB + "IronFather/Head.stl",
            hand_r=(BB + "Consul/PowerAxe.stl", "Melee"), hand_l=(MM + "Stuff/Bionic_Hand_Pointing.stl", "Hands"), nm="mf2")
m3 = marine(MFT, 80, PR + "Rarm_TwoHandedGrip.stl", PR + "LArm.stl", PR + "Backpack.stl", BB + "Chaplain/Head.stl",
            hand_r=(PR + "Two_Handed_Power_Sword_Gear.stl", "Two-Handed Held"), nm="mf3")
m4 = marine(TNT, 120, MM + "Arms/RArm4.stl", MM + "Arms/LArm1.stl", MM + "Backpacks/Backpack2_PerpClaw.stl", BB + "Chaplain/Head_Wireless.stl",
            hand_r=(BB + "Chaplain/CroziusArcanum.stl", "Melee"), nm="tn4")
m5 = marine(MFT, 160, BB + "Chaplain/ChaplainRArm.stl", BB + "Chaplain/LArm.stl", BB + "IronFather/Backpack.stl", BB + "Consul/Helmet.stl",
            hand_r=(BB + "Chaplain/PlasmaPistol.stl", "Pistols"), hand_l=(BB + "Chaplain/Hand.stl", "Hands"), nm="mf5")
V = {"front": (0.25, 1, 0.1), "side": (1, 0, 0.05), "back": (-0.3, -1, 0.15), "top": (0.1, 0.4, 1)}
for nm, root in roots:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "bb_" + nm, obs, V, [rend.ORANGE if "BBoosty" in str(o.get("tiow_src", "")) else rend.GREY for o in obs])
print("\nFAILS:", fails)
