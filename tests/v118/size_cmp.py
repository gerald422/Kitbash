exec(open("/home/claude/test/v17/common17.py").read())
sys.path.insert(0, "/home/claude/bionic")
prefs.bionic_dir = "/home/claude/test/v118/kit"
KIT = T.bionic_kit(prefs.bionic_dir)
# the kit: plug ball, glue face, thigh top
from geom import read_stl
V2, T2 = read_stl("/home/claude/test/v118/kit/LEG_HIGH.stl")
top = V2[V2[:, 2] > 9.801 - 2.5]
print(f"KIT plug ball dia {2 * 2.689:.2f}, glue face dia {2 * 2.42:.2f}; thigh top (2.5 mm under the cup centre) X {np.ptp(top[:, 0]):.2f} Y {np.ptp(top[:, 1]):.2f}; thigh overall X {np.ptp(V2[:, 0]):.2f} Y {np.ptp(V2[:, 1]):.2f}")
for i, rel in enumerate(sys.argv[sys.argv.index("--") + 1:]):
    select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (80 * i, 0, 0))
    select(torso); legs = send(f"{AM}/Legs/{rel}.stl", "Legs")
    s = float(legs.get("tiow_unit") or 1.0)
    V, Tr = T.mesh_np(legs); V = V / s
    belt = T.bio_belt(legs, V)
    pts = T._bio_side_shin_points(legs, V, Tr)
    for side in ("R", "L"):
        plan = T.bio_plan(V, Tr, *pts[side])
        ub = belt["up"]; lat = belt["lat"][side]; lat = lat - (lat @ ub) * ub; lat /= np.linalg.norm(lat)
        fw = np.cross(ub, lat); fw = fw if fw[1] > 0 else -fw
        # the old thigh's section at the trace's cut point and 1.5 mm below
        out = []
        for back in (0.0, 1.5):
            c = plan["C"] - back * plan["d"]
            loops = T.bio_slice(V, Tr, c, plan["d"], 9.0)
            # the loop round the centre
            best = None
            for L in loops:
                P = np.asarray(L[0]) if isinstance(L, (list, tuple)) else np.asarray(L)
                if P.ndim != 2: continue
                if best is None or np.linalg.norm(P.mean(0) - c) < np.linalg.norm(best.mean(0) - c): best = P
            if best is None: out.append("?"); continue
            dl = plan["d"]; la = lat - (lat @ dl) * dl; la /= np.linalg.norm(la); f2 = np.cross(dl, la); f2 = f2 if f2 @ fw > 0 else -f2
            out.append(f"{np.ptp(best @ la):.2f} wide x {np.ptp(best @ f2):.2f} deep")
        # the hip just under the belt: the leg's points 0.6-1.4 mm under the hip anchor, outside the codpiece line
        Pb = belt["hip"][side] - 0.6 * ub
        h = (V - Pb) @ ub
        rel_ = V - plan["C"]; al = rel_ @ plan["d"]; rad = np.linalg.norm(rel_ - np.outer(al, plan["d"]), axis=1)
        band = V[(h < 0) & (h > -0.8) & (rad < plan["ext"] + 1.8)]
        lw = band @ lat - belt["centre"] @ lat
        bs = band[lw > 0]
        print(f"{rel} {side}: thigh top {out[0]}; 1.5 mm lower {out[1]}; under the belt: leg from {lw[lw > 0].min():.2f} to {lw.max():.2f} mm out from the middle ({lw.max() - max(lw[lw > 0].min(), 0):.2f} wide), front-back {np.ptp(bs @ fw):.2f}")
    for o in [torso] + list(T._descendants(torso)):
        if o.name in bpy.data.objects: bpy.data.objects.remove(o)
