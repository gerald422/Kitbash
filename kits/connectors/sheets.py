"""read only: per part type, a sheet of small marines built from a proving run's numbers alone: the reference marine
(the run's reference parts) with only the tested part swapped in, its name and result under it. Two sheets per type:
working (every joint it takes part in sure, no note) and flagged (placed but near / noted). Parts with nothing placed
are listed only. Saves PNGs and a text list, nothing else.
blender -b --factory-startup --python kits/connectors/sheets.py -- DIR/results.json DIR [per_sheet] [--base OTHER/results.json] [--types Arms,Melee]
(after a prove.py run; --base: a run whose reference parts stand in for the types this run did not search, e.g. its torso)"""
import bpy, os, sys, json, math, collections
import numpy as np
from mathutils import Matrix, Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", ".."))); sys.path.insert(0, HERE)
import seat as S
A = sys.argv[sys.argv.index("--") + 1:]; BASE = A[A.index("--base") + 1] if "--base" in A else None
TYPES = A[A.index("--types") + 1].split(",") if "--types" in A else None
A = [a for i, a in enumerate(A) if a not in ("--base", "--types") and not (i and A[i - 1] in ("--base", "--types"))]; res, outdir = A[0], A[1]; PER = int(A[2]) if len(A) > 2 else 16
D = json.load(open(res, encoding="utf-8")); R = D["results"]; lib = "D:/Kitbash Library"
M4 = lambda a: np.array(a, float).reshape(4, 4); MX = np.diag([-1.0, 1, 1, 1])
by = collections.defaultdict(list)
for r in R:
    if r.get("side") != "L": by[r["cat"]].append(r)          # right parts (a left file is its right twin mirrored)
refrels = {c["part"] for j in D["reference"].values() for k in ("hosts", "children") for c in j[k]}
base_by = collections.defaultdict(list)
if BASE:
    B = json.load(open(BASE, encoding="utf-8"))
    for r in B["results"]: base_by[r["cat"]].append(r)
    refrels |= {c["part"] for j in B["reference"].values() for k in ("hosts", "children") for c in j[k]}
def J(r, jk): return (r or {}).get("joints", {}).get(jk) or {}
def mat(r, jk): d = J(r, jk); return M4(d["matrix"]) if "matrix" in d else None
def good(d): return d.get("level") == "sure" and not d.get("note") and "matrix" in d
def ref(cat, need):
    """the reference part of a type (the run lists the reference's parts first), else the first whose joints are good"""
    xs = by.get(cat) or base_by.get(cat, [])
    for r in sorted(xs, key=lambda r: r["rel"] not in refrels):
        if all(good(J(r, k)) for k in need): return r
    return None
REF = {"Chests": ref("Chests", ["shoulder:host", "neck:host", "waist:host", "back:host"]), "Arms": ref("Arms", ["shoulder:child", "pad:host", "wrist:host"]),
       "Legs": ref("Legs", ["waist:child", "shin:host"]), "Heads": ref("Heads", ["neck:child"]), "Backpacks": ref("Backpacks", ["back:child"]),
       "Shoulder Pads": ref("Shoulder Pads", ["pad:child"]), "Knee Pads": ref("Knee Pads", ["shin:child"]), "Melee": ref("Melee", ["wrist:child"])}
print("reference marine:", {k: os.path.basename(v["rel"]) if v else None for k, v in REF.items()})
HOSTED = {"Chests": [], "Arms": ["shoulder:child", "pad:host", "wrist:host"], "Legs": ["waist:child", "shin:host"], "Heads": ["neck:child"],
          "Jump Packs": ["back:child"], "Backpacks": ["back:child"], "Melee": ["wrist:child"], "Pistols": ["wrist:child"], "Hands": ["wrist:child"],
          "Shields": ["wrist:child"], "Shoulder Pads": ["pad:child"], "Knee Pads": ["shin:child"]}
