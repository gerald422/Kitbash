exec(open("/home/claude/test/variants/exp_rock.py").read().split("for kind in")[0])
out = {}
def grab(tag, part, legs, anchor):
    Aw = unit(anchor.matrix_world); Ai = np.array(Aw.inverted())
    pv, pt = T._world_tris(part, deps); lv, lt = T._world_tris(legs, deps)
    out[tag + "_pv"] = pv @ Ai[:3, :3].T + Ai[:3, 3]; out[tag + "_pt"] = pt
    out[tag + "_lv"] = lv @ Ai[:3, :3].T + Ai[:3, 3]; out[tag + "_lt"] = lt
for side in ("R", "L"):
    byeye_shin(pB, legs29, a29[side], "marfilB", stage=0); grab(f"B{side}0", pB, legs29, a29[side])
    rk = rock(pB, legs29, a29[side], "mean"); grab(f"B{side}1", pB, legs29, a29[side]); print("B", side, rk)
    byeye_shin(pM[side], legs29, a29[side], "marta", stage=0); grab(f"M{side}0", pM[side], legs29, a29[side])
    rk = rock(pM[side], legs29, a29[side], "mean"); grab(f"M{side}1", pM[side], legs29, a29[side]); print("M", side, rk)
np.savez("/home/claude/test/variants/exp_slice.npz", **out)
