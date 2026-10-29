"""Save Correction (TIOW Inbox 1.17.2): fix the part / fix the socket, this file or
the whole folder, both sides mirrored; saved corrections come back on the next send."""
import bpy, json, math, os, shutil, sys, tempfile
import numpy as np
from mathutils import Matrix, Vector
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
SRC = "/mnt/user-data/uploads/d/Kitbash Library/"
LIB = tempfile.mkdtemp() + "/lib/"
parts = {"torso": "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 3",
         "legs": "Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A",
         "armR": "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 6B R",
         "armL": "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 6B L",
         "head": "Mar Fil - Tacticus/AssaultMarines-V2/Helmet-Heads/Heads/MarFil Assault - Helmet 1",
         "sword": "Mar Fil - Tacticus/AssaultMarines-V2/Melee/MarFil Assault - Chain Sword 1 R",
         "pad": "Mar Fil - Tacticus/AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 5"}
for k, rel in parts.items():
    os.makedirs(os.path.dirname(LIB + rel), exist_ok=True)
    for ext in (".stl", ".sockets.json"):
        shutil.copy(SRC + rel + ext, LIB + rel + ext)
# a sibling in the sword's folder, to test Whole Folder
sib = parts["sword"].replace("Chain Sword 1 R", "Chain Sword 9 R")
shutil.copy(LIB + parts["sword"] + ".stl", LIB + sib + ".stl"); shutil.copy(LIB + parts["sword"] + ".sockets.json", LIB + sib + ".sockets.json")
def sc(rel): return json.load(open(LIB + rel + ".sockets.json"))
def M16(a): return np.array(a, float).reshape(4, 4)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_117x/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp(); prefs.builder_inbox = ""
vl = bpy.context.view_layer
def send(model, key, cat, socket=None, at=None):
    job = {"path": LIB + parts[key] + ".stl", "category": cat, "name": os.path.basename(parts[key]), "model": model}
    if socket: job["socket"] = socket
    if at: job["at"] = at
    new = T.import_request(job, prefs)
    return next(o for o in new if o.type == 'MESH')
def build(model, x):
    o = {}
    o["torso"] = send(model, "torso", "Chests", at=[x, 0, 0])
    o["legs"] = send(model, "legs", "Legs", socket="Waist")
    o["armR"] = send(model, "armR", "Arms", socket="Shoulder R")
    o["armL"] = send(model, "armL", "Arms", socket="Shoulder L")
    o["head"] = send(model, "head", "Heads", socket="Neck")
    o["sword"] = send(model, "sword", "Melee", socket="Hand R")
    o["padR"] = send(model, "pad", "Shoulder Pads", socket="Pad R")
    o["padL"] = send(model, "pad", "Shoulder Pads", socket="Pad L")
    vl.update()
    return o
A = build("mA", 0)
B = build("mB", -80)
ps = T._part_sockets(); sk, co = ps
def sockof(o): return T._snap_of(o)
ck("both models built, sword on Hand R", sockof(A["sword"])[1] == "Hand R" and sockof(B["sword"])[1] == "Hand R")
W = lambda o: np.array(o.matrix_world)

# ---- 1. Fix the Part: nudge the sword in its hand
s, t, g = sockof(A["sword"])
D = Matrix.Translation((0.0, 0.4, 0.2)) @ Matrix.Rotation(math.radians(6), 4, 'X')
F0 = Matrix([A["sword"][f"ws_fit::{t}"][i:i + 4] for i in (0, 4, 8, 12)])
A["sword"].matrix_world = s.matrix_world @ Matrix.Translation((0, 0, g)) @ D @ F0
vl.update()
want = np.array(A["sword"].matrix_world)
sibF0 = M16(sc(sib)["fits"]["Hand R"])
note = T.correct_part(A["sword"], folder=False, both=True)
print("     ", note)
F1 = M16(sc(parts["sword"])["fits"]["Hand R"])
ck("part fix: the sidecar's Hand R fit is the new placement", np.allclose(F1, np.array(D @ F0), atol=1e-5), np.abs(F1 - np.array(D @ F0)).max())
ck("part fix: marked exact (no settling next time)", "Hand R" in sc(parts["sword"]).get("exact", []))
ck("part fix: the sword on the other model moved the same way", np.allclose(W(B["sword"]), np.array(sockof(B["sword"])[0].matrix_world @ Matrix.Translation((0, 0, g)) @ D @ F0), atol=1e-4))
ck("part fix (this file): the folder sibling is untouched", np.allclose(M16(sc(sib)["fits"]["Hand R"]), sibF0))
C1 = send("mA", "sword", "Melee", socket="Hand R"); vl.update()
ck("part fix: sent again, it lands as corrected", np.allclose(W(C1), want, atol=1e-4), np.abs(W(C1) - want).max())
A["sword"] = C1   # the re-send took the old sword's place

