"""Every pauldron's origin onto the shell (Nov 28, Josh: "every single pauldron has now been hand checked. lets go
ahead and move the origins"; notes 174).

    BL kits/seat/pads_origin.py -- plan ONE_ARM.blend PLAN.json
    BL kits/seat/pads_origin.py -- write PLAN.json [--yes]          (without --yes: the report only, nothing written)
    BL kits/seat/pads_origin.py -- check ONE_ARM.blend PLAN.json    (after the write: each pauldron from the library)
    restore: BL kits/connectors/origins.py -- restore origins-pads-<date> [--yes]
  BL = blender --background --factory-startup --python

ONE_ARM is the file with every pauldron in the one shell on Arm 2B R (kits/seat/one_arm.py), each placed by Josh (or
carried by inner surface and then checked by him). A pauldron's place there against Arm 2B R's written Pad R socket
is its fit F (as batch.write's on_written_socket). New fits only: every older pad fit goes. Then the file itself is
moved by that fit (kb.origin, notes 101): its origin is the shell's crown (2B R's Pad R frame) and the fit becomes
none, the same point and roll for every pauldron. A left-only pauldron (shown mirrored, as a right one) gets Pad L:
moved by MX F MX, so on a left arm (its Pad L = the mirror of the right arm's Pad R) it is the mirror of what Josh set.
A part with a sidecar `scale` moves too (its STL by raw_move: the shift / scale). Written like origins.py: originals
into _backups/origins-pads-<date>/before (STL, sidecar, preview, page index), each new STL checked against the old one
moved, a journal and written.json, so origins.py's restore puts them back. The repo's mirror of each sidecar is
written when it was in step with the library."""
import os, sys, json, time, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
from kb import sidecar as SC, origin as OG

LIB = "D:/Kitbash Library"
ARM = "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 2B R"
SPEC = os.path.join(HERE, "batches", "04-pauldrons-all-d.json")
MX = np.diag([-1.0, 1, 1, 1])
CHECK = 2e-4


def plan(A):
    import bpy
    import geom as G, batch as B
    blend, out = A[1], A[2]
    bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    host = by["p0_arm"]
    moved = np.abs(np.array(host.matrix_world) - G.M4(host["kb_seated"])).max()
    if moved > 1e-5: raise SystemExit("Arm 2B R moved in the file (%.5f): nothing planned" % moved)
    S = G.M4(next(s["matrix"] for s in SC.load(os.path.join(LIB, ARM + SC.SUFFIX))[0]["sockets"] if s["type"] == "Pad R"))
    spec = {e["id"]: e for e in json.load(open(SPEC, encoding="utf-8"))["objects"]}
    rows, bad = [], []
    for i, o in sorted(by.items(), key=lambda kv: int(kv[0].split("_")[0][1:])):
        if not i.endswith("_pad"): continue
        rel = o["kb_rel"]; left = bool(spec[i].get("mirror_mesh"))
        F = np.linalg.inv(S) @ np.linalg.inv(B.own(host)) @ B.own(o)
        k = float(np.cbrt(np.linalg.det(F[:3, :3])))
        if abs(k - 1) > 1e-4: bad.append("%s %s: scaled %.4f in the file, not moved" % (i, o.name, k)); continue
        Gm = MX @ F @ MX if left else F
        sc = json.load(open(os.path.join(LIB, rel + SC.SUFFIX), encoding="utf-8-sig"))
        rows.append(dict(id=i, rel=rel, name=o.name, joint="Pad L" if left else "Pad R", G=G.flat16(Gm), scale=float(sc.get("scale") or 1.0),
                         had=sorted(sc.get("fits") or {}), was_moved=bool(sc.get("origin"))))
    json.dump(dict(file=os.path.basename(blend), made=time.strftime("%Y-%m-%d %H:%M"), rows=rows, bad=bad), open(out, "w", encoding="utf-8"), indent=1)
    d = np.array([[np.linalg.norm(G.M4(r["G"])[:3, 3]), G.ang(np.eye(4), G.M4(r["G"]))] for r in rows])
    print("%d pauldrons: %d right (Pad R), %d left-only (Pad L), %d with a scale, %d already moved once" % (
        len(rows), sum(r["joint"] == "Pad R" for r in rows), sum(r["joint"] == "Pad L" for r in rows), sum(r["scale"] != 1 for r in rows), sum(r["was_moved"] for r in rows)))
    print("origin moves %.1f mm (median; most %.1f), turns %.0f deg (median; most %.0f)" % (np.median(d[:, 0]), d[:, 0].max(), np.median(d[:, 1]), d[:, 1].max()))
    for b in bad: print("  NOT MOVED:", b)
    print("PLAN", out, flush=True)


