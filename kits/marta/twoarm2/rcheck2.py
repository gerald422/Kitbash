"""Each new Marta part through TIOW Inbox 1.17.7 on Mar Fil Assault Torso 1: arms on their shoulder, held parts in
Mar Fil Arm 1A R's hand. One front-ish render per model. python rcheck.py -- OUTDIR"""
import bpy, json, os, sys, tempfile
sys.path.insert(0, "/home/claude/test"); import rend
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
NC = "/mnt/user-data/uploads/d/new cults/"; W = "/home/claude/work/mm/W/MarFil/"
TOR, ARM = W + "MarFil Assault - Torso 1.stl", W + "MarFil Assault - Arm 1A R.stl"
R = [{"rel": k} for k in json.load(open("/home/claude/work/m2h/keep.json"))]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/kitbash/addons/tiow_inbox.py", overwrite=True); bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); n = 0; models = []
for i, r in enumerate(R):
    sc = NC + os.path.splitext(r["rel"])[0] + ".sockets.json"
    if not os.path.exists(sc): continue
    d = json.load(open(sc)); m = "m%02d" % i; p = NC + r["rel"]
    reqs = [(TOR, "Chests", None), (p, d["category"], "Shoulder R")]
    for q, cat, sock in reqs:
        j = {"schemaVersion": 1, "path": q, "name": os.path.basename(q)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": m}
        if sock: j["socket"] = sock
        else: j["at"] = [60 * (i % 8), 60 * (i // 8), 0]
        n += 1; json.dump(j, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox(); models.append((m, r))
scene = bpy.context.scene; rend.setup(scene, 300)
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
for m, r in models:
    mine = [o for o in obs if o.get("tiow_model") == m]
    if not mine:
        root = [o for o in obs if o.get("tiow_model") == m]
    cols = [rend.GREY if o.get("tiow_category") in ("Chests",) or os.path.basename(str(o.name)).startswith("MarFil") else rend.ORANGE for o in mine]
    snapped = [o.get("ws_snap_type") for o in mine]
    print("MODEL", m, os.path.basename(r["rel"]), [o.name[:30] for o in mine], snapped)
    rend.render(scene, OUT, m, mine, {"f": (0.35, 1, 0.2), "s": (1, 0.15, 0.1)}, cols)
