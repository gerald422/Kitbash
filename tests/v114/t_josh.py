"""Josh's example issues.blend sequence on the new Kitbash Library files."""
exec(open("/home/claude/test/v18/common18.py").read().replace('LIB = "/home/claude/test/kitlib"', 'LIB = "/mnt/user-data/uploads/d/Kitbash Library"'))
MF = "Mar Fil - Tacticus/"
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
select(None); c = send(MF + "ChaplainWithJumpPack/Chests/2-ChestChaplain.stl", "Bodies", (0, 0, 0))
print('chest children', [o.get('ws_type') for o in c.children])
lg = send(MF + "Intercessors-V2/Intercessors-Bits/Legs/26-Legs-10.stl", "Legs"); ck("legs on Waist", on(lg, "Waist"), T._state["last"])
select(c); h = send(MF + "ChaplainWithJumpPack/Heads/1-Head.stl", "Heads"); ck("head on Neck", on(h, "Neck"), T._state["last"])
select(c); a = send(MF + "Techmarine/Arms/18-Arm-4-R.stl", "Arms"); ck("arm on Shoulder R", on(a, "Shoulder R"), T._state["last"])
select(a); ax = send(MF + "Techmarine/Weapons/Melee/33-CogAxe-1.stl", "Melee"); ck("axe on Hand R", on(ax, "Hand R"), T._state["last"])
select(lg); pr = send(MF + "ChaplainOnBike-Bits/Chaplain/Knee Pads/5-ShinPad-R.stl", "Knee Pads"); ck("pad on Shin R", on(pr, "Shin R"), T._state["last"])
print('pad keys', list(pr.keys()))
select(lg); pl = send(MF + "ChaplainOnBike-Bits/Chaplain/Knee Pads/6-ShinPad-L.stl", "Knee Pads"); ck("pad on Shin L", on(pl, "Shin L"), T._state["last"])
print("FAILS", fails)
