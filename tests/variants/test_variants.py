"""Variations: the other Mar Fil shin pads (29-32) and Marta's shin pads on the assault legs
(29-Legs-2 and the jump legs 35-Legs-2-A), both legs; pauldrons sitting down on the arm, both
arms, through arm swaps and pad swaps. Every stage goes through the real inbox; renders go to OUT."""
exec(open("/home/claude/test/variants/common.py").read())
OUT = "/home/claude/test/variants/out"; os.makedirs(OUT, exist_ok=True)
ONLY = os.environ.get("ONLY", "shins pads").split()

def far(ob):
    ob.hide_render = True; ob.hide_set(True)

# ------------------------------------------------------------------ shins
if "shins" in ONLY:
    select(None)
    legs29 = send(f"{MF}/Kit/Legs/29-Legs-2.stl", "Legs", (0, 0, 0)); a29 = shin_anchors(legs29, "29-Legs-2")
    legs35 = send(f"{MF}/Kit/Legs/35-Legs-2-A.stl", "Legs", (80, 0, 0)); a35 = shin_anchors(legs35, "35-Legs-2-A")
    FAMS = [
        ("marfilB", "Mar Fil 29-32", f"{MF}/Kit B/Knee Pads",
         {"R": "29-Shin-Pad-1", "L": "29-Shin-Pad-1"},                    # placed by eye, fit saved
         {"R": "30-Shin-Pad-2", "L": "31-Shin-Pad-3"},                    # then sent onto 29-Legs-2
         {"R": "32-Shin-Pad-4", "L": "30-Shin-Pad-2"}),                   # and onto the jump legs
        ("marta", "Marta", f"{MA}/Kit/ShinPads-RawSTL",
         {"R": "Chin_pad_2_R", "L": "Chin_pad_2_L"},
         {"R": "Chin_pad_3_R", "L": "Chin_pad_3_L"},
         {"R": "Chin_pad_1_R", "L": "Chin_pad_3_L"}),
    ]
    LEGVIEWS = {"front": (0, 1, 0.12), "right": (1, 0.15, 0.08), "left": (-1, 0.15, 0.08)}
    for fam, label, folder, first, on29, on35 in FAMS:
        print(f"\n== {label}: first pad from the folder placed by eye on 29-Legs-2, fit saved (both legs)")
        eye = {}
        for side in ("R", "L"):
            select(a29[side])
            p = send(f"{folder}/{first[side]}.stl", "Knee Pads", (40, 0, 0))
            ck(f"{first[side]} parked on Shin {side}", f"parked on Shin {side}" in T._state["last"], T._state["last"])
            byeye_shin(p, legs29, a29[side], fam, touch=20.0 if fam == "marfilB" else 10.0)
            T.save_folder_fit(p)
            eye[side] = p
        print(f"== {label}: the next pads from that folder, sent onto 29-Legs-2")
        got29 = {}
        for side in ("R", "L"):
            select(eye[side])
            q = send(f"{folder}/{on29[side]}.stl", "Knee Pads", (60, 0, 0))
            ck(f"{on29[side]} replaced the first pad on Shin {side}", q.ws_snap_sock_ref == a29[side], T._state["last"])
            got29[side] = q
        print(f"== {label}: same folder onto the jump legs (fit saved on 29-Legs-2)")
        got35 = {}
        for side in ("R", "L"):
            select(a35[side])
            q = send(f"{folder}/{on35[side]}.stl", "Knee Pads", (120, 0, 0))
            ck(f"{on35[side]} on the jump legs' Shin {side}", q.ws_snap_sock_ref == a35[side], T._state["last"])
            got35[side] = q
        rend.render(scene, OUT, f"{fam}_29", [legs29, got29["R"], got29["L"]], LEGVIEWS, [rend.GREY, rend.ORANGE, rend.BLUE])
        rend.render(scene, OUT, f"{fam}_35", [legs35, got35["R"], got35["L"]], LEGVIEWS, [rend.GREY, rend.ORANGE, rend.BLUE])
        for p in list(got29.values()) + list(got35.values()):
            far(p)

