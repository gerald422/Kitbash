"""Auto-snap: parts sent from TIOW land on the selected model's sockets.
Uses the library lifted from '3rd attempt finalising actual.blend'."""
import bpy, json, os, shutil, sys, tempfile
import numpy as np
from mathutils import Matrix, Vector

LIB = "/home/claude/liblift_v3"
D = {o["name"]: o for o in json.load(open("/home/claude/blend/actual/dump.json"))["objects"]}
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
A = lambda m: np.array([list(r) for r in m], float)
def close(a, b, tol=2e-3): return np.abs(np.asarray(a) - np.asarray(b)).max() < tol

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs()
inbox = tempfile.mkdtemp(); prefs.inbox_path = inbox
scene = bpy.context.scene
vl = bpy.context.view_layer
print("parent mode:", scene.ws_parent_mode)

n = [0]
def send(rel, cat, cursor=None):
    n[0] += 1
    if cursor is not None:
        scene.cursor.location = cursor
    with open(os.path.join(inbox, f"{n[0]:03d}.json"), "w") as f:
        json.dump({"path": os.path.join(LIB, rel), "category": cat, "name": os.path.basename(rel)}, f)
    T.process_inbox()
    print("     ", T._state["last"])
    return vl.objects.active
def select(ob):
    for o in vl.objects: o.select_set(False)
    if ob is not None:
        ob.select_set(True)
    vl.objects.active = ob
def sock_of(part, t):
    return next(c for c in part.children if c.get("ws_type") == t)
def on(part):
    return part.ws_snap_sock_ref

print("\n== nothing selected: torso just arrives")
select(None)
torso = send("Mar Fil - Tacticus/AssaultMarines-V2/Chests/23-Torso-2.stl", "Chests", (0, 0, 0))
ck("torso has the renamed sockets", sorted(c["ws_type"] for c in torso.children if c.get("ws_type")) ==
   ["Back", "Legs to chest", "Neck", "Shoulder R"], [c.get("ws_type") for c in torso.children])
ck("fit types came in under the new names", {"Shoulder R", "Back", "Neck"} <= {t.name for t in scene.ws_types})

print("\n== arm with the torso selected -> Shoulder R")
select(torso)
arm1 = send("Mar Fil - Tacticus/AssaultMarines-V2/Arms/77-Arm-1-R-B.stl", "Arms", (40, 0, 0))
sh = sock_of(torso, "Shoulder R")
ck("arm is on the torso's Shoulder R", on(arm1) == sh, on(arm1))
ck("arm origin sits on the socket", close(A(arm1.matrix_world), A(sh.matrix_world)))
ck("status says so", "snapped to Shoulder R on" in T._state["last"], T._state["last"])

print("\n== pistol with the arm selected -> that arm's Hand R")
pistol = send("Mar Fil - Tacticus/AssaultMarines-V2/Pistols/211-BoltPistol-R.stl", "Pistols", (80, 0, 0))
hand1 = sock_of(arm1, "Hand R")
off = Matrix.Translation((0, 0, 0)) @ Matrix(np.array(next(t.mat for t in scene.ws_types if t.name == "Hand R")).reshape(4, 4).tolist())
ck("pistol is on the arm's Hand R", on(pistol) == hand1, on(pistol))
ck("pistol pose = hand socket @ Hand R offset", close(A(pistol.matrix_world), A(hand1.matrix_world @ off)))

print("\n== second arm with the pistol selected: swaps the arm, pistol moves across")
arm1_name = arm1.name
arm2 = send("Mar Fil - Tacticus/AssaultMarines-V2/Arms/82-Arm-2-R-B.stl", "Arms", (120, 0, 0))
ck("new arm on Shoulder R", on(arm2) == sh)
ck("old arm deleted (it came from TIOW)", bpy.data.objects.get(arm1_name) is None)
hand2 = sock_of(arm2, "Hand R")
ck("pistol now on the new arm's Hand R", on(pistol) == hand2, on(pistol))
ck("pistol pose follows the new hand", close(A(pistol.matrix_world), A(hand2.matrix_world @ off)))
ck("status reports the swap", "replaced " + arm1_name in T._state["last"] and "moved across" in T._state["last"], T._state["last"])

