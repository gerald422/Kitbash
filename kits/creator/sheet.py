"""Contact sheet for add_creator.py: every part on one grid, each scaled to its cell (its real size in the label),
rendered straight on from -Y and from +Y (two renders in all), numbered. Confirms up / front before any rule runs
and shows sculpted aquilas, seals and scrolls.
    /home/claude/bpyenv/bin/python sheet.py -- JOB.json
JOB: {"items": [[stl_path, label], ...], "scale": 1.0, "out": "sheet.jpg", "px": 2600}
Without PIL (Blender's own Python, on the PC) the labels are Blender text and the two views stay two files:
<out>_front.png and <out>_back.png."""
import bpy, json, math, os, sys
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
items, S = job["items"], job.get("scale", 1.0)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
n = len(items); cols = max(1, math.ceil(math.sqrt(n * 1.8))); rows = math.ceil(n / cols)
PX = job.get("px", min(2600, 300 * cols))
CELL, LAB = 10.0, 2.2                      # cell size and label strip in scene units
cells = []
for i, (p, lab) in enumerate(items):
    bpy.ops.wm.stl_import('EXEC_DEFAULT', filepath=p); o = bpy.context.selected_objects[0]
    xs = [v[0] for v in o.bound_box]; ys = [v[1] for v in o.bound_box]; zs = [v[2] for v in o.bound_box]
    ext = max(max(xs) - min(xs), max(zs) - min(zs), 1e-6); k = CELL * 0.86 / ext
    c, r = i % cols, i // cols
    cx, base = (c + 0.5) * CELL, -(r + 1) * (CELL + LAB) + LAB + CELL * 0.07
    o.scale = (k, k, k); o.location = (cx - k * (min(xs) + max(xs)) / 2, -k * (min(ys) + max(ys)) / 2, base - k * min(zs))
    o.color = (0.82, 0.8, 0.74, 1)
    real = [S * (max(a) - min(a)) for a in (xs, ys, zs)]
    cells.append((cx, base - CELL * 0.07, "%d  %s  %.0fx%.0fx%.0f" % (i + 1, lab, *real)))
W, H = cols * CELL, rows * (CELL + LAB)
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'; sc.display.shading.show_cavity = True
sc.render.resolution_x = PX; sc.render.resolution_y = max(64, round(PX * H / W))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.sensor_fit = 'HORIZONTAL'; cam.data.ortho_scale = W; cam.data.clip_end = 5000
from mathutils import Euler
texts = {"front": [], "back": []}
if Image is None:                       # labels in the scene: one set facing each camera, white paper behind
    sc.render.film_transparent = False; sc.world = bpy.data.worlds.new("paper"); sc.world.color = (1, 1, 1)
    sc.view_settings.view_transform = 'Standard'
    for name, back in (("front", False), ("back", True)):
        for cx, ly, text in cells:
            cu = bpy.data.curves.new("label", 'FONT'); cu.body = text; cu.size = CELL / 17
            o = bpy.data.objects.new("label", cu); sc.collection.objects.link(o); o.color = (0.05, 0.05, 0.05, 1)
            o.rotation_euler = Euler((math.pi / 2, 0, math.pi if back else 0))
            o.location = (cx + CELL * (0.48 if back else -0.48), 0, ly - cu.size * 1.15); texts[name].append(o)
shots = []
for name, y, rot in (("front", -500, (math.pi / 2, 0, 0)), ("back", 500, (math.pi / 2, 0, math.pi))):
    cam.location = (W / 2, y, -H / 2); cam.rotation_euler = Euler(rot)
    for k, obs in texts.items():
        for o in obs: o.hide_render = k != name
    f = os.path.splitext(job["out"])[0] + "_" + name + ".png"; sc.render.filepath = f
    bpy.ops.render.render(write_still=True); shots.append((name, f))
if Image is None:
    print("sheet", ", ".join(f for _, f in shots)); sys.exit(0)
try: FONT = ImageFont.load_default(size=max(11, round(PX / cols / 18)))
except TypeError: FONT = None
ims = []
for name, f in shots:
    a = Image.open(f).convert("RGBA"); im = Image.new("RGB", a.size, (255, 255, 255)); im.paste(a, mask=a); d = ImageDraw.Draw(im); s = PX / W
    for cx, ly, text in cells:
        x = cx if name == "front" else W - cx          # the back view is mirrored left to right
        d.text(((x - CELL * 0.48) * s, -ly * s + 2), text, fill=(20, 20, 20), font=FONT)
    d.text((6, 4), "from %s (%s)" % ("-Y" if name == "front" else "+Y", name), fill=(160, 0, 0), font=FONT)
    ims.append(im); os.remove(f)
out = Image.new("RGB", (PX, sum(i.height for i in ims) + 8), (255, 255, 255)); y = 0
for im in ims: out.paste(im, (0, y)); y += im.height + 8
out.save(job["out"], quality=85)
print("sheet", job["out"], out.size)
