"""1.6 end to end over the real files: shin anchors found on the legs, Mar Fil / Veteran Blade / Marta shin
pads from their folders' fits (lefts mirrored, Mirrored/LeftOrientated files used as they are), pauldrons from
Josh's example on arms whose Pad anchors are copied, arm swaps and pad swaps. Renders to out/."""
exec(open("/home/claude/test/v16/common16.py").read())
OUT = "/home/claude/test/v16/out"
ONLY = os.environ.get("ONLY", "shins pads").split()
def hide(*obs):
    for o in obs: o.hide_render = True; o.hide_set(True)
def rel(part, anchor):
    """part pose in its anchor's frame (scale-free)"""
    l, r, _ = anchor.matrix_world.decompose(); Aw = Matrix.LocRotScale(l, r, Vector((1, 1, 1)))
    l, r, _ = part.matrix_world.decompose(); Pw = Matrix.LocRotScale(l, r, Vector((1, 1, 1)))
    return Aw.inverted() @ Pw
def drop(pad, host, anchor):
    """how far the pad would move in along the anchor's Z to touch: + floats, - already in"""
    return T.settle_onto(pad, [host], anchor.matrix_world.to_3x3() @ Vector((0, 0, -1)), dry=True)
if "shins" in ONLY:
    SPL = json.load(open("/home/claude/blend/mf/icp/shin_place.json"))
    legs = {}
    for name, rel_, cur in (("29-Legs-2", f"{AM}/Legs/29-Legs-2.stl", (0, 0, 0)), ("35-Legs-2-A", f"{AM}/Legs(JumpPack)/35-Legs-2-A.stl", (60, 0, 0))):
        select(None); lg = send(rel_, "Legs", cur); legs[name] = lg
        ck(f"{name}: both Shin anchors found", sock(lg, "Shin R") is not None and sock(lg, "Shin L") is not None, T._state["last"])
    SETS = [  # (label, R file, L file, what the left should say)
        ("marfil", f"{AM}/ShinPads/68-ShinPad-1.stl", f"{AM}/ShinPads/71-ShinPad-4.stl", "mirrored for the left"),
        ("marfil_LO", f"{AM}/ShinPads/72-ShinPad-5.stl", f"{AM}/ShinPads/LeftOrientated/Mirrored-72-ShinPad-5.stl", ""),
        ("vbs", f"{VBS}/Shin-Pads/Shin-Pads-RawSTL/30-Shin-Pad-2.stl", f"{VBS}/Shin-Pads/Shin-Pads-Mirrored/30-Shin-Pad-2-Mirrored.stl", ""),
        ("vbs_flame", f"{VBS}/Shin-Pads/Shin-Pads-RawSTL/Right-ShinPad-Flame.stl", f"{VBS}/Shin-Pads/Shin-Pads-RawSTL/33-Shin-Pad-5.stl", "mirrored for the left"),
        ("marta", f"{MA}/Chin_pad_2_R.stl", f"{MA}/Chin_pad_2_L.stl", ""),
        ("marta6", f"{MA}/Chin_pad_6_R.stl", f"{MA}/Chin_pad_6_L_with_I.stl", ""),
    ]
    V3 = {"front": (0, 1, 0.12), "right": (1, 0.15, 0.08), "left": (-1, 0.15, 0.08)}
    placed = {}
    for label, fr, fl, lnote in SETS:
        print(f"\n== {label}")
        for lname, lg in legs.items():
            got = {}
            for side, f in (("R", fr), ("L", fl)):
                select(sock(lg, f"Shin {side}"))
                p = send(f, "Knee Pads", (120, 0, 0)); got[side] = p
                ok = p.get("ws_snap_sock_ref") == sock(lg, f"Shin {side}") if hasattr(p, "ws_snap_sock_ref") else False
                ck(f"{lname} {os.path.basename(f)} snapped on Shin {side}", T._co().snap_socket_of(p) == sock(lg, f"Shin {side}") if hasattr(T, "_co") else f"snapped to Shin {side}" in T._state["last"], T._state["last"])
                if side == "L" and lnote:
                    ck(f"   {lnote}", lnote in T._state["last"], T._state["last"])
                g = drop(p, lg, sock(lg, f"Shin {side}"))
                print(f"      seated: would move {g if g is None else round(g, 3)} to touch")
            placed[(label, lname)] = got
            rend.render(scene, OUT, f"shin_{label}_{lname.split('-')[0]}", [lg, got["R"], got["L"]], V3, [rend.GREY, rend.ORANGE, rend.BLUE])
            hide(got["R"], got["L"])
    # 68 on the right of 29-Legs-2 against the placement Josh signed off (offline)
    for lname in legs:
        p = placed[("marfil", lname)]["R"]; lg = legs[lname]
        want = np.array(SPL["frames"][f"{lname}|R"]) @ np.array(SPL["pads"]["68-ShinPad-1|R"]["F"]) @ np.array(SPL["pads"]["68-ShinPad-1|R"]["A"])
        have = A(lg.matrix_world.inverted() @ p.matrix_world)
        a = ang(have, want); d = np.linalg.norm(have[:3, 3] - want[:3, 3])
        ck(f"{lname}: 68 on the right sits where the approved one did (<0.6 deg, <0.2 mm)", a < 0.6 and d < 0.2, (round(a, 3), round(d, 3)))
