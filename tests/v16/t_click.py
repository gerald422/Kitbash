"""Clicking a Pad anchor on a snapped arm gives the same frame as the copy made on import (the side-based
rule and the forward rule agree), and a clicked arm becomes the reference for its folder."""
exec(open("/home/claude/test/v16/common16.py").read())
torso, shR, shL = torso_both((200, 0, 0))
for side, n in (("R", "76-Arm-1-R-A"), ("L", "78-Arm-1-L-A")):
    select(torso); arm = send(f"{AM}/Arms/{n}.stl", "Arms", (230, 0, 0))
    s = sock(arm, f"Pad {side}"); Mc = A(arm.matrix_world.inverted() @ s.matrix_world)
    pts = [arm.matrix_world @ Vector(p) for p in json.loads(s["tiow_points"])]
    nrm = [Vector((0, 0, 1))] * 3
    s2 = T.make_anchor(arm, f"Pad {side}", pts, nrm, kind="clicked")
    Mk = A(arm.matrix_world.inverted() @ s2.matrix_world)
    ck(f"{n}: clicked on the model = copied on arrival ({T._outward_of(arm, pts[2]) is not None and 'side rule' or 'forward rule'})",
       ang(Mc, Mk) < 0.01 and np.linalg.norm(Mc[:3, 3] - Mk[:3, 3]) < 1e-4, (ang(Mc, Mk), Mc[:3, 3] - Mk[:3, 3]))
    if side == "R":
        path = T.remember_anchor(arm, s2)
        d = json.load(open(path))
        ck("clicked anchor saved beside the arm with its points", any(x.get("type") == "Pad R" and len(x.get("points", [])) == 3
           and x["props"]["tiow_anchor"] == "clicked" for x in d["sockets"]), d["sockets"])
select(None)
a111 = send(f"{AM}/Arms/111-Arm-8-R-A.stl", "Arms", (300, 0, 0))
refs = [r[0] for r in T._pad_references(a111, "R")]
ck("the clicked 76 is the first reference for 111, the built-in after it", refs[:1] == ["76-Arm-1-R-A"] and len(refs) == 2, refs)
ck("111 got its Pad R anchor", sock(a111, "Pad R") is not None, T._state["last"])
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
