exec(open("/home/claude/test/variants/exp_touch2.py").read().split("OUT = ")[0])
OUT = "/home/claude/test/variants/proto/same"; os.makedirs(OUT, exist_ok=True)
touch = float(os.environ.get("TOUCH", "20"))
for side in ("R", "L"):
    sx = 1 if side == "R" else -1
    for nm, fam, pad in (("B", "marfilB", pB), ("M", "marta", pM[side])):
        byeye_shin(pad, legs29, a29[side], fam, touch=touch); byeye = pad.matrix_world.copy()
        rend.render(scene, OUT, f"{nm}_{side}_eye", [legs29, pad], {"out": (sx, 0.15, 0.05), "frontout": (sx, 1, 0.1)}, [rend.GREY, rend.ORANGE])
        rk, mv = auto(pad, legs29, a29[side], touch)
        Aw = unit(a29[side].matrix_world)
        e = (Aw.to_3x3().inverted() @ pad.matrix_world.to_3x3() @ byeye.to_3x3().inverted() @ Aw.to_3x3()).to_euler()
        print(f"   {nm} {side}: rock {rk:4.1f} (X {math.degrees(e.x):5.1f} Y {math.degrees(e.y):5.1f} Z {math.degrees(e.z):5.1f})")
        rend.render(scene, OUT, f"{nm}_{side}_rock", [legs29, pad], {"out": (sx, 0.15, 0.05), "frontout": (sx, 1, 0.1)}, [rend.GREY, rend.ORANGE])
        pad.matrix_world = Matrix.Translation((500, 0, 0))
