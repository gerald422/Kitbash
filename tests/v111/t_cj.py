"""Chaplain with Jump Pack through the inbox: the four poses, each built on the chest (root): seated legs + its rock,
its posed arms, head, jump pack + exhaust, pads, belt bits on the legs' anchors; pose A with the crozius and pistol."""
exec(open("/home/claude/test/v18/common18.py").read())
OUT = "/home/claude/test/v111/out"; os.makedirs(OUT, exist_ok=True)
K = "All Mar All the time/ChaplainWithJumpPack (1)/ChaplainWithJumpPack"
PO = json.load(open("/home/claude/kits/cj/pose.json"))
PAR = json.load(open("/home/claude/kits/cj/cj_partial.json"))["side"]
def fitM(rel, t): return M16(PAR[rel]["fits"][t])
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") == want
def put(host, rel, cat, want, label):
    select(host); p = send(f"{K}/{rel}", cat); ck(f"{label}: on {want}", on(p, want), T._state["last"]); return p
def rel_to(label, part, host, M, what, deg=0.05, mm=0.02):
    got = A(frame(host).inverted() @ frame(part)); ck(f"{label}: {what}", close(got, M, deg, mm), f"{ang(got, M):.2f} deg {np.linalg.norm(got[:3,3]-M[:3,3]):.3f} mm")
    return got
TOR = {s['type']: M16(s['matrix']) for s in PAR["ChaplainWithJumpPack (1)/ChaplainWithJumpPack/Chest/Chest-Raw-STL/2-ChestChaplain.stl"]["sockets"]}
ARMS = {'A': ('13-Arm-Right-A', '17-Arm-Left-A'), 'B': ('14-Arm-Right-B', '18-Arm-Left-B'), 'C': ('15-Arm-Right-C', '19-Arm-Left-C'), 'D': ('16-Arm-Right-D', '20-Arm-Left-D')}
ROCK = {'A': '29-Rock-A', 'B': '28-Rock-B', 'C': '27-Rock-C', 'D': '30-Rock-D'}
KR = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
marines = []
for i, X in enumerate("ABCD"):
    lab = "cj" + X
    select(None); t = send(f"{K}/Chest/Chest-Raw-STL/2-ChestChaplain.stl", "Bodies", (70 * i, 0, 0))
    ck(f"{lab}: chest has its sockets", all(sock(t, k) for k in ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist")))
    legs = os.path.basename(PO[X]["legs"])
    lg = put(t, f"Legs/Legs-Raw-STL/{legs}", "Bodies", "Waist", f"{lab} legs")
    rel_to(f"{lab} legs", lg, t, M16(PO[X]["M_josh"]), "seated like Josh's AM legs")
    ck(f"{lab} legs: hips + belt anchors", all(sock(lg, k) for k in ("Hip R", "Hip L", "Belt Front", "Belt Back")), [c.get("ws_type") for c in lg.children])
    rk = put(lg, f"Rocks/Rocks-Raw-STL/{ROCK[X]}.stl", "Bases", "Base", f"{lab} rock"); rel_to(f"{lab} rock", rk, lg, np.eye(4), "under the legs as exported")
    arms = {}
    for sd, nm in zip("RL", ARMS[X]):
        rel = f"Arms/Arms-Raw-STL/{nm}.stl"
        a = put(t, rel, "Arms", f"Shoulder {sd}", f"{lab} arm {sd}"); arms[sd] = a
        got = rel_to(f"{lab} arm {sd}", a, t, TOR[f"Shoulder {sd}"] @ fitM(KR + rel, f"Shoulder {sd}"), "posed as its pair")
        # against Mar Fil's own arrangement (torso pose from the discs)
        mf = np.linalg.inv(M16(PO[X]["P"]))
        print(f"      {lab} arm {sd} vs Mar Fil's export: {ang(got, mf):.3f} deg {np.linalg.norm(got[:3,3]-mf[:3,3]):.3f} mm")
        ck(f"{lab} arm {sd}: has its Hand socket", sock(a, f"Hand {sd}") is not None)
    hd = put(t, "Head/Head-Raw-STL/1-Head.stl", "Heads", "Neck", f"{lab} head"); rel_to(f"{lab} head", hd, t, TOR["Neck"] @ fitM(KR + "Head/Head-Raw-STL/1-Head.stl", "Neck"), "on the AM helmet neck seat")
    jp = put(t, "Jumppack/Jumppack-Raw-STL/11-Jumppack.stl", "Backpacks", "Back", f"{lab} jump pack"); rel_to(f"{lab} jump pack", jp, t, np.eye(4), "as exported on the chest")
    ex = put(jp, "Jumppack/Jumppack-Raw-STL/12-Exhaust.stl", "Backpacks", "Back Top", f"{lab} exhaust"); rel_to(f"{lab} exhaust", ex, t, np.eye(4), "as exported on the chest")
    put(arms["R"], "ShoulderPads/ShoulderPads-Raw-STL/7-ShoulderPad-Right.stl", "Shoulder Pads", "Pad R", f"{lab} pauldron R")
    put(arms["L"], "ShoulderPads/ShoulderPads-Raw-STL/8-ShoulderPad-Left.stl", "Shoulder Pads", "Pad L", f"{lab} pauldron L")
    for sd, nm in (("R", "9-ShinPad-Right"), ("L", "10-ShinPad-Left")):
        s_ = sock(lg, f"Shin {sd}"); ck(f"{lab} legs: Shin {sd} anchor found", s_ is not None)
        if s_ is not None:
            select(s_); p = send(f"{K}/ShinPads/ShinPads-Raw-STL/{nm}.stl", "Knee Pads"); ck(f"{lab} shin pad {sd}", on(p, f"Shin {sd}"), T._state["last"])
    for a_ in ("23-Book", "24-Badge", "25-Holster", "26-Grenade"):
        select(lg); p = send(f"{K}/Accesories/Accesories-Raw-STL/{a_}.stl", "Accessories")
        ok = p is not None and p.parent is not None and str(p.parent.get("tiow_holds", "")) == a_
        ck(f"{lab} {a_}: on the anchor at Mar Fil's spot", ok, T._state["last"])
        if ok: rel_to(f"{lab} {a_}", p, lg, M16(PO[X]["P"]), "exactly where Mar Fil put it")
    if X == "D":
        select(lg); p = send(f"{K}/Accesories/Accesories-Raw-STL/23-Book.stl", "Accessories")
        ck(f"{lab} second book: on the free Hip R, settled", p is not None and p.parent is not None and p.parent.get("ws_type") == "Hip R" and "settled" in T._state["last"], T._state["last"])
    if X == "A":
        put(arms["R"], "Weapons/Weapons-Raw-STL/22-Crozius.stl", "Weapons", "Hand R", f"{lab} crozius")
        put(arms["L"], "Weapons/Weapons-Raw-STL/21-AbsolvorPistol.stl", "Weapons", "Hand L", f"{lab} absolvor pistol")
    marines.append((lab, t))
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05), "back": (-0.4, -1, 0.25)}
for nm, root in marines:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    cols = [rend.ORANGE if str(o.get("tiow_category", "")) in ("Shoulder Pads", "Knee Pads", "Accessories", "Grenades") else
            rend.BLUE if str(o.get("tiow_category", "")) in ("Melee", "Pistols", "Backpack Toppers", "Jump Packs") else rend.GREY for o in obs]
    rend.render(scene, OUT, nm, obs, V, cols)
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/cj_test.blend")
print("\nFAILS:", fails)
