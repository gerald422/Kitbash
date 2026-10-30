"""Marta at 90% through TIOW Inbox 1.17.2: the two-armed piece on a Mar Fil torso lands where the page shows it, at 90%."""
import bpy, json, os, sys, tempfile, time, struct
import numpy as np
LIB = "/mnt/user-data/uploads/d/Kitbash Library"
TOR = "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 3.stl"
PC = "Marta PunkGirl - Weapons/Primary Combo Weapons/Marta Punkgirl - Primary Combo Weapons/Primary Combo weapons (part 3)/2h weapons-arms/Two-Handed Guns/Marta Combo Weapons - 2H Combi Grav.stl"
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d)));  c or fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_117x/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); prefs.builder_inbox = inbox
os.makedirs(inbox, exist_ok=True); T.process_inbox()
for i, (rel, cat, sock) in enumerate([(TOR, "Chests", None), (PC, "Two-Handed Guns", "Shoulder R")]):
    r = {"schemaVersion": 1, "path": os.path.join(LIB, rel), "name": os.path.basename(rel)[:-4], "title": os.path.basename(rel)[:-4],
         "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": "m90"}
    if sock: r["socket"] = sock
    else: r["at"] = [0, 0, 0]
    json.dump(r, open(os.path.join(inbox, "sb-%03d.json" % i), "w"))
T._state["beat"] = {}; n = T.process_inbox(); print("imported", n, T._state["last"])
vl = bpy.context.view_layer
obs = {o.get("tiow_category"): o for o in vl.objects if o.type == 'MESH' and o.get("tiow_model") == "m90"}
tor, pc = obs.get("Chests"), obs.get("Two-Handed Guns")
ck("both imported", tor is not None and pc is not None, list(obs))
ck("the piece carries scale 0.9", abs(float(pc.get("tiow_scale", 1)) - 0.9) < 1e-9, pc.get("tiow_scale"))
# expected world matrix: torso . Shoulder R . fit (the page's maths), in Blender units
unit = float(tor.get("tiow_unit", 1.0))
sd_t = json.load(open(os.path.join(LIB, TOR[:-4] + ".sockets.json"))); sd_p = json.load(open(os.path.join(LIB, PC[:-4] + ".sockets.json")))
M = lambda a: np.array(a, float).reshape(4, 4)
S = M([s["matrix"] for s in sd_t["sockets"] if s["type"] == "Shoulder R"][0]); Fp = M(sd_p["fits"]["Shoulder R"])
want = np.array(tor.matrix_world) @ S @ Fp
got = np.array(pc.matrix_world); got_mm = got.copy(); got_mm[:3, 3] /= unit; want[:3, 3] /= 1.0
want_mm = (np.array(tor.matrix_world) / 1); want_mm[:3, 3] /= unit; want_mm = want_mm @ S @ Fp
d = np.abs(got_mm[:3, 3] - want_mm[:3, 3]).max(); R = got_mm[:3, :3] @ want_mm[:3, :3].T
ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
print("      offset from the page's spot %.3f mm, %.2f deg (TIOW rocks/settles spans pieces a little)" % (d, ang))
ck("piece where the page shows it (within 1 mm / 3 deg)", d < 1.0 and ang < 3.0, (d, ang))
# size: the mesh is the STL at 90%
V = np.array([v.co[:] for v in pc.data.vertices]) / unit
import sys; sys.path.insert(0, "/home/claude/real"); import fitlib as F
V0, _ = F.stl(os.path.join(LIB, PC))
r = (V.max(0) - V.min(0)) / (V0.max(0) - V0.min(0))
ck("mesh at 90% of the STL", np.allclose(r, 0.9, atol=0.002), r.round(4))
# the right shoulder stays on the socket, the left lands near Shoulder L
print("fails:", len(fails))
