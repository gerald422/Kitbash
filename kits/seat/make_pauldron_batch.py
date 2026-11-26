"""Stage 4 pads, Josh's plan (Nov 26, notes 172): "place every pauldron onto a single arm ... get everything set on the
placement pad as it already is", all in one file "to make sure the fit is good across all of them at the same time".
Then one more file with each arm type once (the arm's Pad R, from his shoulder cuts: setup only).

    BL kits/seat/make_pauldron_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME
  BL = blender --background --factory-startup --python

Every shoulder pauldron in scope (category Shoulder Pads; not hidden, not Terminator / Gravis / Phobos / Old Style /
Rigging Required) gets a column: Torso 2, the spacer, Arm 2B R by its written fit and the guide on its written Pad R
(stage 1, Josh's), all locked and sharing one mesh each; the pauldron in the guide, which Josh moves. Its place in the
guide is its Pad R fit (the general guide: how it sits, the same on every arm). Left-only pauldrons show as their
mirror image and are written as their Pad L fit (as the left arms, notes 147).
Where it starts (Josh: "use the fit as we have it obviously and then hopefully its just adjustments"):
1. his Nov 22 placement on the guide master, for the 15 he placed;
2. else its own library fit (Pad R, or Pad L for a left-only one, mirrored): where it sat on Arm 2B R's old Pad R
   (the Nov 20 pad spot socket, backup `batch write 2026-11-24 1723`), carried into the guide;
3. else a kit-mate's (Mar Fil) or same maker's Nov 22 placement, else Shoulder Pad 1's, moved so its bounding-box
   centre sits where that pauldron's does (files of a kit share a frame).
Shoulder Pad 1 itself is already his (stage 1): the first column, locked."""
import os, sys, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B, make_torso_batch as MT, make_pad_batch as MP

OUT = ("Gravis", "Phobos", "Terminator", "Old Style")
MX = np.diag([-1.0, 1, 1, 1])
GAP, PER_ROW, ROW_GAP = 60.0, 20, 80.0


def kit(rel):
    parts = rel.split("/")
    return (parts[0], parts[1]) if parts[0].startswith("Mar Fil") else (parts[0], "")


