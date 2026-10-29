from PIL import Image, ImageDraw, ImageFont
def sheet(rows, out, cell=300, title=None):
    """rows: list of lists of (png, caption)"""
    W = max(len(r) for r in rows) * cell; H = len(rows) * (cell + 22) + (30 if title else 0)
    im = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14); ft = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    except Exception: f = ft = None
    y = 0
    if title: d.text((8, 6), title, fill=(0, 0, 0), font=ft); y = 30
    for r in rows:
        for i, (p, c) in enumerate(r):
            try: t = Image.open(p).convert('RGB'); t.thumbnail((cell, cell)); im.paste(t, (i * cell, y))
            except Exception: pass
            d.text((i * cell + 4, y + cell + 3), c, fill=(0, 0, 0), font=f)
        y += cell + 22
    im.save(out); return out