# ---- 2. Whole folder
prefs.correct_folder = True
s, t, g = sockof(A["sword"])
D2 = Matrix.Translation((0.0, 0.0, -0.3))
F1m = Matrix([A["sword"][f"ws_fit::{t}"][i:i + 4] for i in (0, 4, 8, 12)])
A["sword"].matrix_world = s.matrix_world @ Matrix.Translation((0, 0, g)) @ D2 @ F1m
vl.update()
note = T.correct_part(A["sword"], folder=True, both=True)
print("     ", note)
ck("whole folder: the sibling's fit moved by the same correction", np.allclose(M16(sc(sib)["fits"]["Hand R"]), np.array(D2) @ sibF0, atol=1e-5),
   np.abs(M16(sc(sib)["fits"]["Hand R"]) - np.array(D2) @ sibF0).max())
prefs.correct_folder = False

# ---- 3. Fix the Socket: the head sits low on this torso -> move the torso's Neck
s, t, g = sockof(A["head"])
Fh = Matrix([A["head"][f"ws_fit::{t}"][i:i + 4] for i in (0, 4, 8, 12)])
L0 = M16([e for e in sc(parts["torso"])["sockets"] if e["type"] == "Neck"][0]["matrix"])
lift = Matrix.Translation((0.0, -0.3, 0.6))
A["head"].matrix_world = Matrix.Translation(s.matrix_world.to_3x3() @ Vector((0.0, -0.3, 0.6))) @ A["head"].matrix_world
vl.update()
wantH = np.array(A["head"].matrix_world)
note = T.correct_socket(A["head"], folder=False, both=True)
print("     ", note)
ck("socket fix: the head stays where you put it", np.allclose(W(A["head"]), wantH, atol=1e-5))
ck("socket fix: the head still sits exactly by its fit on the moved socket",
   np.allclose(np.array(sockof(A["head"])[0].matrix_world @ Matrix.Translation((0, 0, g)) @ Fh), wantH, atol=1e-4))
L1 = M16([e for e in sc(parts["torso"])["sockets"] if e["type"] == "Neck"][0]["matrix"])
ck("socket fix: the torso's sidecar Neck moved by the same amount", np.allclose(L1, L0 @ np.array(lift), atol=1e-4), np.abs(L1 - L0 @ np.array(lift)).max())
ck("socket fix: model B's head moved with its socket", np.allclose(np.array(sockof(B["head"])[0].matrix_world @ Matrix.Translation((0, 0, g)) @ Fh), W(B["head"]), atol=1e-4))
H2 = send("mB", "head", "Heads", socket="Neck"); vl.update(); B["head"] = H2
ck("socket fix: a head sent onto model B lands like model A's", np.allclose(np.array(B["torso"].matrix_world.inverted() @ H2.matrix_world),
   np.array(A["torso"].matrix_world.inverted() @ A["head"].matrix_world), atol=1e-4))

# ---- 4. Socket fix with both sides: the right pad on the arm -> arm's Pad R (and its left copy's Pad L) move
s, t, g = sockof(A["padR"])
sR0 = np.array(s.matrix_world)
sL = sockof(A["padL"])[0]; sL0 = np.array(sL.matrix_world)
Fp = Matrix([A["padR"][f"ws_fit::{t}"][i:i + 4] for i in (0, 4, 8, 12)])
Cp = Matrix.Translation((0.5, 0.0, 0.0)) @ Matrix.Rotation(math.radians(-4), 4, 'Y')
A["padR"].matrix_world = s.matrix_world @ Cp @ Matrix.Translation((0, 0, g)) @ Fp
vl.update()
note = T.correct_socket(A["padR"], folder=False, both=True)
print("     ", note)
ck("both sides: Pad R moved by the correction", np.allclose(np.array(s.matrix_world), sR0 @ np.array(Cp), atol=1e-4))
armLsame = T._same_file(A["armL"]["tiow_src"], A["armR"]["tiow_src"])
print("      (left arm is", "the right arm's left copy)" if armLsame else "its own file)")
MX = np.diag([-1.0, 1, 1, 1])
if armLsame:
    ck("both sides: the left copy's Pad L moved by the mirror image", np.allclose(np.array(sL.matrix_world), sL0 @ (MX @ np.array(Cp) @ MX), atol=1e-4))
else:
    ck("both sides: a left arm in its own file isn't touched without Whole Folder", np.allclose(np.array(sL.matrix_world), sL0, atol=1e-6))
print("FAILS:", fails)
