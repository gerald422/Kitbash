"""Marta one-handed parts through TIOW Inbox: Marta arms (90%, shoulder rule) on a Mar Fil torso; TIOW's own wrist rule
on the arm and hand rule on the held part. python t_onehand.py -- WORKLIB TIOW_FILE OUTDIR"""
import bpy, json, os, sys, tempfile
import numpy as np
sys.path.insert(0, "/home/claude/test"); import rend
W, TIOW, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
TOR = W + "/MarFil/Torso 1.stl"
B = W + "/Marta/bionics-for-bois-and-gurls-september-23/"; S = W + "/Marta/Marta GURLS/Marta Feb 2024 Dragonborn Gurls/02.24 Salamanders/"; L = W + "/Marta/Marta GURLS/04.23 DA Lion Knights/"
def _req(t):
    t = (t,) if isinstance(t, str) else t
    p = t[0] + ".stl"; d = json.load(open(t[0] + ".sockets.json")); cat = d["category"]
    sock = t[1] if len(t) > 1 else [k for k in d["fits"]][0]
    return (p, cat, sock)
MODELS = [  # (name, [(path, category, socket)])
    ("n1", [(B + "bionic-amrs-bionic-arm-3-with-rifle-primary"), (B + "bionic-arms-for-shield-bionic-left-arm-boarding-shield")]),
    ("n2", [(B + "bionic-arms-for-shield-bionic-arm-right-bording-shield"), (B + "bionic-arms-for-shield-bionic-left-arm-empty-shield"), (B + "bionic-arms-for-shield-rifle-one-handed", "Hand L"), (B + "bionic-arms-for-shield-boarding-shield-1 with handle", "Hand R")]),
    ("n3", [(B + "bionic-amrs-bionic-arm-6"), (S + "arms/L_dragon_arms_1"), (S + "shield/shield_1 with handle", "Hand L"), (B + "bionic-arms-for-shield-rifle-one-handed", "Hand R")]),
    ("n4", [(L + "arms/arm_1"), (B + "bionic-amrs-arm-1-primary"), (L + "weapons/sword_1", "Hand R"), (B + "bionic-arms-for-shield-boarding-shield-1 with handle", "Hand L")]),
]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox()
k = 0
for mi, (mn, parts) in enumerate(MODELS):
    for j, (p, cat, sock) in enumerate([(TOR, "Chests", None)] + [_req(x) for x in parts]):
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": os.path.basename(p)[:-4], "category": cat,
             "tags": [], "itemId": "", "sentAt": "", "model": mn}
        if sock: r["socket"] = sock
        else: r["at"] = [mi * 60.0, 0, 0]
        json.dump(r, open(os.path.join(inbox, "sb-%03d.json" % k), "w")); k += 1
T._state["beat"] = {}; n = T.process_inbox(); print("imported", n)
print(T._state.get("last"))
vl = bpy.context.view_layer
scene = bpy.context.scene; rend.setup(scene, 520)
for mn, parts in MODELS:
    obs = [o for o in vl.objects if o.type == 'MESH' and o.get("tiow_model") == mn]
    for o in obs:
        if o.get("tiow_category") == "Chests": continue
        socks = [c.get("ws_type") for c in o.children if c.get("ws_type")]
        par = o.parent.get("ws_type") if o.parent is not None else None
        print("  %s %-55s scale %.2f on %-12s sockets %s" % (mn, o.name[:55], float(o.get("tiow_scale", 1)), o.get("tiow_snapped") or "", [s for s in socks if s.startswith("Hand")]))
    cols = [rend.GREY if o.get("tiow_category") == "Chests" else rend.BLUE if o.get("tiow_category") == "Arms" else rend.ORANGE for o in obs]
    rend.render(scene, OUT, mn, obs, {"front": (0, 1, 0.15), "side_r": (1, 0.4, 0.1), "side_l": (-1, 0.4, 0.1), "top": (0, 0.2, 1)}, cols)
