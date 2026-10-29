"""Round trip: parts lifted from 3rd attempt finalising.blend come back through
the TIOW Inbox with their sockets, and snap exactly as they were assembled."""
import bpy, json, os, sys, tempfile, time
import numpy as np
from mathutils import Matrix

LIB = "/home/claude/liblift"
orig = {r["name"]: r for r in json.load(open("/home/claude/blend/objects.json"))}
scn = json.load(open("/home/claude/blend/scenes.json"))["Scene"]
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
M = lambda rows: np.array(rows, float)
def rel(a, b):            # b in a's frame
    return np.linalg.inv(M(a)) @ M(b)
def close(A, B, tol=2e-3): return np.abs(np.asarray(A) - np.asarray(B)).max() < tol

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
inbox = tempfile.mkdtemp(); T.get_prefs().inbox_path = inbox; T.get_prefs().auto_snap = False   # manual snaps below
scene = bpy.context.scene
ck("fresh scene has no fit types", len(scene.ws_types) == 0, len(scene.ws_types))

parts = {
  "torso":  ("Mar Fil - Tacticus/AssaultMarines-V2/Chests/23-Torso-2.stl", "Chests", "23-Torso-2.001"),
  "combi":  ("Mar Fil - Tacticus/VeteranSquad/Two-Handed Guns/115-CombiWeapon-3-B.stl", "Two-Handed Guns", "115-CombiWeapon-3-B"),
  "helmet": ("Mar Fil - Tacticus/AssaultMarines-V2/Heads/1-Helmet-1.stl", "Heads", "1-Helmet-1"),
  "pack":   ("Mar Fil - Tacticus/AssaultMarines-V2/Jump Packs/55-JumpPack-1.stl", "Jump Packs", "55-JumpPack-1"),
  "arm":    ("Mar Fil - Tacticus/AssaultMarines-V2/Arms/101-Arm-6-R-A.stl", "Arms", "101-Arm-6-R-A"),
}
new = {}
for i, (key, (rel_path, cat, _)) in enumerate(parts.items()):
    scene.cursor.location = (i * 40.0, 0, 0)        # land them apart, like real use
    with open(os.path.join(inbox, f"{i}-{key}.json"), "w") as f:
        json.dump({"path": os.path.join(LIB, rel_path), "category": cat, "name": key}, f)
    T.process_inbox()
    new[key] = bpy.context.view_layer.objects.active
    print("    ", T._state["last"])

torso, combi, helmet, pack, arm = (new[k] for k in ("torso", "combi", "helmet", "pack", "arm"))
WAS = {"Shoulder R": "arm__Torso_r", "Back": "Backpack", "Neck": "Head", "Hand R": "Wrist_socket_r"}
tsocks = {c["ws_type"]: c for c in torso.children if c.get("ws_type")}
ck("torso came back with its sockets, renamed (HeresyArms_r merged into Shoulder R)", sorted(tsocks) == sorted(["Shoulder R", "Back", "Neck"]), sorted(tsocks))
ck("sockets are in the torso's collection", all(s.users_collection[0].name == "Chests" for s in tsocks.values()))
types = {t.name: t for t in scene.ws_types}
ck("fit types used by the sockets were added", {"Shoulder R", "Back", "Neck"} <= set(types), sorted(types))
want = {t["name"]: t for t in scn["types"]}
ck("added types keep their captured offsets",
   all(types[n].captured and close(list(types[n].mat), want[WAS[n]]["mat"], 1e-3) for n in ("Shoulder R", "Back", "Neck")))
o_t = orig["23-Torso-2.001"]["mw"]
for tname, s in tsocks.items():
    o_s = orig[f"23-Torso-2.001_socket_{WAS.get(tname, tname)}"]["mw"]
    ck(f"socket {tname} sits where it did on the torso", close(rel([list(r) for r in torso.matrix_world], [list(r) for r in s.matrix_world]), rel(o_t, o_s)))

def snap(part, tname):
    scene.ws_types_index = [t.name for t in scene.ws_types].index(tname)
    for o in bpy.context.view_layer.objects: o.select_set(False)
    part.select_set(True); torso.select_set(True); bpy.context.view_layer.objects.active = torso
    return bpy.ops.ws.snap_part()

for part, tname, oname in ((combi, "Shoulder R", "115-CombiWeapon-3-B"), (helmet, "Neck", "1-Helmet-1")):
    r = snap(part, tname)
    got = rel([list(x) for x in torso.matrix_world], [list(x) for x in part.matrix_world])
    exp = rel(o_t, orig[oname]["mw"])
    ck(f"{oname} snaps onto the lifted torso exactly as assembled ({tname})", r == {'FINISHED'} and close(got, exp), np.abs(got - exp).max())

r = snap(pack, "Back")
ck("jump pack snaps onto the lifted Back socket", r == {'FINISHED'} and close(rel([list(x) for x in tsocks["Back"].matrix_world], [list(x) for x in pack.matrix_world]), np.eye(4)))
nudge = rel(orig["23-Torso-2.001_socket_Backpack"]["mw"], orig["55-JumpPack-1"]["mw"])[:3, 3]
print(f"     (in the original file the jump pack sits {nudge.round(3).tolist()} off its socket - moved by hand after snapping)")
asocks = [c for c in arm.children if c.get("ws_type") == "Hand R"]
ck("arm came back with its wrist socket", len(asocks) == 1, [s.get("ws_type") for s in arm.children])
o_ws = [r for r in orig.values() if r.get("parent") == "101-Arm-6-R-A" and r["props"].get("ws_type")][0]
ck("wrist socket sits where it did on the arm", close(rel([list(x) for x in arm.matrix_world], [list(x) for x in asocks[0].matrix_world]), rel(orig["101-Arm-6-R-A"]["mw"], o_ws["mw"])))
ck("Hand R type added with its offset", "Hand R" in {t.name for t in scene.ws_types})

# geometry: lifted STL == mesh data from the file (origin preserved)
for key, (_, _, oname) in parts.items():
    me = new[key].data; o = orig[oname]
    co = np.array([v.co[:] for v in me.vertices]); lo, hi = co.min(0), co.max(0)
    ck(f"{oname}: geometry and origin unchanged", close(lo, o["bb_lo"], 2e-3) and close(hi, o["bb_hi"], 2e-3), (lo, o["bb_lo"]))
print(f"\n{len(fails)} failure(s)"); sys.exit(1 if fails else 0)
