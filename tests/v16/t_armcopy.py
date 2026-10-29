exec(open("/home/claude/test/v16/common16.py").read())
ref = json.load(open("/home/claude/real/arm_match5.json"))
for n in ("76-Arm-1-R-A", "78-Arm-1-L-A", "111-Arm-8-R-A", "113-Arm-8-L-A", "101-Arm-6-R-A", "126-Arm-11-R-A", "128-Arm-11-L-A", "131-Arm-12-R-A", "133-Arm-12-L-A"):
    select(None)
    arm = send(f"{AM}/Arms/{n}.stl", "Arms", (0, 0, 0))
    side = "L" if "-L-" in n else "R"
    s = sock(arm, f"Pad {side}")
    ck(f"{n}: Pad {side} anchor", s is not None, T._state["last"])
    if s is None: continue
    P = np.array(json.loads(s["tiow_points"]))
    d = np.linalg.norm(P - np.array(ref[n + ".stl"]["points"]), axis=1)
    ck(f"   points match the offline search (<0.25: they are projected onto the surface here)", d.max() < 0.25, np.round(d, 3))
    arm.hide_set(True); arm.hide_render = True
for n in ("36-Arm-1-A", "44-Arm-5-A"):
    select(None)
    arm = send(f"{VBS}/Arms/Arms-RawSTL/{n}.stl", "Arms", (0, 0, 0))
    ck(f"{n} (other kit): no anchor guessed", sock(arm, "Pad R") is None and "click its three points" in T._state["last"], T._state["last"])
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