def main(A):
    spec_out, blend_out, name = A[0], A[1], A[2]
    lib = MT.LIB
    hidden = set(l.strip().replace("\\", "/")[:-4] for l in open(os.path.join(lib, "_hidden.txt"), encoding="utf-8-sig") if l.strip().endswith(".stl"))
    pads = []
    for p in sorted(glob.glob(os.path.join(lib, "*", "**", "*.sockets.json"), recursive=True)):
        rel = os.path.relpath(p, lib).replace("\\", "/")[:-13]
        if rel.startswith("_") or any(o in rel.split("/")[0] for o in OUT) or "rigging required" in rel.lower() or rel in hidden: continue
        d = json.load(open(p, encoding="utf-8-sig"))
        if d.get("category") != "Shoulder Pads": continue
        f = d.get("fits") or {}
        pads.append((rel, "Pad L" in f and "Pad R" not in f, "Pad R" in (d.get("exact") or [])))
    # his Nov 22 placements on the guide master: pauldron own -> crown, by kit / maker
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(MT.SRC["seat"]), load_ui=False); bpy.context.view_layer.update()
    ob = bpy.data.objects; Wg = np.array(ob["Pauldron adapter"].matrix_world)      # the guide's own frame = its crown
    reps = {}
    for c in ob["Pauldron adapter"].children:
        r = MP.rel_of(c.name)
        if not r: continue
        F = np.linalg.inv(Wg) @ B.own_world(c, r, lib, B.sidecar(lib, r))
        V = B.stl_tris(lib, r, B.sidecar(lib, r)).reshape(-1, 3); reps.setdefault(kit(r), (F, (V.min(0) + V.max(0)) / 2, r))
        reps.setdefault((kit(r)[0], ""), reps[kit(r)])
    default = reps[kit(MT.PAD)]
    mine = {MP.rel_of(c.name): np.linalg.inv(Wg) @ B.own_world(c, MP.rel_of(c.name), lib, B.sidecar(lib, MP.rel_of(c.name)))
            for c in ob["Pauldron adapter"].children if MP.rel_of(c.name)}
    old = json.load(open(os.path.join(lib, "_backups", "batch write 2026-11-24 1723", "before", "lib", MT.ARM + ".sockets.json"), encoding="utf-8-sig"))
    S_old = G.M4(next(s["matrix"] for s in old["sockets"] if s["type"] == "Pad R")); S_new = MT.sockets(MT.ARM)["Pad R"]
    C = np.linalg.inv(S_new) @ S_old                  # old pad frame -> the guide's crown, on Arm 2B R
    objs, log = [], []
    shown = sorted(pads, key=lambda t: (t[0] != MT.PAD, t[0]))
    for k, (rel, left, done) in enumerate(shown):
        tid = "p%d" % k; short = os.path.basename(rel)
        at = [GAP * (k % PER_ROW), 0, -ROW_GAP * (k // PER_ROW)]
        objs += [{"id": tid, "role": "host", "name": "Torso 2 for " + short, "rel": MT.T2, "pose": {"place": True}, "at": at},
                 {"id": tid + "_spacer", "role": "check", "name": short + " Spacer", "connector": {"kind": "spacer", "from": "arms", "obj": "Springles Spacer"},
                  "parent": tid, "on": "Shoulder R", "pose": {"at_pivot": True, "shift_from": [MT.T2, "Shoulder R"]}},
                 {"id": tid + "_arm", "role": "check", "name": short + " Arm 2B R", "rel": MT.ARM, "parent": tid + "_spacer", "on": "arm seat", "pose": {"fit": "Shoulder R"}},
                 {"id": tid + "_guide", "role": "check", "name": short + " Guide", "connector": MT.GUIDE, "parent": tid + "_arm", "on": "Pad R",
                  "pose": {"at_pivot": True, "shift_from": [MT.ARM, "Pad R"]}}]
        e = {"id": tid + "_pad", "role": "check" if done else "part", "name": short + (" (mirrored, as a right pauldron)" if left else "") + (" (yours, locked)" if done else ""),
             "rel": rel, "parent": tid + "_guide", "on": "crown", "joint": "Pauldron in the guide"}
        if done: e["pose"] = {"fit": "Pad R"}; how = "already yours (locked)"
        else:
            fits = B.sidecar(lib, rel).get("fits") or {}
            if rel in mine and not left: start = mine[rel]; how = "your Nov 22 placement"
            elif left and "Pad L" in fits: start = C @ MX @ G.M4(fits["Pad L"]) @ MX; how = "its own Pad L fit, mirrored"
            elif not left and "Pad R" in fits: start = C @ G.M4(fits["Pad R"]); how = "its own Pad R fit"
            else:
                F, c_rep, r_rep = reps.get(kit(rel)) or reps.get((kit(rel)[0], "")) or default
                V = B.stl_tris(lib, rel, B.sidecar(lib, rel)).reshape(-1, 3)
                if left: V = V * np.array([-1.0, 1, 1])
                c = (V.min(0) + V.max(0)) / 2; T = np.eye(4); T[:3, 3] = c_rep - c
                start = F @ T; how = "no fit: starts like %s" % os.path.basename(r_rep)
            e["pose"] = {"in_pivot": G.flat16(start)}
            e["write"] = {"host": tid + "_arm", "socket": "Pad R", "half": "fit"}
            if left: e["mirror_mesh"] = True; e["write"]["left"] = "Pad L"
            else: e["write"]["mirror"] = "Pad L"
            e["note"] = "move the pauldron in the guide so it sits right; its place is its fit on every arm (starts from %s)" % how
        objs.append(e); log.append("%-52s %s%s" % (short[:52], how, ", left-only: mirrored" if left else ""))
    spec = {"name": name, "stage": "4 (arms' sockets): pauldrons in the guide", "out": blend_out, "sources": MT.SRC,
            "about": "Every pauldron in the guide on Arm 2B R (locked, as written in stage 1): move each pauldron so it sits right. Its place in the guide is its fit on every arm.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("%d pauldrons (%d left-only, %d already yours)" % (len(pads), sum(1 for p in pads if p[1]), sum(1 for p in pads if p[2])))
    print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
