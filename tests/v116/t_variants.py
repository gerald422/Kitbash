"""TIOW Inbox 1.16: one file, both sides.

reflib = the test library as it is; varlib = the same with mirror copies folded
into their twins' sockets files (fold_twins.py). A part sent from varlib that
goes on the other side must land exactly where its old copy from reflib lands
(same shape in the same place, same sockets). Then the Mirror button."""
import bpy, json, math, os, sys, tempfile, time
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
from scipy.spatial import cKDTree
HERE = "/home/claude/test/v116"
REF, VAR = HERE + "/reflib", HERE + "/varlib"
# RENLOG=<rename log>: the folded library renamed (renvar), sent the same parts by their new names
MAP = {}
if os.environ.get("RENLOG"):
    import csv
    VAR = HERE + "/renvar"
    for r in csv.DictReader(open(os.environ["RENLOG"], encoding="utf-8-sig")):
        if r["status"] == "renamed":
            MAP[r["was"].replace("\\", "/")] = r["now"].replace("\\", "/")
def vr(lib, rel): return MAP.get(rel, rel) if lib == VAR else rel
AM = "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL"
OUT = HERE + "/out"; os.makedirs(OUT, exist_ok=True)
A = lambda m: np.array([list(r) for r in m], float)
fails = []
def ck(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  {detail}"))
    if not cond: fails.append(label)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_blender/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); inbox = tempfile.mkdtemp(); prefs.inbox_path = inbox
scene = bpy.context.scene; vl = bpy.context.view_layer
rend.setup(scene, 620)
_n = [0]
def send(lib, rel, cat, cursor=None):
    _n[0] += 1
    if cursor is not None: scene.cursor.location = cursor
    with open(os.path.join(inbox, f"{_n[0]:03d}.json"), "w") as f:
        rel = vr(lib, rel)
        json.dump({"path": os.path.join(lib, rel), "category": cat, "name": os.path.splitext(os.path.basename(rel))[0]}, f)
    t = time.time(); T.process_inbox()
    print(f"      [{time.time() - t:4.1f}s]", T._state["last"])
    return vl.objects.active
def select(ob):
    for o in list(vl.objects): o.select_set(False)
    if ob is not None: ob.select_set(True)
    vl.objects.active = ob
def on(p):
    s = T._part_sockets()[1].snap_socket_of(p) if p is not None else None
    return str(s.get("ws_type")) if s is not None else None
def sock(part, t): return next((c for c in part.children if c.get("ws_type") == t), None)
def world_pts(ob):
    M = A(ob.matrix_world); V = np.array([v.co for v in ob.data.vertices])
    return V @ M[:3, :3].T + M[:3, 3]
def rel_pts(ob, root):
    P = world_pts(ob); R = np.linalg.inv(A(root.matrix_world)); return P @ R[:3, :3].T + R[:3, 3]
def same_shape(a, ra, b, rb):
    """median / 95% gap (mm) between part a (in root ra's frame) and part b (in rb's)"""
    P = rel_pts(a, ra); Q = rel_pts(b, rb)
    rng = np.random.default_rng(0); P = P[rng.choice(len(P), min(len(P), 20000), replace=False)]
    d = cKDTree(Q).query(P)[0]; return float(np.median(d)), float(np.quantile(d, 0.95))
def frame_rel(ob, root):
    return np.linalg.inv(A(root.matrix_world)) @ A(ob.matrix_world)
def socks_match(a, ra, b, rb, mm=0.05, deg=0.5):
    """every socket type on a is on b at the same place (relative to the roots)"""
    out = []
    for s in [c for c in a.children if c.get("ws_type") is not None]:
        t = s["ws_type"]; s2 = sock(b, t)
        if s2 is None: out.append(f"{t} missing"); continue
        M1, M2 = frame_rel(s, ra), frame_rel(s2, rb)
        dmm = np.linalg.norm(M1[:3, 3] - M2[:3, 3])
        R = M1[:3, :3] @ M2[:3, :3].T; dd = math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
        if dmm > mm or dd > deg: out.append(f"{t} off {dmm:.3f} mm {dd:.2f} deg")
    return out
