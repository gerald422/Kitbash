"""The squad the builder page made (test/out/dump.json) sent through TIOW Inbox 1.17
in Blender: every model is built, and every part lands where the page showed it."""
import bpy, json, math, os, sys, tempfile, time
import numpy as np
sys.path.insert(0, "/home/claude/test"); import rend
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/home/claude/builder/test/out"
LIB = "/mnt/user-data/uploads/d/Kitbash Library"
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_117x/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); tiow_inbox = tempfile.mkdtemp(); prefs.inbox_path = tiow_inbox
libroot = tempfile.mkdtemp(); os.makedirs(os.path.join(libroot, "_builder")); inbox = os.path.join(libroot, "_builder", "inbox"); prefs.builder_inbox = inbox
T.process_inbox()  # makes the builder inbox and both heartbeats
prefs.adaptor_dir = os.path.join(LIB, "Bits", "Adapters")
scene = bpy.context.scene; vl = bpy.context.view_layer
rend.setup(scene, 620)
D = json.load(open(os.path.join(OUT, "dump.json")))
# something selected that the squad must ignore
bpy.ops.mesh.primitive_cube_add(location=(0, -200, 0)); cube = vl.objects.active
for i, r in enumerate(D["requests"]):
    r = dict(r); r["path"] = r["path"].replace("\\", "/").replace("D:/Kitbash Library", LIB)
    with open(os.path.join(inbox, f"sb-{i:03d}.json"), "w") as f:
        json.dump(r, f)
T._state["beat"] = {}; t = time.time(); n = T.process_inbox()
ck("heartbeat in TIOW inbox and in the builder inbox", os.path.exists(os.path.join(tiow_inbox, ".listening")) and os.path.exists(os.path.join(inbox, ".listening")))
ck("version 1.17.1", T.bl_info["version"] == (1, 17, 1))
print(f"      [{time.time() - t:4.1f}s] {n} imported; last: {T._state['last']}")
ck("every request imported", n == len(D["requests"]), (n, len(D["requests"])))
ck("the selected cube was left alone", cube.name in bpy.data.objects and not cube.children)
co = T._part_sockets()[1]
SOCK = {"torso": None, "legs": ("Waist", "Flat Waist"), "adaptor": ("Waist",), "armR": ("Shoulder R",), "armL": ("Shoulder L",),
        "head": ("Neck",), "pack": ("Back",), "padR": ("Pad R",), "padL": ("Pad L",), "handR": ("Hand R",), "handL": ("Hand L",),
        "shinR": ("Shin R",), "shinL": ("Shin L",), "base": ("Base",)}
ids = []
for r in D["requests"]:
    if r["model"] not in ids: ids.append(r["model"])
def A(m): return np.array([list(x) for x in m], float)
def ang(a, b):
    R = a[:3, :3] @ b[:3, :3].T
    return math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
for mi, mid in enumerate(ids):
    lay = [x for x in D["layouts"][mi] if x["W"]]
    obs = [o for o in vl.objects if o.type == 'MESH' and o.get("tiow_model") == mid]
    adaptors = [o for o in vl.objects if o.type == 'MESH' and o.get("tiow_category") == "Adapters" and not o.get("tiow_model")]
    root = T.model_by_id(mid)
    ck(f"model {mi + 1}: built, root is its torso", root is not None and any(x["slot"] == "torso" and root["tiow_src"].endswith(x["path"].replace("\\", "/")) for x in lay), root and root.name)
    if root is None: continue
    R0 = A(root.matrix_world)
    W0 = np.array([x for x in lay if x["slot"] == "torso"][0]["W"]).reshape(4, 4)
    d0 = R0[:3, 3] - W0[:3, 3]
    ck(f"model {mi + 1}: torso where the page showed it (x, y exact; z within 0.2 mm after standing on the base)",
       abs(d0[0]) < 0.05 and abs(d0[1]) < 0.05 and abs(d0[2]) < 0.2 and ang(R0, W0) < 0.05, (np.round(d0, 3), round(ang(R0, W0), 3)))
    for x in lay:
        if x["slot"] == "torso": continue
        want = SOCK[x["slot"]]
        pool = obs + adaptors if x["slot"] == "adaptor" else obs
        cand = [o for o in pool if str(o.get("tiow_src", "")).endswith(x["path"].replace("\\", "/"))
                and (co.snap_socket_of(o) is not None and str(co.snap_socket_of(o).get("ws_type")) in want)]
        if x["slot"] == "adaptor":
            cand = [o for o in cand if T._model_root(co.snap_socket_of(o)) is root] or cand
        if not cand:
            ck(f"model {mi + 1}: {x['slot']} {os.path.basename(x['path'])} in Blender", False,
               [(o.name, co.snap_socket_of(o) and co.snap_socket_of(o).get("ws_type")) for o in obs])
            continue
        o = cand[0]
        W = np.array(x["W"]).reshape(4, 4)
        # compare relative to each model's torso (the base drop is checked above)
        Rb = np.linalg.inv(R0) @ A(o.matrix_world); Rw = np.linalg.inv(W0) @ W
        dm = np.linalg.norm(Rb[:3, 3] - Rw[:3, 3]); da = ang(Rb, Rw)
        tag = " (maker's copy)" if x["v"] is not None else " (mirrored)" if x["mirror"] else ""
        ck(f"model {mi + 1}: {x['slot']} {o.name}{tag} where the page showed it", dm < 0.05 and da < 0.1, f"{dm:.3f} mm {da:.3f} deg")
        if x["v"] is not None:
            ck(f"model {mi + 1}: {x['slot']} came in as the maker's copy", o.get("tiow_variant") == x["v"], o.get("tiow_variant"))
for mi, mid in enumerate(ids):
    root = T.model_by_id(mid)
    if root is None: continue
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, f"blender_model{mi + 1}", obs, {"front": (0.25, 1, 0.1), "q": (0.7, 0.7, 0.2)}, [rend.GREY] * len(obs))
print("\nFAILS:", fails)