def md5(p):
    import hashlib; return hashlib.md5(open(p, "rb").read()).hexdigest()


def write(A):
    import shutil
    from kb.index import Index
    P = json.load(open(A[1], encoding="utf-8")); go = "--yes" in A; lib = LIB
    tag = "Josh's seat in '%s' (every pauldron on Arm 2B R's shell, hand checked), %s" % (os.path.splitext(P["file"])[0], time.strftime("%Y-%m-%d"))
    by = "pads_origin.py %s" % time.strftime("%Y-%m-%d")
    todo, left = [], []
    for r in P["rows"]:
        old, style = SC.load(os.path.join(lib, r["rel"] + SC.SUFFIX))
        new = json.loads(json.dumps(old))
        new["fits"] = {r["joint"]: r["G"]}; new["exact"] = [r["joint"]]               # new fits only (Nov 24)
        new.pop("check", None)                       # old fits' "check by eye" list: every one is replaced, all hand checked
        notes = new.get("notes") if isinstance(new.get("notes"), dict) else {}
        notes = {k: v for k, v in notes.items() if not k.startswith("Pad ")}
        notes[r["joint"]] = tag + "; origin moved onto the shell's crown (Arm 2B R's Pad R), so this fit is none"
        new["notes"] = notes
        try: moved, Gs, did = OG.move(new, ["Pad"], r["rel"], by, scaled=True)
        except OG.Skip as e: left.append((r, str(e))); continue
        bad = [x for x in SC.problems(moved) if x not in SC.problems(old)]
        if bad: left.append((r, "the moved sidecar would be wrong: %s" % bad[:2])); continue
        todo.append((r, old, style, moved, Gs))
    print("%d to write, %d left:" % (len(todo), len(left)))
    for r, why in left: print("  LEFT %-60s %s" % (r["name"][:60], why))
    if not go: print("(no --yes: nothing written)"); return
    task = "origins-pads-%s" % time.strftime("%Y-%m-%d"); k = 1
    while os.path.exists(lib + "/_backups/" + task): k += 1; task = "origins-pads-%s-%d" % (time.strftime("%Y-%m-%d"), k)
    T = lib + "/_backups/" + task; Bk = T + "/before"; os.makedirs(Bk)
    def backup(f):
        b = Bk + "/" + f
        if not os.path.exists(b): os.makedirs(os.path.dirname(b), exist_ok=True); shutil.copyfile(lib + "/" + f, b)
    ip = lib + "/_builder/index.json"; idx = Index.load(ip); backup("_builder/index.json")
    J = open(T + "/journal.jsonl", "a", encoding="utf-8"); wrote, failed = {}, []
    for n, (r, old, style, moved, Gs) in enumerate(todo):
        rel = r["rel"]; scp, stl = lib + "/" + rel + SC.SUFFIX, lib + "/" + rel + ".stl"; begun = []
        try:
            e = idx.by_path.get(rel.replace("/", "\\") + ".stl")
            prev = "_builder/" + e["prev"] if e and e.get("prev") and "#" not in e["prev"] and os.path.exists(lib + "/_builder/" + e["prev"]) else None
            backup(rel + SC.SUFFIX)
            J.write(json.dumps({"rel": rel, "state": "start", "stl": Gs is not None, "prev": prev if Gs is not None else None}) + "\n"); J.flush()
            begun = [rel + SC.SUFFIX] + ([rel + ".stl"] + ([prev] if prev else []) if Gs is not None else [])
            if Gs is not None:
                backup(rel + ".stl"); Gr = OG.raw_move(Gs, r["scale"])
                tmp = stl + ".moving"; OG.move_stl(stl, tmp, Gr)
                M = np.array(Gr, float).reshape(4, 4); Pp = OG.stl_points(stl); Q = OG.stl_points(tmp)
                err = float(np.abs(Pp @ M[:3, :3].T + M[:3, 3] - Q).max()) if len(Pp) == len(Q) and len(Pp) else 9e9
                if err > CHECK: os.remove(tmp); raise OG.Skip("the rewritten STL is %.5f mm off" % err)
                os.replace(tmp, stl)
            repo_p = os.path.join(REPO, "library", rel + SC.SUFFIX)
            in_step = os.path.exists(repo_p) and open(repo_p, "rb").read() == open(scp, "rb").read()
            data = SC.save(scp, moved, style)
            if in_step: open(repo_p, "wb").write(data)
            if Gs is not None and prev:
                backup(prev); OG.move_preview(lib + "/" + prev, lib + "/" + prev + ".moving", Gs); os.replace(lib + "/" + prev + ".moving", lib + "/" + prev)
            if e is not None: idx.update_part(e["path"], moved)
            wrote[rel] = {"sc": md5(scp), "stl": md5(stl) if Gs is not None else None, "prev": prev if Gs is not None else None, "repo": in_step}
            J.write(json.dumps({"rel": rel, "state": "done"}) + "\n"); J.flush()
        except (OG.Skip, OSError, ValueError, KeyError) as ex:
            failed.append("%s: %s" % (rel, ex))
            for f in begun:
                if os.path.exists(Bk + "/" + f): shutil.copyfile(Bk + "/" + f, lib + "/" + f)
            if begun: J.write(json.dumps({"rel": rel, "state": "undone"}) + "\n"); J.flush()
        if (n + 1) % 50 == 0: print("  %d of %d" % (n + 1, len(todo)), flush=True)
    open(ip, "wb").write(idx.dumps())
    json.dump({"wrote": wrote, "index": md5(ip)}, open(T + "/written.json", "w", encoding="utf-8"), indent=1)
    print("written %d (%d also in the repo's mirror); failed %d%s; backup %s" % (len(wrote), sum(w["repo"] for w in wrote.values()), len(failed),
          "".join("\n  FAILED " + f for f in failed), T), flush=True)


