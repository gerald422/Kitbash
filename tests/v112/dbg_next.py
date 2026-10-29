exec(open("/home/claude/test/v18/common18.py").read())
prefs.adaptor_dir = os.path.join(LIB, "body adaptor"); prefs.adaptor_default = 3
AMT = f"{AM}/Chest/22-Torso-1.stl"
TNL = "Turtle Ninja/TurtleNinja's Mk2-6 Builder/Mk6/Legs/Lower A 1.stl"
select(None); t = send(AMT, "Bodies", (0, 0, 0)); legs = send(TNL, "Legs")
ad = [o for o in vl.objects if o is not None and o.get("tiow_category") == "Adapters"][0]
fw = sock(ad, "Flat Waist"); print("parent mode", scene.ws_parent_mode, "legs parent", legs.parent.name, "ad parent", ad.parent and ad.parent.name)
w0 = A(frame(legs)); print("before: legs", np.round(w0[:3, 3], 3), "ad", np.round(A(ad.matrix_world)[:3, 3], 3), "fw", np.round(A(fw.matrix_world)[:3, 3], 3))
scene.cursor.location = (100, 0, 0)
msg = T.next_adaptor(legs, prefs); print(msg)
ad2 = [o for o in vl.objects if o is not None and o.get("tiow_category") == "Adapters"][0]; fw2 = sock(ad2, "Flat Waist")
vl.update()
print("after: legs", np.round(A(frame(legs))[:3, 3], 3), "ad2", np.round(A(ad2.matrix_world)[:3, 3], 3), "fw2", np.round(A(fw2.matrix_world)[:3, 3], 3), "legs parent", legs.parent.name)