if "pads" in ONLY:
    print("\n== pauldrons")
    torso, shR, shL = torso_both((200, 0, 0))
    arms = {}
    for side, n in (("R", "76-Arm-1-R-A"), ("L", "78-Arm-1-L-A")):
        select(torso); arms[side] = send(f"{AM}/Arms/{n}.stl", "Arms", (230, 0, 0))
        ck(f"{n} on Shoulder {side} with a Pad {side} anchor", sock(arms[side], f"Pad {side}") is not None and f"snapped to Shoulder {side}" in T._state["last"], T._state["last"])
    pads = {}
    for side in ("R", "L"):
        select(arms[side]); pads[side] = send(f"{AM}/ShoulderPads/62-ShoulderPad-1.stl", "Shoulder Pads", (260, 0, 0))
        ck(f"62 snapped on Pad {side}", f"snapped to Pad {side}" in T._state["last"], T._state["last"])
    D = np.load("/home/claude/blend/pp/pp.npz"); padmw = D["62-ShoulderPad-1_mw"]
    have = A(arms["R"].matrix_world.inverted() @ pads["R"].matrix_world)
    a = ang(have, padmw); d = np.linalg.norm(have[:3, 3] - padmw[:3, 3])
    ck(f"62 on arm 76 sits where Josh put it in his example (<0.3 deg, <0.05 mm)", a < 0.3 and d < 0.05, (round(a, 3), round(d, 3)))
    # left: the mirror image of the right, across the torso's middle
    Mt = torso.matrix_world @ MX @ torso.matrix_world.inverted()
    l, r, _ = pads["R"].matrix_world.decompose(); PR = Matrix.LocRotScale(l, r, Vector((1, 1, 1)))
    l, r, _ = pads["L"].matrix_world.decompose(); PL = Matrix.LocRotScale(l, r, Vector((1, 1, 1)))
    mirrorR = Mt @ PR @ MX            # the right pad's mesh mirrored = the left pad's mesh (mirrored copy)
    a = ang(PL, mirrorR); d = (PL.translation - mirrorR.translation).length
    ck(f"left pad is the right one mirrored (arm 78 is 76 mirrored to ~0.7 deg)", a < 1.5 and d < 0.15, (round(a, 3), round(d, 3)))
    V = {"front": (0, 1, 0.25), "right": (1, 0, 0.15), "top": (0.2, 0.6, 1.0)}
    COLS = [rend.GREY, rend.BLUE, rend.BLUE, rend.ORANGE, rend.ORANGE]
    rend.render(scene, OUT, "pads_76_62", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, COLS)
    for rn, ln in (("111-Arm-8-R-A", "113-Arm-8-L-A"), ("101-Arm-6-R-A", "103-Arm-6-L-A"), ("126-Arm-11-R-A", "128-Arm-11-L-A"), ("131-Arm-12-R-A", "133-Arm-12-L-A")):
        print(f"\n== swap arms for {rn.split('-')[0]}")
        for side, n in (("R", rn), ("L", ln)):
            select(arms[side]); a_ = send(f"{AM}/Arms/{n}.stl", "Arms", (300, 0, 0))
            s_ = sock(a_, f"Pad {side}")
            ck(f"{n}: Pad anchor copied, pad carried across", s_ is not None and T._co().snap_socket_of(pads[side]) == s_ if hasattr(T, "_co") else s_ is not None and "moved across" in T._state["last"], T._state["last"])
            arms[side] = a_
            g = drop(pads[side], a_, s_) if s_ is not None else None
            print(f"      {side}: pad would move {g if g is None else round(g, 3)} to touch the arm")
        rend.render(scene, OUT, f"pads_{rn.split('-')[0]}_62", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, COLS)
    for label, fr, fl in (("63", f"{AM}/ShoulderPads/63-ShoulderPad-2.stl", f"{AM}/ShoulderPads/63-ShoulderPad-2.stl"),
                          ("66", f"{AM}/ShoulderPads/66-ShoulderPad-5.stl", f"{AM}/ShoulderPads/67-ShoulderPad-6.stl"),
                          ("56", f"{VBS}/ShoulderPads/ShoulderPads-RawSTL/56-ShoulderPad-1.stl", f"{VBS}/ShoulderPads/ShoulderPads-Mirrored/57-ShoulderPad-2-Mirrored.stl"),
                          ("death", f"{VBS}/ShoulderPads/ShoulderPads-RawSTL/Death-ShoulderPad.stl", f"{VBS}/ShoulderPads/ShoulderPads-RawSTL/58-ShoulderPad-3.stl"),
                          ("tn", f"{TN}/Pauldron_Assault_1.stl", f"{TN}/Pauldron_Assault_2.stl")):
        print(f"\n== pad swap: {label}")
        for side, f in (("R", fr), ("L", fl)):
            select(pads[side]); q = send(f, "Shoulder Pads", (330, 0, 0))
            ck(f"{os.path.basename(f)} replaced the pad on Pad {side}", f"snapped to Pad {side}" in T._state["last"], T._state["last"])
            pads[side] = q
            g = drop(q, arms[side], sock(arms[side], f"Pad {side}"))
            print(f"      {side}: would move {g if g is None else round(g, 3)} to touch the arm")
        rend.render(scene, OUT, f"pads_131_{label}", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, COLS)
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
