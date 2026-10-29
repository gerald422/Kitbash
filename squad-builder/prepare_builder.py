"""Get the Kitbash Library ready for the Squad Builder page, in one run.

    blender --background --python prepare_builder.py -- "D:\\Kitbash Library" [--budget SECONDS] [--skip-anchors]

1. Anchors: some anchors are only found the first time Blender brings a part
   in (an arm's wrist socket and pauldron points, a legs piece's shin
   anchors, a hand-held weapon's grip). Each arm, legs piece and hand-held
   part is brought in once through TIOW Inbox's own rules, with nothing
   selected so nothing snaps, and what they find is saved in its
   .sockets.json (a mirror copy's go in its own entry). Done parts are listed
   in _builder/anchors_done.txt.
2. Previews and index: a light copy of every part's mesh (Blender's own
   Decimate, about 6,000 triangles) in _builder/previews, and
   _builder/index.json listing every part with its sockets and fits.

Run it again any time: only new or changed parts are done. --budget stops
after that many seconds (run again to carry on). Blender stays closed to you
while it runs (it's a background run); your open scenes aren't touched.
Needs Part Sockets and TIOW Inbox 1.17 enabled in Blender's preferences.
"""
import csv
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
LIB = argv[0] if argv else r"D:\Kitbash Library"
SKIP_ANCHORS = "--skip-anchors" in argv
BUDGET = float(argv[argv.index("--budget") + 1]) if "--budget" in argv else 1e9

for mod in ("part_sockets", "tiow_inbox"):
    try:
        bpy.ops.preferences.addon_enable(module=mod)
    except Exception:         # an extension install has its own module name; tiow_inbox finds it either way
        pass
import tiow_inbox as T        # noqa: E402

prefs = T.get_prefs()
prefs.listening = False       # don't pick up TIOW requests while this runs
HANDS = {c for c, s in T.DEFAULT_JOINTS.items() if s.get("socket") == "Hand" and s.get("sided")}
WANT = {"Arms", "Legs"} | HANDS

done_path = os.path.join(LIB, "_builder", "anchors_done.txt")
os.makedirs(os.path.dirname(done_path), exist_ok=True)
done = set(open(done_path, encoding="utf-8").read().splitlines()) if os.path.exists(done_path) else set()
rows = list(csv.DictReader(open(os.path.join(LIB, "_sources.csv"), encoding="utf-8-sig")))
t0 = time.time()
n = made = 0
log = open(done_path, "a", encoding="utf-8")


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)


for r in ([] if SKIP_ANCHORS else rows):
    if time.time() - t0 > BUDGET:
        break
    rel = r["library path"]
    path = os.path.join(LIB, rel.replace("\\", os.sep))
    if not os.path.isfile(path):
        continue
    side = T.read_sidecar(path) or {}
    cat = str(side.get("category") or r.get("type") or "")
    if cat not in WANT:
        continue
    which = [None] + [i for i, v in enumerate(T.part_variants(side))
                      if isinstance(v, dict) and not v.get("duplicate") and not v.get("synth")]
    for vi in which:
        key = rel + ("" if vi is None else f"#{vi}")
        if key in done:
            continue
        clear()
        job = {"path": path, "category": cat, "name": os.path.splitext(os.path.basename(path))[0],
               "_variant": vi, "_nosnap": True}
        try:
            new = T.import_request(job, prefs)
            part = next(o for o in new if o.type == 'MESH')
            if cat == "Legs":
                for s in [c for c in part.children if c.get("ws_type") in ("Shin R", "Shin L")]:
                    if s.get("tiow_anchor") == "auto":
                        T.remember_anchor(part, s)
                        made += 1
            elif cat in HANDS:
                sd = T.part_side(T._pname(part), T._pfolder(part)) or \
                    T._side_with_mirrored(T._pname(part), T._pfolder(part))
                if sd:
                    note, _med = T.rule_hand_fit(part, sd)
                else:
                    note = T.hand_side_by_rule(part) or ""
                made += bool(note)
            note = (job.get("_found") or "").strip(", ")
            print(f"[anchors] {key}: {note or 'ok'}")
        except Exception as exc:      # one bad part is logged, not a stopped batch
            print(f"[anchors] {key}: FAILED {exc!r}")
        log.write(key + "\n")
        log.flush()
        n += 1
clear()
print(f"[anchors] {n} parts done this run, {made} anchors or grips saved")


def blender_preview(stl, k, target):
    """A light copy of the part's mesh: Blender's Decimate on the imported STL."""
    import numpy as np
    before = set(bpy.data.objects)
    with bpy.context.temp_override(**T._view3d_override()):
        bpy.ops.wm.stl_import('EXEC_DEFAULT', filepath=stl)
    ob = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    try:
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        if tris > target:
            mod = ob.modifiers.new("preview", 'DECIMATE')
            mod.ratio = max(0.001, target / tris)
        dg = bpy.context.evaluated_depsgraph_get()
        me = ob.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V)
        Tr = np.empty(len(me.loop_triangles) * 3, dtype=np.int32); me.loop_triangles.foreach_get("vertices", Tr)
        ob.evaluated_get(dg).to_mesh_clear()
        return V.reshape(-1, 3) * k, Tr.reshape(-1, 3)
    finally:
        me_ = ob.data
        bpy.data.objects.remove(ob)
        if me_.users == 0:
            bpy.data.meshes.remove(me_)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index    # noqa: E402  (beside this script)
left = BUDGET - (time.time() - t0)
todo = build_index.build(LIB, budget=max(0.0, left), preview_fn=blender_preview) if left > 0 else -1
if time.time() - t0 > BUDGET or todo:
    print("[prepare] stopped at the time limit - run it again to carry on")
else:
    print("[prepare] all done: open Squad Builder.html")