HOSTED["Chests"] = ["shoulder:host", "neck:host", "waist:host", "back:host"]
TWOH = ("Two-Handed Guns", "Two-Handed Melee", "Heavy Weapons")     # two-armed parts: both arms in one, on the right shoulder (Nov 20)
for t in TWOH: HOSTED[t] = ["shoulder:child"]
def status(r):
    """'ok' / 'flag' / 'none' (nothing of it placed) and a short reason"""
    ks = HOSTED[r["cat"]]; why = []; placed = False
    if r.get("error"): return "none", "error"
    for k in ks:
        d = J(r, k)
        if k == "shin:host":
            for sn, sd in sorted((d.get("sides") or {}).items()):
                if "matrix" in sd: placed = True
                if not ("matrix" in sd and not sd.get("note")): why.append("%s %s%s" % (sn, sd.get("level"), " (noted)" if sd.get("note") else ""))
            if not d.get("sides"): why.append("shin none")
            continue
        if "matrix" in d: placed = True
        if not good(d): why.append("%s %s%s" % (k.split(":")[0], d.get("level", "none"), " (noted)" if d.get("note") else ""))
        if k == "waist:child" and d.get("buckle", {}).get("level") not in ("sure",): why.append("buckle %s" % d.get("buckle", {}).get("level"))
    if r["cat"] in ("Arms", "Legs") and "matrix" not in J(r, ks[0]): placed = False   # it hangs nowhere
    if r["cat"] == "Chests": placed = placed
    st = "ok" if not why else ("flag" if placed else "none")
    return st, ", ".join(why)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
cache = {}
def put(rel, Wm, coll):
    sc, G, back = S.maker(lib + "/" + rel + S.SC.SUFFIX)
    if rel not in cache:
        bpy.ops.wm.stl_import(filepath=lib + "/" + rel + ".stl"); o = bpy.context.selected_objects[0]
        for c in list(o.users_collection): c.objects.unlink(o)
        cache[rel] = o.data
    o = bpy.data.objects.new(os.path.basename(rel)[:60], cache[rel]); coll.objects.link(o)
    o.matrix_world = Matrix((Wm if back is None else Wm @ back).tolist()); return o
def label(text, x, z, coll, size=1.7):
    cu = bpy.data.curves.new("t", "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = bpy.data.objects.new("label", cu); coll.objects.link(o); o.location = (x, 30, z); o.rotation_euler = (math.pi / 2, 0, math.pi); return o
def marine(r, W, coll):
    """the reference marine with r swapped in; joints placed only where both sides have numbers"""
    cat = r["cat"]; pick = lambda c: r if cat == c else REF.get(c)
    if cat in ("Melee", "Pistols", "Hands", "Shields"): weapon = r
    else: weapon = REF["Melee"]
    torso = pick("Chests"); put(torso["rel"], W, coll)
    def hang(child, jn, Wh, host):
        Sx, F = mat(host, jn + ":host"), mat(child, jn + ":child")
        if child is None or Sx is None or F is None: return None
        Wc = Wh @ Sx @ F; placed.append(put(child["rel"], Wc, coll)); return Wc
    placed = []; Wa = hang(r if cat in TWOH else pick("Arms"), "shoulder", W, torso); arm_objs = placed[:]
    if cat in TWOH: Wa = None                                    # it is both arms: no pad, weapon or mirrored left arm
    if cat in ("Chests", "Legs", "Knee Pads") or True: Wl = hang(pick("Legs"), "waist", W, torso)
    hang(pick("Heads"), "neck", W, torso)
    pack = r if cat in ("Jump Packs", "Backpacks") else REF.get("Backpacks"); hang(pack, "back", W, torso)
    if Wa is not None:
        n0 = len(placed); hang(pick("Shoulder Pads"), "pad", Wa, pick("Arms")); hang(weapon, "wrist", Wa, pick("Arms")); arm_objs += placed[n0:]
        # the left arm, its pad and weapon: the right ones mirrored about the torso's waist frame (+X = the right, as
        # for the left shin pad; Josh, Nov 18: left arms are right arms mirrored, so the sheets show both)
        Sw = mat(torso, "waist:host")
        if Sw is not None:
            Mw = Matrix((W @ Sw @ MX @ np.linalg.inv(Sw) @ np.linalg.inv(W)).tolist())
            for o in arm_objs:
                m = bpy.data.objects.new(o.name[:56] + " L", o.data); coll.objects.link(m); m.matrix_world = Mw @ o.matrix_world
    if Wl is not None:
        legs, pad = pick("Legs"), pick("Knee Pads")
        if hang(pad, "shin", Wl, legs) is not None:
            o = J(legs, "shin:host").get("other")
            if o and "matrix" in o: put(pad["rel"], Wl @ M4(o["matrix"]) @ MX @ mat(pad, "shin:child"), coll)
def render(coll_objs, name):
    sc = bpy.context.scene
    for o in sc.collection.objects: pass
    bpy.context.view_layer.update(); pts = [o.matrix_world @ Vector(c) for o in coll_objs if o.type in ("MESH", "FONT") for c in o.bound_box]
    if not pts: return
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)]); lo.z -= 2; mid = (lo + hi) / 2
    cam = sc.camera; ext = hi - lo
    dv = Vector((0, -1, 0))                    # the camera in front (+Y), looking back: as in the earlier renders
    cam.location = mid - dv * 900; cam.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = max(ext.x, ext.z * sc.render.resolution_x / sc.render.resolution_y) * 1.04
    sc.render.filepath = os.path.join(outdir, name + ".png"); bpy.ops.render.render(write_still=True)
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "RANDOM"; sc.display.shading.show_cavity = True
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"; cam.data.clip_end = 5000
lines = []; COLS = 8; DX, DZ = 46.0, 78.0
def spread(xs, n):
    if len(xs) <= n: return xs
    return [xs[int(round(i * (len(xs) - 1) / (n - 1)))] for i in range(n)]
