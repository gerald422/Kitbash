"""Stage 4 pads, Josh's two-guide split (Nov 26, notes 171): "combine the general guide with a maker/type guide. so the
existing one sets how the pauldron sits and the second sets where its placed on the arm".

    BL kits/seat/make_pad_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME
  BL = blender --background --factory-startup --python

From his Nov 23 seat file (`Pauldron adapter - seat and cut (2026-11-23).blend`): one column per arm type, with
Torso 2, the spacer and the arm as written in stage 3 (locked), and
- the guide where he seated it on that arm (`Adapter - <arm>`): he moves it (it turns about its crown, the guide's own
  origin); its place is the arm's Pad R socket (and Pad L), shared by every arm of that type (same-shape transfer);
- that type's pauldron in the guide as he placed it there: movable in the first column it appears in (its place in
  the guide is the pad's Pad R fit, the general guide), locked where it repeats or is already his (Shoulder Pad 1).
Pauldrons in his guide master (`Pauldron adapter`, Nov 22) with no arm type yet get a column on Arm 2B R's written
guide (locked), the pad movable. Arms that are left-only sculpts (Marta Gurls Arm 4 Cloth) are left for later."""
import os, sys, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B, make_torso_batch as MT
from kb import sidecar as SC

SPRINGLES = {"patternC ranged Rarm 1": "Pattern C - Ranged Arm 1 R", "patternP ranged Rarm 1": "Pattern P - Ranged Arm 1 R",
             "patternS ranged Rarm 1": "Pattern S - Ranged Arm 1 R",       # seat-file names -> library stems (_sources.csv)
             "TN Mk10 2.0 Arm Right A 1": "TN Mk10 Assault - Arm A1 R", "TN Mk7 Arm Single A 1": "TN Mk7-8 Assault - Mk7 Arm Single A1"}
NOT_IN_LIB = {"Pauldron A 1": "TN Mk10 Assault - Pauldron Assault 1"}   # from the new cults download, not in the library:
                                                                       # shown by this pad's place in the guide master instead
_stems = None


def rel_of(name):
    """the library path of a part from its object name in the seat file (the STL's stem)"""
    global _stems
    if _stems is None:
        _stems = {}
        for p in glob.glob(os.path.join(MT.LIB, "*", "**", "*.stl"), recursive=True):
            r = os.path.relpath(p, MT.LIB).replace("\\", "/")[:-4]
            if not r.startswith("_"): _stems.setdefault(os.path.basename(r), []).append(r)
    stem = name.split(" (in adapter")[0]
    if stem in SPRINGLES: stem = next((s for s in _stems if s.endswith(SPRINGLES[stem])), stem)
    hits = _stems.get(stem, [])
    return hits[0] if len(hits) == 1 else None


