import os
exec(open('/home/claude/test/both/compose.py').read().split("compose('shin_pads")[0])
os.chdir("/home/claude/test/variants/out")
compose('shin_pads_marfil_29-32.png', [
    [('marfilB_29_front.png', '29-Legs-2: front (R 30-Shin-Pad-2, L 31-Shin-Pad-3)'), ('marfilB_29_right.png', 'right side'), ('marfilB_29_left.png', 'left side')],
    [('marfilB_35_front.png', 'Jump legs 35: front (R 32, L 30)'), ('marfilB_35_right.png', 'right side'), ('marfilB_35_left.png', 'left side')]],
    title='Mar Fil shin pads 29-32 on the assault legs (fit saved once, from 29-Shin-Pad-1 placed by eye on 29-Legs-2)')
compose('shin_pads_marta.png', [
    [('marta_29_front.png', '29-Legs-2: front (Chin_pad_3_R, Chin_pad_3_L)'), ('marta_29_right.png', 'right side'), ('marta_29_left.png', 'left side')],
    [('marta_35_front.png', 'Jump legs 35: front (Chin_pad_1_R, Chin_pad_3_L)'), ('marta_35_right.png', 'right side'), ('marta_35_left.png', 'left side')]],
    title="Marta's shin pads on the assault legs (fit saved once, from Chin_pad_2 R/L placed by eye on 29-Legs-2)")
compose('pauldrons_on_the_arm.png', [
    [('pads_111_front.png', 'Arm 111, hanging: front'), ('pads_111_right.png', 'right side'), ('pads_111_top.png', 'from above')],
    [('pads_101_front.png', 'Arm 101, forward: front'), ('pads_101_right.png', 'right side'), ('pads_101_top.png', 'from above')],
    [('pads_126_front.png', 'Arm 126, raised forward: front'), ('pads_126_right.png', 'right side'), ('pads_126_top.png', 'from above')],
    [('pads_131_front.png', 'Arm 131, out to the side: front'), ('pads_131_right.png', 'right side'), ('pads_131_top.png', 'from above')],
    [('pads_131_57_front.png', 'Pad 57 swapped in (arm 131): front'), ('pads_131_58_front.png', 'Pad 58 (R) swapped in: front'), ('pads_131_58_top.png', 'from above')]],
    scale=0.45, title='Pauldrons sitting on the arm, both arms, carried across each arm swap (fit saved once, on arm 111)')
