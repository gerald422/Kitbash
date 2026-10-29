import sys, glob, os
from PIL import Image, ImageDraw
out, pat = sys.argv[1], sys.argv[2]; names = sys.argv[3:]
views = ['front', 'side', 'back', 'top']; S = 380
rows = []
for nm in names:
    ims = [Image.open(f"{pat}{nm}_{v}.png").convert('RGB').resize((S, S)) for v in views if os.path.exists(f"{pat}{nm}_{v}.png")]
    row = Image.new('RGB', (S * 4, S + 18), 'white'); [row.paste(im, (i * S, 18)) for i, im in enumerate(ims)]
    ImageDraw.Draw(row).text((4, 3), nm, fill='black'); rows.append(row)
g = Image.new('RGB', (S * 4, sum(r.height for r in rows)), 'white'); y = 0
for r in rows: g.paste(r, (0, y)); y += r.height
g.save(out, quality=85); print(out, g.size)