print("\n== heresy arm (re-based in the lift) lands where the HeresyArms_r socket put it")
select(torso)
her = send("_Unsorted/From 3rd attempt finalising actual/Arms/patternC banner arm.stl", "Arms", (160, 0, 0))
ck("heresy arm replaced the Mar Fil arm on Shoulder R", on(her) == sh and on(pistol) == sock_of(her, "Hand R") if any(c.get("ws_type") == "Hand R" for c in her.children) else on(her) == sh)
SA = A(D["23-Torso-2.001_socket_arm__Torso_r"]["mw"]); SB = A(D["23-Torso-2.001_socket_HeresyArms_r"]["mw"])
TO = A(D["23-Torso-2.001"]["mw"])
o = D["patternC banner arm"]
lo, hi = np.array(o["bb_lo"]), np.array(o["bb_hi"])
corners = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
want = (A(torso.matrix_world) @ np.linalg.inv(TO) @ SB @ corners.T).T[:, :3]     # old geometry on the heresy socket
v = np.array([her.matrix_world @ x.co for x in her.data.vertices])
# the old local box, carried to world through the HeresyArms_r socket, must contain the new world geometry snugly
R = np.linalg.inv(np.linalg.inv(TO) @ SB) @ np.linalg.inv(A(torso.matrix_world)) @ np.c_[v, np.ones(len(v))].T
loc = R.T[:, :3]
ck("geometry = old arm on the old HeresyArms_r socket", close(loc.min(0), lo, 3e-3) and close(loc.max(0), hi, 3e-3), (loc.min(0), lo, loc.max(0), hi))

print("\n== helmet -> Neck, jump pack -> Back")
select(torso)
helm = send("Mar Fil - Tacticus/AssaultMarines-V2/Heads/1-Helmet-1.stl", "Heads", (200, 0, 0))
ck("helmet on Neck", on(helm) == sock_of(torso, "Neck"))
ck("helmet sits on torso exactly as in your file",
   close(np.linalg.inv(A(torso.matrix_world)) @ A(helm.matrix_world), np.linalg.inv(TO) @ A(D["1-Helmet-1"]["mw"])))
select(torso)
pack = send("Mar Fil - Tacticus/AssaultMarines-V2/Jump Packs/55-JumpPack-1.stl", "Jump Packs", (240, 0, 0))
ck("jump pack on Back", on(pack) == sock_of(torso, "Back"))
ck("jump pack brought its fin sockets", sorted(c["ws_type"] for c in pack.children if c.get("ws_type")) == ["Pack Fin L", "Pack Fin R"])

print("\n== left arm: no Shoulder L on this torso")
tmpd = os.path.join(LIB, "_test", "Arms"); os.makedirs(tmpd, exist_ok=True)
shutil.copy(os.path.join(LIB, "Mar Fil - Tacticus/AssaultMarines-V2/Arms/77-Arm-1-R-B.stl"), os.path.join(tmpd, "77-Arm-1-L-B.stl"))
select(torso)
left = send("_test/Arms/77-Arm-1-L-B.stl", "Arms", (280, 0, 0))
ck("left arm stays at the cursor", on(left) is None and left.parent is None)
ck("status says there's no Shoulder L", "no Shoulder L" in T._state["last"], T._state["last"])

print("\n== nothing selected: arm stays at the cursor")
select(None)
lone = send("Mar Fil - Tacticus/AssaultMarines-V2/Arms/82-Arm-2-R-B.stl", "Arms", (320, 0, 0))
ck("not snapped", on(lone) is None and "select a model" in T._state["last"], T._state["last"])

print("\n== side words")
for name, want_side in (("77-Arm-1-R-B", "R"), ("Nartheciumarms_l", "L"), ("HeresyArms_r", "R"), ("Arm_L_03", "L"),
                        ("LeftOrientated", "L"), ("RawSTL(Right)", "R"), ("Lower A 1", None), ("115-CombiWeapon-3-B", None),
                        ("ShinPads-Mirrored", None)):
    ck(f"side of {name!r} = {want_side}", T.part_side(name) == want_side, T.part_side(name))

print("\n(pauldrons, shin pads and belt bits: see test_pads.py)")
print("\n== settle reproduces a hand-placed fit: Backpack2 against the torso")
# in your file Backpack2 sits on the Back socket, touching the torso (0.03 overlap)
T._lib_cache.clear()
lj = json.load(open(os.path.join(LIB, "_library.json")))
lj2 = dict(lj); lj2["joints"] = dict(lj["joints"]); lj2["joints"]["Backpacks"] = {"socket": "Back", "settle": "+Y"}
os.makedirs(os.path.join(LIB, "_test2"), exist_ok=True)
json.dump(lj2, open(os.path.join(LIB, "_test2", "_library.json"), "w"))
os.makedirs(os.path.join(LIB, "_test2", "Backpacks"), exist_ok=True)
shutil.copy(os.path.join(LIB, "_Unsorted/From 3rd attempt finalising actual/Backpacks/Backpack2.stl"), os.path.join(LIB, "_test2", "Backpacks", "Backpack2.stl"))
select(torso)
bp_rel = "_test2/Backpacks/Backpack2.stl"
bp = send(bp_rel, "Backpacks", (440, 0, 0))
back = sock_of(torso, "Back")
ck("Backpack2 replaced the jump pack on Back", on(bp) == back)
rel = np.linalg.inv(A(back.matrix_world)) @ A(bp.matrix_world)
ck("settled to within 0.05 of where you put it by hand", np.abs(rel[:3, 3]).max() < 0.05, rel[:3, 3])
print("      offset from your placement:", rel[:3, 3].round(3))

shutil.rmtree(os.path.join(LIB, "_test")); shutil.rmtree(os.path.join(LIB, "_test2"))
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