def main(A):
    spec_out, blend_out, name = A[0], A[1], A[2]
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(MT.SRC["seat"]), load_ui=False); bpy.context.view_layer.update()
    ob = bpy.data.objects
    adapters = sorted(o.name for o in ob if o.name.startswith("Adapter - "))
    master = [c.name for c in ob["Pauldron adapter"].children]
    objs = [{"id": "ref", "role": "host", "name": "REFERENCE Torso 2 (locked)", "rel": MT.T2, "pose": {"place": True}, "at": [0, 0, 0]}]
    objs += MT.column("ref", "REF ", None, locked=True)
    log, seen = [], set()
    pad_done = lambda rel: "Pad R" in (B.sidecar(MT.LIB, rel).get("exact") or [])

    def base(k, short, arm_rel):
        tid = "a%d" % k; at = [MT.GAP * (k % MT.PER_ROW), 0, -MT.ROW_GAP * (k // MT.PER_ROW)]
        o = [{"id": tid, "role": "host", "name": "Torso 2 for " + short, "rel": MT.T2, "pose": {"place": True}, "at": at},
             {"id": tid + "_spacer", "role": "check", "name": short + " Spacer", "connector": {"kind": "spacer", "from": "arms", "obj": "Springles Spacer"},
              "parent": tid, "on": "Shoulder R", "mirror": True, "pose": {"at_pivot": True, "shift_from": [MT.T2, "Shoulder R"]}},
             {"id": tid + "_arm", "role": "check", "name": short + " (locked)", "rel": arm_rel, "parent": tid + "_spacer", "on": "arm seat", "mirror": True, "pose": {"fit": "Shoulder R"}}]
        for sock, pid, ref_obj, prel, c, joint in MT.PIECES:
            o.append({"id": "%s_%s" % (tid, pid), "role": "neighbour" if pid == "head" else "check", "name": short + " " + ref_obj.split(" - ")[-1],
                      "rel": prel, "parent": tid, "on": sock, "pose": {"fit": sock}})
        return tid, o

    def pad_entry(tid, pad_obj, pad_rel, pose, short):
        free = pad_rel not in seen and not pad_done(pad_rel); seen.add(pad_rel)
        e = {"id": tid + "_pad", "role": "part" if free else "check", "name": "%s %s%s" % (short, os.path.basename(pad_rel), "" if free else " (locked)"),
             "rel": pad_rel, "parent": tid + "_guide", "on": "crown", "mirror": True, "joint": "Pad in the guide", "pose": pose}
        if free:
            e.update(write={"host": tid + "_arm", "socket": "Pad R", "half": "fit"},
                     note="this pauldron in the general guide: move it so it sits right; its place in the guide is its fit for every arm")
        return e, ("pad movable (its fit)" if free else "pad locked (%s)" % ("already yours" if pad_done(pad_rel) else "fitted in an earlier column"))

    k = 1
    for an in adapters:
        arm_name = an[len("Adapter - "):]
        if arm_name not in ob: log.append("%-40s no arm object: left out" % arm_name); continue
        arm_rel = rel_of(arm_name); kids = [c for c in ob[an].children if c.type == "MESH"]
        if ob[arm_name].get("kb_mirrored"): log.append("%-40s a left arm mirrored in the seat file: left for later" % arm_name); continue
        if not arm_rel or "Shoulder R" not in (B.sidecar(MT.LIB, arm_rel).get("exact") or []):
            log.append("%-40s %s: left out" % (arm_name, "not found in the library" if not arm_rel else "no written Shoulder R fit")); continue
        if len(kids) != 1: log.append("%-40s its pad in the guide not found: left out" % arm_name); continue
        pad_name = kids[0].name; pose = {"from": "seat", "obj": pad_name, "relative_to": [an, None]}
        sub = NOT_IN_LIB.get(pad_name.split(" (in adapter")[0])
        if sub: pad_name = sub; pose = {"from": "seat", "obj": sub, "relative_to": ["Pauldron adapter", None]}
        pad_rel = rel_of(pad_name); short = os.path.basename(arm_rel)
        if not pad_rel: log.append("%-40s its pad not in the library: left out" % arm_name); continue
        tid, o = base(k, short, arm_rel)
        ref = arm_rel == MT.ARM                       # Arm 2B R: its Pad R is Josh's (stage 1), locked
        g = {"id": tid + "_guide", "role": "check" if ref else "part", "name": short + " Guide (Pad R)" + (" (locked)" if ref else ""),
             "connector": MT.GUIDE, "parent": tid + "_arm", "on": "self", "mirror": True, "joint": "Guide on the arm (Pad R)",
             "pose": {"from": "seat", "obj": an, "relative_to": [arm_name, tid + "_arm"]}}
        if not ref:
            g.update(write={"host": tid + "_arm", "socket": "Pad R", "mirror": "Pad L", "half": "socket"},
                     note="your guide seat for this arm type (Nov 23): move it so the guide sits right on the shoulder; its place is the Pad R of every arm of this type")
        pose["relative_to"][1] = tid + "_guide"
        p, said = pad_entry(tid, pad_name, pad_rel, pose, short)
        if sub: said += "; %s isn't in the library: %s shown instead" % (kids[0].name.split(" (in adapter")[0], os.path.basename(pad_rel))
        objs += o + [g, p]; k += 1
        log.append("%-40s guide %s; %s" % (short[:40], "locked (yours, stage 1)" if ref else "movable (Pad R)", said))
    for pn in master:
        if pn in NOT_IN_LIB: continue                                 # pauldron types with no arm type yet: on Arm 2B R's written guide
        pad_rel = rel_of(pn)
        if not pad_rel: log.append("%-40s (guide master) not found in the library: left out" % pn); continue
        if pad_rel in seen: continue
        tid, o = base(k, os.path.basename(MT.ARM) + " / " + os.path.basename(pad_rel), MT.ARM)
        g = {"id": tid + "_guide", "role": "check", "name": "Arm 2B R Guide (locked)", "connector": MT.GUIDE, "parent": tid + "_arm",
             "on": "Pad R", "mirror": True, "pose": {"at_pivot": True, "shift_from": [MT.ARM, "Pad R"]}}
        p, said = pad_entry(tid, pn, pad_rel, {"from": "seat", "obj": pn, "relative_to": ["Pauldron adapter", tid + "_guide"]}, os.path.basename(pad_rel))
        objs += o + [g, p]; k += 1
        log.append("%-40s on Arm 2B R's guide; %s" % (os.path.basename(pad_rel)[:40], said))
    spec = {"name": name, "stage": "4 (arms' sockets): pads", "out": blend_out, "sources": MT.SRC,
            "about": "One column per arm type: move the guide (where it sits on this arm type: Pad R) and, where it is free, the pauldron in the guide (how it sits: its fit).",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
