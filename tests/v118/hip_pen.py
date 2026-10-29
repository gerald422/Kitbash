exec(open("/home/claude/test/v17/common17.py").read())
from mathutils.bvhtree import BVHTree
prefs.bionic_dir = "/home/claude/test/v118/kit"
LEGS = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "29-Legs-2"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
for side in ("R", "L"):
    print(side, T.bionic_build(legs, side, prefs, cut="belt"))
vl.update()
dg = bpy.context.evaluated_depsgraph_get()
t0 = time.time(); tl = BVHTree.FromObject(legs, dg); print("legs tree %.2fs" % (time.time() - t0))
inv = legs.matrix_world.inverted()
st = json.loads(legs["tiow_bionic_state"])
for side in ("R", "L"):
    P = T.bio_parts(legs, side)
    ball = inv @ P["hip"].matrix_world.translation
    for role in ("thigh", "plug", "shin", "foot"):
        ob = P[role]; M = inv @ ob.matrix_world
        t0 = time.time()
        deep, n, tot, where = 0.0, 0, 0, []
        for v in list(ob.data.vertices)[::2]:
            p = M @ v.co; tot += 1
            loc, nr, i, dist = tl.find_nearest(p)
            if loc is not None and (p - loc).dot(nr) < -1e-4:
                n += 1
                if dist > deep: deep, where = dist, (p - ball, nr)
        print(f"{side} {role}: {n}/{tot} vertices inside the legs, deepest {deep:.2f} mm" + (f" at {tuple(round(x, 2) for x in where[0])} from the ball, push {tuple(round(x, 2) for x in where[1])}" if n else "") + f" ({time.time() - t0:.1f}s)")
    lat = np.array(st[side]["C"]) - np.array(st["L" if side == "R" else "R"]["C"]); print("  ball->other ball", lat.round(2))