for cat in ["Chests", "Arms", "Legs", "Heads", "Jump Packs", "Backpacks", "Shoulder Pads", "Knee Pads", "Melee", "Pistols", "Hands", "Shields"] + list(TWOH):
    if TYPES and cat not in TYPES: continue
    xs = sorted(by.get(cat, []), key=lambda r: r["rel"]); st = {r["rel"]: status(r) for r in xs}
    cnt = collections.Counter(s for s, _ in st.values())
    lines.append("== %s: %d parts: %d working, %d flagged (placed), %d not placed" % (cat, len(xs), cnt["ok"], cnt["flag"], cnt["none"]))
    for r in xs:
        if st[r["rel"]][0] != "ok": lines.append("   %-5s %-60s %s" % (st[r["rel"]][0], os.path.basename(r["rel"])[:60], st[r["rel"]][1]))
    for kind in ("ok", "flag"):
        chosen = spread([r for r in xs if st[r["rel"]][0] == kind], PER)
        if not chosen: continue
        for view, turn in (("front", 0.0), ("side", 90.0)):   # side: each marine turned so its right side faces the camera
            coll = bpy.data.collections.new(cat + " " + kind + " " + view); sc.collection.children.link(coll)
            for i, r in enumerate(chosen):
                W = np.eye(4); W[0, 3] = -DX * (i % COLS); W[2, 3] = -DZ * (i // COLS)
                Rz = np.eye(4); t = math.radians(turn); Rz[:2, :2] = [[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]
                before = set(coll.objects); marine(r, W @ Rz, coll); bpy.context.view_layer.update()
                zmin = min((o.matrix_world @ Vector(c)).z for o in coll.objects if o not in before and o.type == "MESH" for c in o.bound_box)
                nm = os.path.basename(r["rel"]).replace("MarFil ", "")[:34]
                label(nm + ("" if kind == "ok" else "\n" + st[r["rel"]][1][:40]), W[0, 3], zmin - 5, coll)
            cols = min(COLS, len(chosen)); rows = (len(chosen) + cols - 1) // cols
            sc.render.resolution_x = min(3000, 375 * cols); sc.render.resolution_y = int(sc.render.resolution_x * rows * DZ / (cols * DX)) + 60
            for c in sc.collection.children: c.hide_render = c is not coll
            render(list(coll.objects), "%s %s %s" % (cat, "working" if kind == "ok" else "flagged", view))
            for o in list(coll.objects): bpy.data.objects.remove(o)
        lines.append("   sheet %s %s: %s" % (cat, kind, ", ".join(os.path.basename(r["rel"]).replace("MarFil ", "") for r in chosen)))
open(os.path.join(outdir, "sheets.txt"), "w", encoding="utf-8").write("Reference marine: %s\n\n" % {k: os.path.basename(v["rel"]) if v else None for k, v in REF.items()} + "\n".join(lines) + "\n")
print("\n".join(l for l in lines if l.startswith("==")))
