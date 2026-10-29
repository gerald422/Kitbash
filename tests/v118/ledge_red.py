exec(open("/home/claude/test/v17/common17.py").read())
import bmesh
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out8"
LEGS = sys.argv[sys.argv.index("--") + 1]; TAG = sys.argv[sys.argv.index("--") + 2]
rend.setup(scene, 600)
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
for side in ("R", "L"):
    T.bionic_build(legs, side, prefs, cut="belt")
vl.update()
st = json.loads(legs["tiow_bionic_state"])
reds = []
for side in ("R", "L"):
    pl = T.bio_parts(legs, side)["plug"]
    n_w = (pl.matrix_world.to_3x3() @ Vector(T.bio_kit_side(T.bionic_kit(prefs.bionic_dir), side)["plug"][1]["flat_n"])).normalized()
    me = pl.data.copy(); bm = bmesh.new(); bm.from_mesh(me); bm.transform(pl.matrix_world); bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.dot(n_w) < 0.99], context='FACES')
    # height of each remaining face along the axis from the ball's centre
    Bw = T.bio_parts(legs, side)["hip"].matrix_world.translation
    hs = [ (f.calc_center_median() - Bw).dot(n_w) for f in bm.faces ]
    print("REDH", side, "face heights:", sorted(set(round(h, 2) for h in hs)))
    if TAG.endswith("cap"):
        bmesh.ops.delete(bm, geom=[f for f, h in zip(list(bm.faces), hs) if h < 0.2], context='FACES')
    elif TAG.endswith("flat"):
        bmesh.ops.delete(bm, geom=[f for f, h in zip(list(bm.faces), hs) if h >= 0.2], context='FACES')
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(f"top {side}", me); scene.collection.objects.link(o)
    # lift it a hair so it wins the depth test against the plug's own top
    o.matrix_world = Matrix.Translation(n_w * 0.005); reds.append(o); print("REDOBJ", side, len(me.polygons), "faces; plug faces facing", sum(1 for f in pl.data.polygons if (pl.matrix_world.to_3x3() @ f.normal).normalized().dot(n_w) > 0.99))
obs = [legs] + [o for side in ("R", "L") for r, o in T.bio_parts(legs, side).items() if o.type == 'MESH' and not r.startswith('cut')] + reds
cols = [rend.GREY] + [rend.ORANGE if o.get("tiow_bionic_role") == "plug" else rend.BLUE for o in obs[1:-2]] + [(1, 0, 0, 1)] * 2
for o in scene.objects:
    if o.type == 'MESH': o.hide_render = o not in obs
    if o.type == 'EMPTY': o.hide_render = True
for o, c in zip(obs, cols): o.color = c
scene.display.shading.light = 'FLAT'
cam = scene.camera
u = Vector((0, 0, 1)); fw = (legs.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized(); rt = (legs.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
c0 = legs.matrix_world @ Vector((0, 0.5, 16.0))
import itertools
tot = 0
for i, (az, el) in enumerate(itertools.product(range(0, 360, 45), (0.15, -0.35))):
    a = math.radians(az); d = (fw * math.cos(a) + rt * math.sin(a) + u * el).normalized()
    y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
    cam.matrix_world = Matrix.LocRotScale(c0 + d * 200, Matrix((x, y, d)).transposed().to_quaternion(), None)
    cam.data.ortho_scale = 18
    f = f"{OUT}/red_{LEGS}_{TAG}_{i:02d}.png"; scene.render.filepath = f; bpy.ops.render.render(write_still=True)
    from PIL import Image
    im = np.asarray(Image.open(f).convert("RGB")).astype(int)
    red = int(((im[:, :, 0] > 200) & (im[:, :, 1] < 60) & (im[:, :, 2] < 60)).sum()); tot += red
    print(f"RED view az {az} el {el:+.2f}: {red} px")
print(f"RED total {LEGS} {TAG}: {tot}")
