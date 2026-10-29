"""Shin anchors found on import: same frames as the numpy run of the same finder, and within the approved
offline frames' spread."""
exec(open("/home/claude/test/v16/common16.py").read())
P = json.load(open("/home/claude/blend/mf/icp/shin_place.json")); NP = json.load(open("/home/claude/test/v16/shin_np.json"))
for legsname, rel_, x in (("29-Legs-2", f"{AM}/Legs/29-Legs-2.stl", 0), ("35-Legs-2-A", f"{AM}/Legs(JumpPack)/35-Legs-2-A.stl", 80)):
    select(None)
    t = time.time(); legs = send(rel_, "Legs", (x, 0, 0)); dt = time.time() - t
    ck(f"{legsname}: found on import in {dt:.1f}s", "Shin anchors found" in T._state["last"], T._state["last"])
    for side in ("R", "L"):
        s = sock(legs, f"Shin {side}")
        ck(f"{legsname}: Shin {side} found", s is not None)
        if s is None: continue
        An = A(legs.matrix_world.inverted() @ s.matrix_world)
        N = np.array(NP[legsname][side]); d = np.linalg.norm(An[:3, 3] - N[:3, 3])
        ck(f"  same as the numpy run (<0.02 deg, <0.002)", ang(N, An) < 0.02 and d < 0.002, (ang(N, An), d))
        S = np.array(P["frames"][f"{legsname}|{side}"]); d = np.linalg.norm(An[:3, 3] - S[:3, 3])
        ck(f"  near the offline frame Josh's renders used (<0.6 deg, <0.3)", ang(S, An) < 0.6 and d < 0.3, (round(ang(S, An), 3), round(d, 3)))
    # Find Shin Anchors on the selected legs redoes it
    select(legs); r = bpy.ops.tiow.find_shins()
    ck(f"{legsname}: Find Shin Anchors redoes them", r == {'FINISHED'} and sock(legs, "Shin R") is not None and sock(legs, "Shin L") is not None, r)
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
