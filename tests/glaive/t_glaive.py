"""Toothed chainswords / chainglaives through TIOW Inbox: right hand, the left-hand copy on the left, and the
two-handed glaives turned about the right wrist to meet the left arm."""
import bpy, json, os, sys, tempfile
import numpy as np
sys.path.insert(0, "/home/claude/test"); import rend
LIB = "/mnt/user-data/uploads/d/Kitbash Library"; GL = "/home/claude/twoarm/glaivelib"
TOR = LIB + "/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 3.stl"
LEGS = LIB + "/Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A.stl"
MF = (LIB + "/Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R.stl", LIB + "/Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1B L.stl")
SP = (LIB + "/Springles - Heresy/patternC arms/2 handed melee/Arms/Springles Pattern C - Duel Melee Arm 1 R.stl", LIB + "/Springles - Heresy/patternC arms/2 handed melee/Arms/Springles Pattern C - Duel Melee Arm 1 L.stl")
G = lambda n: GL + "/Bits Toothed - " + n + ".stl"
MODELS = [("swords", MF, [(G("Chainsword 01"), "Melee", "Hand R"), (G("Chainsword 07"), "Melee", "Hand L")]),
          ("glaives", MF, [(G("Chainglaive 03"), "Melee", "Hand R"), (G("Chainglaive 09"), "Melee", "Hand L")]),
          ("two hands, duel arms", SP, [(G("Chainglaive Two Hands 01"), "Two-Handed Held", "Hand R")]),
          ("two hands, duel arms 2", SP, [(G("Chainglaive Two Hands 07"), "Two-Handed Held", "Hand R")]),
          ("two hands, Mar Fil arms", MF, [(G("Chainglaive Two Hands 05"), "Two-Handed Held", "Hand R")])]
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_117x/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); scene = bpy.context.scene; rend.setup(scene, 520); co = T._part_sockets()[1]
n = 0
for mi, (label, arms, weps) in enumerate(MODELS):
    mid = "g%d" % mi
    reqs = [(TOR, "Chests", None), (LEGS, "Legs", None), (arms[0], "Arms", "Shoulder R"), (arms[1], "Arms", "Shoulder L")] + list(weps)
    for i, (p, cat, sock) in enumerate(reqs):
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": os.path.basename(p)[:-4], "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": mid}
        if sock: r["socket"] = sock
        else: r["at"] = [mi * 70.0, 0, 0] if cat == "Chests" else None
        if r.get("at") is None: r.pop("at", None)
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
    obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH' and o.get("tiow_model") == mid]
    for p, cat, sock in weps:
        nm = os.path.basename(p)[:-4]
        w = next((o for o in obs if o.get("tiow_category") == cat and o.name.startswith(nm[:50])), None)
        s = co.snap_socket_of(w) if w is not None else None
        st = s.get("ws_type") if s is not None else None
        extra = ""
        if w is not None and w.get("tiow_offhand") is not None:
            # how far the glaive's left hand ended up from the left arm's wrist
            H = np.array(w.matrix_world) @ np.array(w["tiow_offhand"], float).reshape(4, 4)
            hl = [o for o in bpy.data.objects if o.get("ws_type") == "Hand L" and o.parent is not None and o.parent.get("tiow_model") == mid]
            d = min(np.linalg.norm(np.array(o.matrix_world.translation) - H[:3, 3]) for o in hl) if hl else None
            extra = "; left hand %.1f mm from the left wrist" % d if d is not None else "; no left wrist"
        ck("%-24s %-40s on %s%s" % (label, nm, st, extra), st == sock, st)
    parts = [o for o in obs if o.get("tiow_category") in ("Chests", "Legs", "Arms", "Melee", "Two-Handed Held", "Adapters")]
    cols = [rend.ORANGE if o.get("tiow_category") in ("Melee", "Two-Handed Held") else rend.GREY for o in parts]
    rend.render(scene, "/home/claude/twoarm/bl/out", "glaive_%d" % mi, parts, {"front": (0.3, 1, 0.15), "right": (1, 0.2, 0.1), "left": (-1, 0.3, 0.1)}, cols, pad=1.05)
print("fails:", len(fails))
