import sys
from PIL import Image, ImageDraw, ImageFont
def compose(out, rows, scale=0.6, title=""):
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16); fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except OSError:
        f = fs = ImageFont.load_default()
    ims = [[(Image.open(p), cap) for p, cap in r] for r in rows]
    W, H = ims[0][0][0].size; tw, th = int(W * scale), int(H * scale)
    cols = max(len(r) for r in ims); head = 34 if title else 0
    s = Image.new('RGB', (tw * cols, head + (th + 24) * len(ims)), (48, 48, 48)); d = ImageDraw.Draw(s)
    if title: d.text((10, 8), title, fill=(240, 240, 240), font=f)
    for ri, r in enumerate(ims):
        for ci, (im, cap) in enumerate(r):
            x, y = ci * tw, head + ri * (th + 24)
            s.paste(im.resize((tw, th)), (x, y + 22)); d.text((x + 8, y + 4), cap, fill=(225, 225, 225), font=fs)
    s.save(out); print(out, s.size)
compose('shin_pads_both_legs.png', [
    [('shins_29_front.png', '29-Legs-2: front'), ('shins_29_right.png', 'right side'), ('shins_29_left.png', 'left side')],
    [('shins_35_front.png', 'Jump legs 35: front'), ('shins_35_right.png', 'right side'), ('shins_35_left.png', 'left side')]],
    title='Shin pads, both legs (fit saved once on 29-Legs-2, reused on the jump legs)')
compose('pauldrons_both_arms.png', [
    [('pads_111_front.png', 'Arm 111, hanging: front'), ('pads_111_right.png', 'right side'), ('pads_111_top.png', 'from above')],
    [('pads_101_front.png', 'Arm 101, forward: front'), ('pads_101_right.png', 'right side'), ('pads_101_top.png', 'from above')],
    [('pads_126_front.png', 'Arm 126, raised forward: front'), ('pads_126_right.png', 'right side'), ('pads_126_top.png', 'from above')],
    [('pads_131_front.png', 'Arm 131, out to the side: front'), ('pads_131_right.png', 'right side'), ('pads_131_top.png', 'from above')]],
    scale=0.45, title='Pauldrons on both arms, carried across each arm swap (fit saved once, on arm 111)')
compose('belt_both_hips.png', [
    [('belt_29_front.png', 'front'), ('belt_29_right.png', 'right side'), ('belt_29_left.png', 'left side'), ('belt_29_back.png', 'back')]],
    scale=0.5, title='Pouches on both hips')
