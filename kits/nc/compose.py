import json, os
from PIL import Image, ImageDraw, ImageFont
TMP = "/tmp/claude-0/sheet"; OUT = "/home/claude/kits/nc/sheets"
meta = json.load(open(TMP + '/meta.json')); font = ImageFont.load_default()
for g, items in meta.items():
    tiles = []
    for nm, fs, lo, hi in items:
        ims = [Image.open(fs[k]).convert('RGB') for k in ("front", "side", "top")]
        tile = Image.new('RGB', (900, 330), 'white'); [tile.paste(im, (i * 300, 0)) for i, im in enumerate(ims)]
        d = ImageDraw.Draw(tile)
        d.text((4, 302), nm[:90], fill='black', font=font)
        d.text((4, 316), 'x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f   (front -Y | side +X | top +Z)' % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]), fill='black', font=font)
        tiles.append(tile)
    for k in range(0, len(tiles), 12):
        part = tiles[k:k + 12]; rows = (len(part) + 1) // 2
        sheet = Image.new('RGB', (1800, rows * 330), 'white')
        for i, t in enumerate(part): sheet.paste(t, ((i % 2) * 900, (i // 2) * 330))
        sheet.save(f"{OUT}/{g.replace(' ', '_')[:80]}_{k // 12}.jpg", quality=80)
print(len(os.listdir(OUT)))