def gap_ok(label, a, ra, b, rb, med=0.05, p95=0.15):
    m, p = same_shape(a, ra, b, rb); ck(label, m <= med and p <= p95, f"median {m:.3f} p95 {p:.3f}")
def sidecar(lib, rel): return json.load(open(os.path.join(lib, os.path.splitext(vr(lib, rel))[0] + ".sockets.json")))

TORSO = f"{AM}/Chest/24-Torso-3.stl"
ck("varlib: 103-Arm-6-L-A folded into 102-Arm-6-R-B", any(v.get("name") == "103-Arm-6-L-A" for v in sidecar(VAR, f"{AM}/Arms/102-Arm-6-R-B.stl").get("variants", [])))
ck("varlib: 103-Arm-6-L-A gone from the library", not os.path.exists(f"{VAR}/{AM}/Arms/103-Arm-6-L-A.stl"))

# ---- 1. reference marine (old left copies) and the same from one file per part
select(None); t_ref = send(REF, TORSO, "Chests", (0, 0, 0))
select(None); t_var = send(VAR, TORSO, "Chests", (150, 0, 0))
for t in (t_ref, t_var):
    select(t); send(REF if t is t_ref else VAR, f"{AM}/Legs/30-Legs-3.stl", "Legs")
    select(t); send(REF if t is t_ref else VAR, f"{AM}/Arms/106-Arm-7-R-A.stl", "Arms")
# reference left arm: the old copy
select(t_ref); aL_ref = send(REF, f"{AM}/Arms/103-Arm-6-L-A.stl", "Arms")
ck("ref: 103-Arm-6-L-A on Shoulder L", on(aL_ref) == "Shoulder L", T._state["last"])
# varlib: the right arm file, sent with the right shoulder taken, goes left as its variant
select(t_var); aL_var = send(VAR, f"{AM}/Arms/102-Arm-6-R-B.stl", "Arms")
ck("var: 102-Arm-6-R-B (right taken) goes on Shoulder L", on(aL_var) == "Shoulder L", T._state["last"])
ck("var: it came in as the 103-Arm-6-L-A variant", aL_var.get("tiow_orig") == "103-Arm-6-L-A" and aL_var.get("tiow_variant") is not None, (aL_var.name, aL_var.get("tiow_orig")))
gap_ok("var: left arm same shape and place as the old copy", aL_var, t_var, aL_ref, t_ref)
bad = socks_match(aL_ref, t_ref, aL_var, t_var); ck("var: left arm sockets match the old copy's", not bad, bad)
# a second one with both shoulders taken replaces the right arm (own side first)
select(t_var); a3 = send(VAR, f"{AM}/Arms/117-Arm-9-R-B.stl", "Arms")
ck("var: 117-Arm-9-R-B with both taken replaces the right arm", on(a3) == "Shoulder R" and a3.get("tiow_variant") is None, (on(a3), T._state["last"]))
# selecting the left arm sends it left (the 12 mm offset copy)
select(aL_var); a4 = send(VAR, f"{AM}/Arms/117-Arm-9-R-B.stl", "Arms")
select(aL_ref); a4r = send(REF, f"{AM}/Arms/118-Arm-9-L-A.stl", "Arms")
ck("var: 117 with the left arm selected replaces it", on(a4) == "Shoulder L" and a4.get("tiow_orig") == "118-Arm-9-L-A", (on(a4), a4.get("tiow_orig")))
gap_ok("var: 118 variant same shape and place as the old 118 copy", a4, t_var, a4r, t_ref)
bad = socks_match(a4r, t_ref, a4, t_var); ck("var: 118 variant sockets match", not bad, bad)
# a sword in the left hand: right sword file into the selected left arm
select(a4r); s_ref = send(REF, f"{AM}/Melee/LeftOrientated/202-PowerSword-A-1-L.stl", "Melee")
select(a4); s_var = send(VAR, f"{AM}/Melee/202-PowerSword-A-1-R.stl", "Melee")
ck("ref: sword L in Hand L", on(s_ref) == "Hand L", T._state["last"])
ck("var: sword R file into the left arm goes in Hand L as its variant", on(s_var) == "Hand L" and s_var.get("tiow_orig") == "202-PowerSword-A-1-L", (on(s_var), s_var.get("tiow_orig")))
gap_ok("var: left sword same shape and place", s_var, t_var, s_ref, t_ref)
# pistol: free right hand takes the file as it is, then the left hand the variant
rarm_var = next(o for o in T._descendants(t_var) if o.type == 'MESH' and on(o) == "Shoulder R")
rarm_ref = next(o for o in T._descendants(t_ref) if o.type == 'MESH' and on(o) == "Shoulder R")
select(t_var); p1 = send(VAR, f"{AM}/Pistols/211-BoltPistol-R.stl", "Pistols")
ck("var: pistol with the right hand free goes right as itself", on(p1) == "Hand R" and p1.get("tiow_variant") is None, (on(p1), T._state["last"]))

