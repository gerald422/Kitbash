import sys, json
from PIL import Image, ImageDraw
files = json.loads(sys.argv[1]); out = sys.argv[2]; title = sys.argv[3] if len(sys.argv) > 3 else ''
ims = [Image.open(f).convert('RGB') for f in files.values()]
W = sum(i.width for i in ims); H = max(i.height for i in ims) + 22
m = Image.new('RGB', (W, H), 'white'); x = 0
for (k, f), im in zip(files.items(), ims):
    m.paste(im, (x, 22)); ImageDraw.Draw(m).text((x + 6, 4), k + '  ' + title if x == 0 else k, fill='black'); x += im.width
m.save(out, quality=85); print(out)