def check(A):
    import bpy
    import geom as G, batch as B
    blend, P = A[1], json.load(open(A[2], encoding="utf-8"))
    bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}; host = by["p0_arm"]
    S = G.M4(next(s["matrix"] for s in SC.load(os.path.join(LIB, ARM + SC.SUFFIX))[0]["sockets"] if s["type"] == "Pad R"))
    H = B.own(host) @ S; worst = []
    for r in P["rows"]:
        o = by[r["id"]]; sc = SC.load(os.path.join(LIB, r["rel"] + SC.SUFFIX))[0]
        fit = G.M4(sc["fits"][r["joint"]]); idn = float(np.abs(fit - np.eye(4)).max())
        T = B.stl_tris(LIB, r["rel"], sc)                                    # the new file, its scale applied
        if r["joint"] == "Pad L": T = T[:, ::-1] * np.array([-1.0, 1, 1]); fit = MX @ fit @ MX   # shown as the right one
        T = T[::max(1, len(T) // 3000)]
        Wt = G.tris(o); Wt = Wt[::max(1, len(Wt) // 3000)]
        M = np.array(o.matrix_world); Wt = Wt @ M[:3, :3].T + M[:3, 3]
        Lt = T @ (H @ fit)[:3, :3].T + (H @ fit)[:3, 3]
        d = float(np.abs(Lt - Wt).max()) if Lt.shape == Wt.shape else 9e9
        worst.append((d, idn, r["name"]))
    worst.sort(reverse=True)
    print("%d pauldrons placed from the library on Arm 2B R's Pad R against the file: worst %.5f mm; fits off none by at most %.6f"
          % (len(worst), worst[0][0], max(w[1] for w in worst)))
    for d, idn, nm in worst[:5]: print("  %.5f mm  %s" % (d, nm))


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: {"plan": plan, "write": write, "check": check}[A[0]](A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
