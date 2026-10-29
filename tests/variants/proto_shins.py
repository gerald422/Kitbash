exec(open("/home/claude/test/variants/common.py").read())
OUT = "/home/claude/test/variants/proto"; os.makedirs(OUT, exist_ok=True)
select(None)
legs = send(f"{MF}/Kit/Legs/29-Legs-2.stl", "Legs", (0, 0, 0))
an = shin_anchors(legs, "29-Legs-2")
LEGVIEWS = {"front": (0, 1, 0.12), "right": (1, 0, 0.08), "left": (-1, 0, 0.08)}
for fam, files in (("marfilB", {"R": f"{MF}/Kit B/Knee Pads/29-Shin-Pad-1.stl", "L": f"{MF}/Kit B/Knee Pads/29-Shin-Pad-1.stl"}),
                   ("marta", {"R": f"{MA}/Kit/ShinPads-RawSTL/Chin_pad_2_R.stl", "L": f"{MA}/Kit/ShinPads-RawSTL/Chin_pad_2_L.stl"})):
    pads = {}
    for side in ("R", "L"):
        select(an[side])
        p = send(files[side], "Knee Pads", (40, 0, 0))
        t = time.time(); byeye_shin(p, legs, an[side], fam, stage=int(os.environ.get('STAGE', '9'))); print(f"   by eye {fam} {side} {time.time()-t:.1f}s")
        pads[side] = p
    rend.render(scene, OUT, f"byeye_{fam}", [legs, pads["R"], pads["L"]], LEGVIEWS, [rend.GREY, rend.ORANGE, rend.BLUE])
    for side in ("R", "L"):
        sx = 1 if side == "R" else -1
        rend.render(scene, OUT, f"close{os.environ.get('STAGE', '')}_{fam}_{side}", [legs, pads[side]], {"front": (0.25 * sx, 1, 0.1), "out": (sx, 0.15, 0.05), "frontout": (sx, 1, 0.1)},
                    [rend.GREY, rend.ORANGE])
    for p in pads.values(): p.hide_render = True; p.hide_set(True)