# ---- 2. Mirror button
# the right arm (117, holding the pistol) goes left as its 118 copy, the pistol with it; the left arm
# (the 118 variant, holding the sword) swaps over to the right as 117, its sword with it
select(a3)
bpy.ops.tiow.mirror_part()
print("     ", T._state["last"])
nowL = next((o for o in T._descendants(t_var) if o.type == 'MESH' and on(o) == "Shoulder L"), None)
nowR = next((o for o in T._descendants(t_var) if o.type == 'MESH' and on(o) == "Shoulder R"), None)
ck("mirror: right arm 117 now on Shoulder L as the 118 copy", nowL is not None and nowL.get("tiow_orig") == "118-Arm-9-L-A", (nowL and nowL.get("tiow_orig")))
ck("mirror: the left arm swapped over to Shoulder R as 117", nowR is not None and nowR.get("tiow_orig") == "117-Arm-9-R-B" and nowR.get("tiow_variant") is None, (nowR and nowR.get("tiow_orig")))
sw = [o for o in vl.objects if o.type == 'MESH' and "PowerSword" in str(o.get("tiow_orig")) and T._model_root(o) is t_var]
ck("mirror: one sword, now the right-hand file in Hand R", len(sw) == 1 and on(sw[0]) == "Hand R" and sw[0].get("tiow_orig") == "202-PowerSword-A-1-R", [(on(o), o.get("tiow_orig")) for o in sw])
pis = [o for o in vl.objects if o.type == 'MESH' and "BoltPistol" in str(o.get("tiow_orig")) and T._model_root(o) is t_var]
ck("mirror: one pistol, now the left copy in Hand L", len(pis) == 1 and on(pis[0]) == "Hand L" and pis[0].get("tiow_orig") == "Weapons-Assault211-BoltPistol-L", [(on(o), o.get("tiow_orig")) for o in pis])
gap_ok("mirror: 118 copy on the left same as the old 118 file there", nowL, t_var, a4r, t_ref)
select(rarm_ref); r117 = send(REF, f"{AM}/Arms/117-Arm-9-R-B.stl", "Arms")
gap_ok("mirror: 117 on the right same as a fresh 117", nowR, t_var, r117, t_ref)
select(a4r); pl = send(REF, f"{AM}/Pistols/LeftOrientated/Weapons-Assault211-BoltPistol-L.stl", "Pistols")
gap_ok("mirror: pistol in the left hand same as the old left pistol there", pis[0], t_var, pl, t_ref)

