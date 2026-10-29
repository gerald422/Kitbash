exec(open("/home/claude/test/variants/exp_rock.py").read().split("for kind in")[0])
def slide(part, legs, anchor, touch, middle=float(os.environ.get("MIDDLE", "4")) or None):
    Aw = unit(anchor.matrix_world)
    return T.settle_onto(part, [legs], Aw.to_3x3() @ Vector((0, 0, -1)), sink=0.2,
                         band=(Aw.translation, Aw.to_3x3() @ Vector((1, 0, 0)), 0.5 * middle) if middle else None, touch=touch, frame=Aw)
def auto(part, legs, anchor, touch, middle=float(os.environ.get("MIDDLE", "4")) or None):
    Aw = unit(anchor.matrix_world)
    rk = T.rock_settle(part, [legs], Aw, 15.0, middle=middle)
    return rk, slide(part, legs, anchor, touch, middle)
OUT = "/home/claude/test/variants/proto"
touch = float(os.environ.get("TOUCH", "10"))
res = []
for side in ("R", "L"):
    fit = unit(a29[side].matrix_world).inverted() @ legs29.matrix_world @ Matrix(CLICKS["29-Legs-2"][side]["seated"])
    p68.matrix_world = unit(a35[side].matrix_world) @ fit
    truth = legs35.matrix_world @ Matrix(CLICKS["35-Legs-2-A"][side]["seated"])
    e0 = ang(p68.matrix_world, truth); rk, mv = auto(p68, legs35, a35[side], touch)
    res.append(f"68@35{side}: {e0:4.1f}->{ang(p68.matrix_world, truth):4.1f}deg {(p68.matrix_world.translation - truth.translation).length:4.2f}mm")
    # same legs: the saved seated pose should stay put
    p68.matrix_world = legs29.matrix_world @ Matrix(CLICKS["29-Legs-2"][side]["seated"]); keep = p68.matrix_world.copy()
    rk, mv = auto(p68, legs29, a29[side], touch)
    res.append(f"68@29{side} stays: {ang(p68.matrix_world, keep):4.1f}deg {(p68.matrix_world.translation - keep.translation).length:4.2f}mm")
print(f"touch {touch:3.0f} Z {os.environ.get('TIOW_ROCK_Z', '0.333')} mid {os.environ.get('MIDDLE', '4')}", " | ".join(res))
if os.environ.get("RENDER"):
    for side in ("R", "L"):
        sx = 1 if side == "R" else -1
        for nm, fam, pad in (("B", "marfilB", pB), ("M", "marta", pM[side])):
            mv = byeye_shin(pad, legs29, a29[side], fam, touch=touch)
            byeye = pad.matrix_world.copy(); fit = unit(a29[side].matrix_world).inverted() @ byeye
            rk, mv2 = auto(pad, legs29, a29[side], touch)
            print(f"      {nm} {side}: by-eye slide {mv:5.2f}; auto on same legs moves it {ang(pad.matrix_world, byeye):4.1f}deg {(pad.matrix_world.translation - byeye.translation).length:4.2f}mm")
            pad.matrix_world = byeye
            rend.render(scene, OUT, f"u_{nm}_{side}_29", [legs29, pad], {"out": (sx, 0.15, 0.05), "frontout": (sx, 1, 0.1)}, [rend.GREY, rend.ORANGE])
            pad.matrix_world = unit(a35[side].matrix_world) @ fit
            rk, mv2 = auto(pad, legs35, a35[side], touch)
            print(f"      {nm} {side} on 35: rock {rk:4.1f} slide {mv2}")
            rend.render(scene, OUT, f"u_{nm}_{side}_35", [legs35, pad], {"out": (sx, 0.15, 0.05), "frontout": (sx, 1, 0.1)}, [rend.GREY, rend.ORANGE])
            pad.matrix_world = Matrix.Translation((500, 0, 0))
