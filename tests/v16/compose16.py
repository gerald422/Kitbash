import os
exec(open('/home/claude/test/both/compose.py').read().split("compose('shin_pads")[0])
os.chdir("/home/claude/test/v16/out")
def row(stem, caps): return [(f"{stem}_{v}.png", c) for v, c in zip(("front", "right", "left"), caps)]
compose('v16_shins_marfil.png', [
    row("shin_marfil_29", ("29-Legs-2: 68 R, 71 mirrored L", "right side", "left side")),
    row("shin_marfil_35", ("Legs 35: 68 R, 71 mirrored L", "right side", "left side")),
    row("shin_marfil_LO_35", ("35: 72 R, LeftOrientated 72 L", "right side", "left side")),
    row("shin_vbs_29", ("29: Vet. Blade 30 R, 30-Mirrored L", "right side", "left side")),
    row("shin_vbs_flame_35", ("35: Flame R, 33 mirrored L", "right side", "left side"))],
    scale=0.45, title="Mar Fil shin pads from their folders' fits (Techmarine rig), shin anchors found on the legs")
compose('v16_shins_marta.png', [
    row("shin_marta_29", ("29: Chin_pad_2 R / L", "right side", "left side")),
    row("shin_marta_35", ("35: Chin_pad_2 R / L", "right side", "left side")),
    row("shin_marta6_29", ("29: Chin_pad_6 R / L_with_I", "right side", "left side"))],
    scale=0.45, title="Marta's shin pads (each pad's own fit, from the rig), on Mar Fil legs")
def prow(stem, cap): return [(f"{stem}_front.png", cap), (f"{stem}_right.png", "right side"), (f"{stem}_top.png", "from above")]
compose('v16_pauldrons_arms.png', [
    prow("pads_76_62", "Arm 76 (your example), 62"), prow("pads_111_62", "Arm 111, 62"), prow("pads_101_62", "Arm 101, 62"),
    prow("pads_126_62", "Arm 126 (raised), 62"), prow("pads_131_62", "Arm 131 (out), 62")],
    scale=0.45, title="Pauldrons from your example (62 on 76), arms' Pad anchors copied from 76, left side mirrored")
compose('v16_pauldrons_pads.png', [
    prow("pads_131_63", "63, left mirrored"), prow("pads_131_66", "66 R, 67 mirrored L"),
    prow("pads_131_56", "Vet. Blade 56 R, 57-Mirrored L"), prow("pads_131_death", "Death pad R, 58 mirrored L"),
    prow("pads_131_tn", "Turtle Ninja 1 R, 2 mirrored L")],
    scale=0.45, title="Other shoulder pads from their folders' fits, on arm 131")
