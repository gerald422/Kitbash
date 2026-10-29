exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
LEGS = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "30-Legs-3"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/{LEGS}.stl", "Legs")
V, Tr = T.mesh_np(legs); belt = T.bio_belt(legs, V)
pts = T._bio_side_shin_points(legs, V, Tr)
for side in ("R", "L"):
    plan = T.bio_plan(V, Tr, *pts[side])
    for sw in (0.0, 20.0, -20.0):
        a = {}
        Cb, n, H = T.bio_belt_cut(V, plan, belt, side, 0.0, auto=a, swing=sw)
        # band: hull points within 0.8 of the plane
        band = H[np.abs((H - Cb) @ n) < 0.05]
        e1 = np.cross(n, [0, 1.0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
        q = np.c_[(band - Cb) @ e1, (band - Cb) @ e2]
        # how much of the glue disc (r 2.42) lies inside the band's 2D hull
        from scipy.spatial import Delaunay
        hull = Delaunay(q)
        g = np.array([[r * np.cos(t), r * np.sin(t)] for r in (0.0, 0.8, 1.6, 2.4) for t in np.linspace(0, 2 * np.pi, 24, endpoint=False)])
        inside = (hull.find_simplex(g) >= 0).mean()
        cen = q.mean(0)
        print(f"{side} swing {sw:+.0f}: band {len(band)} pts, extent e1 {q[:,0].min():.2f}..{q[:,0].max():.2f} e2 {q[:,1].min():.2f}..{q[:,1].max():.2f}; band centre from glue {cen.round(2)}; disc on the face {inside:.0%}; auto {a.get('out_auto', 0):.2f} notch {'notch' in a}")
