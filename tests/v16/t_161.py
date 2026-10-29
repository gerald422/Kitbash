"""1.6.1: the Chaplain pads as TIOW sends them ('Shin Pads'), a saved click on one side, Find Shin Anchors resetting."""
exec(open("/home/claude/test/v16/common16.py").read())
CHP = "All Mar All the time/ChaplainOnBike-Bits/ChaplainOnBike-Bits/RawSTL/ChaplainRawSTL"
ck("version 1.6.1", T.bl_info["version"] == (1, 6, 1))
select(None); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs", (0, 0, 0))
ck("legs: 'Shin anchors found' on the status line", "Shin anchors found" in T._state["last"], T._state["last"])
sR, sL = sock(legs, "Shin R"), sock(legs, "Shin L")
ck("anchors are drawn in front, bigger", sR.show_in_front and sR.empty_display_size > 2.0, (sR.show_in_front, sR.empty_display_size))
autoR = A(legs.matrix_world.inverted() @ sR.matrix_world)
select(legs); pR = send(f"{CHP}/5-ShinPad-R.stl", "Shin Pads", (40, 0, 0))
ck("5-ShinPad-R sent as 'Shin Pads' snaps onto Shin R", "snapped to Shin R" in T._state["last"], T._state["last"])
select(legs); pL = send(f"{CHP}/6-ShinPad-L.stl", "Shin Pads", (60, 0, 0))
ck("6-ShinPad-L goes on Shin L as it is", "snapped to Shin L" in T._state["last"] and "mirrored" not in T._state["last"], T._state["last"])
# placement = the Chaplain rig's, carried by the anchors: R and L mirror each other through the anchors
fr = A(sR.matrix_world.inverted() @ pR.matrix_world); fl = A(sL.matrix_world.inverted() @ pL.matrix_world)
MXn = np.diag([-1.0, 1, 1, 1]); mir = MXn @ fr @ MXn
print("      left vs right mirrored (pad files differ slightly): %.2f deg" % ang(fl, mir))
rend.render(scene, "/home/claude/test/v16/out", "chaplain_29", [legs, pR, pL], {"front": (0, 1, 0.12), "right": (1, 0.15, 0.08), "left": (-1, 0.15, 0.08)}, [rend.GREY, rend.ORANGE, rend.BLUE])
# a click saved for Shin R: next import keeps it and still finds Shin L
pts = [legs.matrix_world @ Vector(p) for p in ([1.85, 3.40, 3.91], [8.25, 2.72, 4.41], [4.61, 5.62, 10.23])]
c = T.make_anchor(legs, "Shin R", pts, [Vector((0, 0, 1))] * 3, kind="clicked"); T.remember_anchor(legs, c)
select(None); legs2 = send(f"{AM}/Legs/29-Legs-2.stl", "Legs", (100, 0, 0))
k2 = sock(legs2, "Shin R"); l2 = sock(legs2, "Shin L")
ck("with a saved Shin R click: Shin R is the click, Shin L still found", k2 is not None and k2.get("tiow_anchor") == "clicked" and l2 is not None and l2.get("tiow_anchor") == "auto", (T._state["last"], k2 and k2.get("tiow_anchor"), l2))
select(legs2); r = bpy.ops.tiow.find_shins()
k3 = sock(legs2, "Shin R")
d = json.load(open(os.path.join(LIB, AM, "Legs/29-Legs-2.sockets.json")))
ck("Find Shin Anchors puts the automatic ones back and forgets the saved click", r == {'FINISHED'} and k3.get("tiow_anchor") == "auto"
   and ang(A(legs2.matrix_world.inverted() @ k3.matrix_world), autoR) < 0.01 and not any(s.get("type") == "Shin R" for s in d["sockets"]), (r, k3.get("tiow_anchor"), d["sockets"]))
os.remove(os.path.join(LIB, AM, "Legs/29-Legs-2.sockets.json"))
select(None); cl = send(f"{CHP}/3-Legs.stl", "Legs", (150, 0, 0))
print("      Chaplain's own 3-Legs:", T._state["last"])
print(f"\n{len(fails)} failure(s)"); sys.exit(1 if fails else 0)
