exec(open("/home/claude/test/variants/exp_rock.py").read().split("for kind in")[0])
def settle(part, legs, anchor, touch, middle=4.0, rock=15.0):
    Aw = unit(anchor.matrix_world)
    rk = T.rock_settle(part, [legs], Aw, rock, middle=middle, touch=max(touch, 5.0)) if rock else 0.0
    mv = T.settle_onto(part, [legs], Aw.to_3x3() @ Vector((0, 0, -1)), sink=0.2,
                       band=(Aw.translation, Aw.to_3x3() @ Vector((1, 0, 0)), 0.5 * middle) if middle else None,
                       touch=touch, frame=Aw)
    return rk, mv
OUT = "/home/claude/test/variants/proto"
for touch in [float(t) for t in os.environ.get("TOUCH", "0 10 20").split()]:
    res = []
    for side in ("R", "L"):
        fit = unit(a29[side].matrix_world).inverted() @ legs29.matrix_world @ Matrix(CLICKS["29-Legs-2"][side]["seated"])
        p68.matrix_world = unit(a35[side].matrix_world) @ fit
        truth = legs35.matrix_world @ Matrix(CLICKS["35-Legs-2-A"][side]["seated"])
        e0 = ang(p68.matrix_world, truth)
        rk, mv = settle(p68, legs35, a35[side], touch)
        dpos = (p68.matrix_world.translation - truth.translation).length
        res.append(f"68@35{side}: {e0:4.1f}->{ang(p68.matrix_world, truth):4.1f}deg {dpos:4.2f}mm")
    print(f"touch {touch:4.0f}", " | ".join(res))
    if os.environ.get("RENDER"):
        for side in ("R", "L"):
            byeye_shin(pB, legs29, a29[side], "marfilB", stage=0); rk, mv = settle(pB, legs29, a29[side], touch)
            print(f"      B {side}: rock {rk:4.1f} slide {mv}")
            byeye_shin(pM[side], legs29, a29[side], "marta", stage=0); rk, mv = settle(pM[side], legs29, a29[side], touch)
            print(f"      Marta {side}: rock {rk:4.1f} slide {mv}")
            sx = 1 if side == "R" else -1
            for nm, pad in (("B", pB), ("M", pM[side])):
                rend.render(scene, OUT, f"t{int(touch)}_{nm}_{side}", [legs29, pad], {"out": (sx, 0.15, 0.05), "frontout": (sx, 1, 0.1)}, [rend.GREY, rend.ORANGE])
            pad = None