# a part with no copy folded in (106): Mirror makes a plain mirror, saved with it
select(None); t_s = send(VAR, TORSO, "Chests", (450, 0, 0))
select(t_s); a106 = send(VAR, f"{AM}/Arms/106-Arm-7-R-A.stl", "Arms")
select(a106); bpy.ops.tiow.mirror_part(); print("     ", T._state["last"])
m106 = next((o for o in T._descendants(t_s) if o.type == 'MESH' and on(o) == "Shoulder L"), None)
ck("plain mirror: 106 now on Shoulder L", m106 is not None and str(m106.get("tiow_orig")).startswith("106-Arm-7-L"), m106 and m106.get("tiow_orig"))
sc106 = sidecar(VAR, f"{AM}/Arms/106-Arm-7-R-A.stl")
ck("plain mirror: saved with 106", any(v.get("synth") for v in sc106.get("variants", [])))
ck("plain mirror: nothing left on Shoulder R", not any(on(o) == "Shoulder R" for o in T._descendants(t_s) if o.type == 'MESH'))
select(None); t_m = send(REF, TORSO, "Chests", (300, 0, 0))
select(t_m); r106 = send(REF, f"{AM}/Arms/106-Arm-7-R-A.stl", "Arms")
def in_frame(P, root, s):
    M = np.linalg.inv(frame_rel(s, root)); return P @ M[:3, :3].T + M[:3, 3]
Pm = in_frame(rel_pts(r106, t_m), t_m, sock(t_m, "Shoulder R")) * [-1, 1, 1]
Qm = in_frame(rel_pts(m106, t_s), t_s, sock(t_s, "Shoulder L"))
d = cKDTree(Qm).query(Pm[::7])[0]
ck("plain mirror: the left 106 is the right one's mirror image in its shoulder's frame", np.median(d) < 0.05, f"median {np.median(d):.3f}")
select(m106); bpy.ops.tiow.mirror_part(); print("     ", T._state["last"])
back = next((o for o in T._descendants(t_s) if o.type == 'MESH' and on(o) == "Shoulder R"), None)
ck("mirror again: 106 back on Shoulder R as itself", back is not None and back.get("tiow_orig") == "106-Arm-7-R-A" and back.get("tiow_variant") is None, (back and back.get("tiow_orig")))
gap_ok("mirror again: same place as a fresh 106", back, t_s, r106, t_m)

# ---- 3. Mirror legs in place: the legs flip, what's on them stays (base, pads)
select(t_var); lg = next(o for o in T._descendants(t_var) if o.type == 'MESH' and on(o) == "Waist")
nlegs = sum(1 for o in vl.objects if o.type == 'MESH')
select(lg); bpy.ops.tiow.mirror_part(); print("     ", T._state["last"])
lg2 = next((o for o in T._descendants(t_var) if o.type == 'MESH' and on(o) == "Waist"), None)
ck("mirror legs: still on the Waist", lg2 is not None and lg2 is not lg if lg2 else False)
ck("mirror legs: a plain mirror (30-Legs-3 has no copy)", lg2 is not None and str(lg2.get("tiow_orig")).endswith("-Mirrored"), lg2 and lg2.get("tiow_orig"))
ck("mirror legs: no part lost", sum(1 for o in vl.objects if o.type == 'MESH') == nlegs)

# ---- 4. a loose torso flipped where it stands keeps its arms on the same shoulders
select(t_m); bpy.ops.tiow.mirror_part(); print("     ", T._state["last"])
tm2 = vl.objects.active
arm = next((o for o in vl.objects if o.type == 'MESH' and o.get("tiow_orig") == "106-Arm-7-R-A" and T._model_root(o) is tm2), None)
ck("mirror torso: the right arm is still on Shoulder R of the flipped torso", arm is not None and on(arm) == "Shoulder R", arm and on(arm))

V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.25), "back": (-0.3, -1, 0.2)}
for nm, root in (("ref", t_ref), ("var", t_var)):
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "variants_" + nm, obs, V, [rend.ORANGE if o.get("tiow_variant") is not None else rend.GREY for o in obs])
print("\nFAILS:", fails)
