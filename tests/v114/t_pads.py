"""Close-ups of every BBoosty / CyberBrush pauldron family on a right arm (BBoosty RArm1 on Mar Fil) and mirrored on a left arm."""
exec(open("/home/claude/test/v18/common18.py").read().replace('LIB = "/home/claude/test/kitlib"', 'LIB = "/home/claude/test/nclib"'))
import glob
OUT = "/home/claude/test/v114/out"
KL = "/home/claude/test/kitlib/"
MFT = glob.glob(KL + "**/23-Torso-2.stl", recursive=True)[0]
BB = "BBoosty/"; MM = BB + "Medusas Mortals/Medusas Mortals/"; PR = BB + "Praetor with Paragon Blade/Praetor with Paragon Blade/"
CB = "CyberBrush/Space Bugs Hunters/Space Bug Hunters Shoulder Pad/"
PADS = [MM + "Stuff/ShoulderPad_Bolts.stl", MM + "Stuff/ShoulderPad_Logo_Studs.stl", PR + "ShoulderPad_Bolts.stl", BB + "Consul/ShoulderPad.stl",
        BB + "Consul/ShoulderPad_Studs.stl", BB + "Chaplain/ChaplainShoulderPad.stl", BB + "IronFather/Shoulderpad.stl", BB + "IronFather/IHShoulderpad.stl",
        BB + "IH_Shoulderpads/IH_Shoulderpad_ALTBlank.stl", BB + "IH_Shoulderpads/IH_Shoulderpad_ALTSign.stl", BB + "IH_Shoulderpads/IH_Shoulderpad_Blank.stl",
        BB + "IH_Shoulderpads/IH_Shoulderpad_BlankChains.stl", BB + "IH_Shoulderpads/IH_Shoulderpad_Dots.stl", BB + "IH_Shoulderpads/IH_Shoulderpad_Sign.stl",
        CB + "Space Bug Hunters Shoulder Pad set 1 (1).stl", CB + "Space Bug Hunters Shoulder Pad set 2 (2).stl",
        CB + "Space Bug Hunters Shoulder Pad set 1 (2).stl", CB + "Space Bug Hunters Shoulder Pad set 1 (4).stl"]
VR = {"fr": (0.8, 1, 0.35), "out": (1, 0.1, 0.2)}
VL = {"fl": (-0.8, 1, 0.35), "outl": (-1, 0.1, 0.2)}
ONLY = [int(x) for x in os.environ.get("PADS_ONLY", "").split(",") if x]
for i, p in enumerate(PADS):
    if ONLY and i not in ONLY: continue
    select(None); t = send(MFT, "Bodies", (i * 40, 0, 0))
    select(t); r = send(MM + "Arms/RArm1.stl", "Arms"); select(t); l = send(MM + "Arms/LArm2_Sh.stl" if False else MM + "Arms/LArm_Bionic_ForHoldingShield.stl", "Arms")
    select(r); pr = send(p, "Shoulder Pads"); ck(f"{os.path.basename(p)} on Pad R", pr is not None and pr.parent is not None and pr.parent.get("ws_type") == "Pad R", T._state["last"])
    select(l); pl = send(p, "Shoulder Pads"); ck(f"{os.path.basename(p)} on Pad L", pl is not None and pl.parent is not None and pl.parent.get("ws_type") == "Pad L", T._state["last"])
    nm = "pad%02d" % i
    rend.render(scene, OUT, nm + "R", [t, r, pr], VR, [rend.GREY, rend.ORANGE, rend.BLUE])
    rend.render(scene, OUT, nm + "L", [t, l, pl], VL, [rend.GREY, rend.ORANGE, rend.BLUE])
print("\nFAILS:", fails)
