"""Pad fix (Nov 8) through TIOW Inbox 1.17.7, sent like the Squad Builder does (model + socket): torso, one arm, one pad.
Each pad must land where the new sidecars put it (torso Shoulder socket @ arm fit @ arm Pad socket @ pad fit), with
only TIOW's own settle on top; pictures of each model from outside its pad go to OUTDIR.
python t_pads.py -- WORKLIB TIOW_FILE OUTDIR"""
import bpy, json, os, sys, tempfile, math
import numpy as np
W, TIOW, OUTD = sys.argv[sys.argv.index("--") + 1:][:3]
sys.path.insert(0, "/home/claude/kitbash/tests"); import rend
M16 = lambda a: np.array(a, float).reshape(4, 4)
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
CH = "Mar Fil - Tacticus/Techmarine/Chests/MarFil Techmarine - Chest"
A7B = "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 7B R"
I1L = "Mar Fil - Tacticus/Intercessors-V2/Intercessors-Bits/Arms/MarFil Intercessor - Arm 1 L"
BB4 = "BBoosty - Heresy/Medusas Mortals/Arms/BBoosty Medusas Mortals - Arm 4 R"
MG = "Marta PunkGirl - Tacticus/GURLS/06.23 Greek Themed Gurls/Arms/Marta Gurls - Arms Set 2 Cloth 1 L"
TNF = "Turtle Ninja - Heresy/Mk7-8 Assault Intercessors Addon 1/Arms/TN Mk7-8 Assault - Mk7 Power Fist B1"
CBC = "CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Claw/Arms/CyberBrush Bug Hunters - Claw 1 (2)"
STUDS = "BBoosty - Heresy/Medusas Mortals/Stuff/Shoulder Pads/BBoosty Medusas Mortals - Shoulder Pad Studs"
BOLTS = "BBoosty - Heresy/Medusas Mortals/Stuff/Shoulder Pads/BBoosty Medusas Mortals - Shoulder Pad Bolts"
P62 = "Mar Fil - Tacticus/AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1"
MP2 = "Marta PunkGirl - Tacticus/GURLS/04.23 DA Lion Knights/Shoulder Pads/Marta Gurls - Shoulder Pad 2"
CASES = [("ex_R", A7B, "R", STUDS), ("ex_L", I1L, "L", BOLTS), ("bb_bolts", BB4, "R", BOLTS), ("bb_62", BB4, "R", P62),
         ("i1l_62", I1L, "L", P62), ("a7b_62", A7B, "R", P62), ("marta_62", MG, "R", P62), ("marta_pad", MG, "R", MP2),
         ("tn_62", TNF, "R", P62), ("cb_62", CBC, "R", P62), ("cb_studs", CBC, "R", STUDS)]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
ck("TIOW Inbox 1.17.7", T.bl_info["version"] == (1, 17, 7), T.bl_info["version"])
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); n = 0
def send(model, reqs, at):
    global n
    for p, cat, sock in reqs:
        r = {"schemaVersion": 1, "path": W + "/" + p + ".stl", "name": os.path.basename(p), "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": model}
        if sock: r["socket"] = sock
        else: r["at"] = at
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
def _side(arm):
    d = json.load(open(W + "/" + arm + ".sockets.json", encoding="utf-8-sig")); return "R" if "Shoulder R" in d.get("fits", {}) else "L"
CASES = [(m, arm, _side(arm), pad) for m, arm, side, pad in CASES]      # the arm's own side, whatever its name says
for i, (m, arm, side, pad) in enumerate(CASES):
    send(m, [(CH, "Chests", None), (arm, "Arms", "Shoulder " + side), (pad, "Shoulder Pads", "Pad " + side)], [70 * i, 0, 0])
sc = lambda rel: json.load(open(W + "/" + rel + ".sockets.json", encoding="utf-8-sig"))
def sk(d, t): return M16(next(s["matrix"] for s in d["sockets"] if s["type"] == t))
MX = np.diag([-1.0, 1, 1, 1])
def padfit(d, side):
    f = d["fits"].get("Pad " + side)
    return M16(f) if f is not None else MX @ M16(d["fits"]["Pad R"]) @ MX
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
seat62 = {}
for m, arm, side, pad in CASES:
    mine = {o.get("tiow_category"): o for o in obs if o.get("tiow_model") == m}
    ch, a, p = mine.get("Chests"), mine.get("Arms"), mine.get("Shoulder Pads")
    ck("%s: torso, arm and pad placed" % m, ch and a and p, list(mine))
    if not (ch and a and p): continue
    Mc = np.array(ch.matrix_world)
    exp = Mc @ sk(sc(CH), "Shoulder " + side) @ M16(sc(arm)["fits"]["Shoulder " + side]) @ sk(sc(arm), "Pad " + side) @ padfit(sc(pad), side)
    got = np.array(p.matrix_world)
    R = got[:3, :3] @ exp[:3, :3].T; da = math.degrees(math.acos(np.clip((np.trace(R) - 1) / 2, -1, 1))); dt = np.linalg.norm(got[:3, 3] - exp[:3, 3])
    ck("%s: pad where the new sidecars put it (%.2f deg, %.2f mm incl. settle)" % (m, da, dt), da < 0.5 and dt < 1.5, (da, dt))
    if pad == P62:   # Josh's 62 in the torso frame, right side
        S = np.linalg.inv(Mc) @ got
        seat62[m] = S if side == "R" else MX @ S @ MX
# Josh's 62 on each arm, as a picture check (raised arms carry their pad round with them, as on Mar Fil's own arms)
for k, S in seat62.items():
    R = S[:3, :3] @ seat62["a7b_62"][:3, :3].T
    print("   62 on %-9s vs on Assault Arm 7B R: %.0f deg (arm pose included)" % (k, math.degrees(math.acos(np.clip((np.trace(R) - 1) / 2, -1, 1)))))
# pictures: each model from outside its pad's shoulder
os.makedirs(OUTD, exist_ok=True)
sc_ = bpy.context.scene; cam = rend.setup(sc_, 420)
for m, arm, side, pad in CASES:
    ms = [o for o in obs if o.get("tiow_model") == m]
    cols = [{"Chests": rend.BLUE, "Arms": rend.GREY, "Shoulder Pads": rend.PURPLE}.get(o.get("tiow_category"), rend.GREY) for o in ms]
    sx = 1 if side == "R" else -1
    rend.render(sc_, OUTD, m, ms, {"out": (sx, 0.45, 0.3), "front": (0.25 * sx, 1, 0.2)}, cols)
print("FAILS:", fails if fails else "none")