# ------------------------------------------------------------------ pauldrons
if "pads" in ONLY:
    print("\n== pauldrons: sit down on the arm, both arms")
    torso, shR, shL = torso_both((200, 0, 0))
    arms = {}
    for side in ("R", "L"):
        select(torso)
        arms[side] = send(f"{MF}/AssaultMarines-V2/Arms/111-Arm-8-{side}-A.stl", "Arms", (230, 0, 0))
        ck(f"arm 111 {side} has a Pad anchor", any(c.get("ws_type") == f"Pad {side}" for c in arms[side].children))
    pads = {}
    Tm = torso.matrix_world @ MX @ torso.matrix_world.inverted()
    for side, rel in (("R", "Shoulder Pads/56-ShoulderPad-1.stl"), ("L", "Shoulder Pads Mirrored/56-ShoulderPad-1-L.stl")):
        select(torso)
        p = send(f"{MF}/Kit/{rel}", "Shoulder Pads", (260, 0, 0))
        ck(f"first pad parked on Pad {side}", f"parked on Pad {side}" in T._state["last"], T._state["last"])
        if side == "R":
            byeye_pauldron(p, arms["R"], shR); PR = p.matrix_world.copy()
        else:
            p.matrix_world = Tm @ PR @ MX
        T.save_folder_fit(p)
        pads[side] = p
    def top_gap(pad, arm, side):
        """How far the pad would drop straight down (along the Pad anchor) before it touches the arm:
        above 0 it floats, below 0 the arm's shoulder is inside it."""
        A_ = sock(arm, f"Pad {side}").matrix_world
        return T.settle_onto(pad, [arm], A_.to_3x3() @ Vector((0, 0, -1)), dry=True)
    V = {"front": (0, 1, 0.25), "right": (1, 0, 0.15), "top": (0.2, 0.6, 1.0)}
    COLS = [rend.GREY, rend.BLUE, rend.BLUE, rend.ORANGE, rend.ORANGE]
    rend.render(scene, OUT, "pads_111", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, COLS)
    for arm_id in ("101-Arm-6", "126-Arm-11", "131-Arm-12"):
        print(f"\n== swap both arms for {arm_id}: the pads come across and sit on the new arm")
        for side in ("R", "L"):
            select(torso)
            a = send(f"{MF}/AssaultMarines-V2/Arms/{arm_id}-{side}-A.stl", "Arms", (300, 0, 0))
            ck(f"{arm_id} {side}: pad carried across", pads[side].ws_snap_sock_ref == sock(a, f"Pad {side}")
               and "moved across" in T._state["last"], T._state["last"])
            arms[side] = a
            g = top_gap(pads[side], a, side)
            print(f"      {side}: drop to touch the arm {g:.2f}, follows the arm {sock(a, f'Pad {side}').get('tiow_swing')} deg")
            ck(f"  {side}: pad isn't floating above the arm", g is not None and g < 0.3, g)
        rend.render(scene, OUT, f"pads_{arm_id.split('-')[0]}", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, COLS)
    print("\n== other pads from the same folders onto arm 131 (select the pad, send the new one)")
    for n_r, n_l in (("57-ShoulderPad-2", "57-ShoulderPad-2-L"), ("58-ShoulderPad-3", None)):
        for side, nm, folder in (("R", n_r, "Shoulder Pads"), ("L", n_l, "Shoulder Pads Mirrored")):
            if nm is None:
                continue
            select(pads[side])
            q = send(f"{MF}/Kit/{folder}/{nm}.stl", "Shoulder Pads", (330, 0, 0))
            ck(f"{nm} replaced the pad on Pad {side}", q.ws_snap_sock_ref == sock(arms[side], f"Pad {side}"), T._state["last"])
            pads[side] = q
        rend.render(scene, OUT, f"pads_131_{n_r.split('-')[0]}", [torso, arms["R"], arms["L"], pads["R"], pads["L"]], V, COLS)

print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
