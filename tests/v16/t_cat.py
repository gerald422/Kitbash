"""Categories as TIOW will actually send them: Marta's chin pads arrive as 'Legs' (their folder), TIOW's own
'Shin Pads' name, jump legs found by file name."""
exec(open("/home/claude/test/v16/common16.py").read())
select(None); legs = send(f"{AM}/Legs(JumpPack)/35-Legs-2-A.stl", "Legs", (0, 0, 0))
ck("jump legs: shin anchors found", "Shin anchors found" in T._state["last"], T._state["last"])
select(legs); p = send(f"{MA}/Chin_pad_2_R.stl", "Legs", (40, 0, 0))
ck("Chin_pad_2_R sent as 'Legs' snaps onto Shin R", "snapped to Shin R" in T._state["last"] and p.users_collection[0].name == "Knee Pads", (T._state["last"], p.users_collection[0].name))
select(legs); p = send(f"{AM}/ShinPads/70-ShinPad-3.stl", "Shin Pads", (60, 0, 0))
ck("TIOW's 'Shin Pads' name works (goes on the free left, mirrored)", "snapped to Shin L" in T._state["last"] and "mirrored" in T._state["last"], T._state["last"])
select(None); arm = send(f"{AM}/Arms/76-Arm-1-R-A.stl", "Arms", (100, 0, 0))
select(arm); p = send(f"{TN}/Pauldron_Assault_1.stl", "Unclassified", (120, 0, 0))
ck("a pauldron sent as 'Unclassified' still snaps", "snapped to Pad R" in T._state["last"], T._state["last"])
print(f"\n{len(fails)} failure(s)"); sys.exit(1 if fails else 0)
