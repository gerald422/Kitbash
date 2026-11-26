"""Stage 4 pads, Josh's plan (Nov 26, notes 172): "place every pauldron onto a single arm ... get everything set on the
placement pad as it already is", all in one file "to make sure the fit is good across all of them at the same time".
Then one more file with each arm type once (the arm's Pad R, from his shoulder cuts: setup only).

    BL kits/seat/make_pauldron_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME
  BL = blender --background --factory-startup --python

Every shoulder pauldron in scope (category Shoulder Pads; not hidden, not Terminator / Gravis / Phobos / Old Style /
Rigging Required) gets a column: Torso 2, the spacer and Arm 2B R by its written fit (locked, sharing one mesh each),
the full-size shell on 2B R's written Pad R (Josh: "have the pauldron parented to the shell. Rotate the shell till its
in position. The shell going forward is a used part that sets the placement"), and the pauldron riding on the shell.
He rotates the shell about its crown (or nudges the pauldron in it). The pauldron's place against 2B R's written Pad R
is its Pad R fit, the same on every arm ("on_written_socket"). Left-only pauldrons show as their mirror image and
are written as their Pad L fit (as the left arms, notes 147).
Where each sits in its shell (Josh: "the previous 15 fits ... would cover every style ... apply that to everything
coming from the same pack ... Then if anything is left over use the maker placement"): his Nov 22 placement on the
shell; else that of the pauldron he placed from the same pack (folder); else from the same maker; else Shoulder Pad 1's,
with this pauldron's bounding-box centre put where that one's is (the files of a pack don't share a place, Nov 26).
Shoulder Pad 1 itself is already his (stage 1): the first column, locked."""
import os, sys, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B, make_torso_batch as MT, make_pad_batch as MP

PADS = "~/Desktop/mar fil connectors/Pauldron adapter - part with pads (2026-11-23).blend"   # his Nov 22 placements
SHELL = {"kind": "guide", "from": "pads", "obj": "Pauldron adapter"}     # the full-size shell (same crown frame as the guide)
OUT = ("Gravis", "Phobos", "Terminator", "Old Style")
MX = np.diag([-1.0, 1, 1, 1])
GAP, PER_ROW, ROW_GAP = 60.0, 20, 80.0


def pack(rel): return rel.rsplit("/", 1)[0]          # the folder it came in
def maker(rel): return rel.split("/")[0]


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
    # his Nov 22 placements on the full-size shell: pauldron own -> crown (Josh: "the previous 15 fits ... would cover
    # every style. ... apply that to everything coming from the same pack ... Then if anything is left over use the
    # maker placement")
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(PADS), load_ui=False); bpy.context.view_layer.update()
    ob = bpy.data.objects; Wg = np.array(ob["Pauldron adapter"].matrix_world)
    mine = {}
    for c in ob["Pauldron adapter"].children:
        r = MP.rel_of(c.name)
        if r: mine[r] = np.linalg.inv(Wg) @ B.own_world(c, r, lib, B.sidecar(lib, r))
    by_pack, by_maker = {}, {}
    for r, F in sorted(mine.items()): by_pack.setdefault(pack(r), (F, r)); by_maker.setdefault(maker(r), (F, r))
    objs, log = [], []
    shown = sorted(pads)                            # by path, so by pack (Shoulder Pad 1 sits in its own pack)
    packs = []                                      # by kit (Josh, Nov 26): each pack starts a row, in its own numbered
    for rel, left, done in shown:                   # collection, so he does a few and asks for them on the rest of the kit
        if not packs or packs[-1][0] != pack(rel): packs.append((pack(rel), []))
        packs[-1][1].append((rel, left, done))
    lay = []; row = 0
    for n, (pk, items) in enumerate(packs, 1):
        coll = "%02d %s" % (n, pk.replace(" - Tacticus", "").replace(" - Heresy", "")[-55:])
        for j, it in enumerate(items):
            lay.append((it, [GAP * (j % PER_ROW), 0, -ROW_GAP * (row + j // PER_ROW)], coll))
        row += (len(items) + PER_ROW - 1) // PER_ROW
    for k, ((rel, left, done), at, coll) in enumerate(lay):
        tid = "p%d" % k; short = os.path.basename(rel)
        objs += [{"id": tid, "role": "host", "name": "Torso 2 for " + short, "rel": MT.T2, "pose": {"place": True}, "at": at},
                 {"id": tid + "_spacer", "role": "check", "name": short + " Spacer", "connector": {"kind": "spacer", "from": "arms", "obj": "Springles Spacer"},
                  "parent": tid, "on": "Shoulder R", "pose": {"at_pivot": True, "shift_from": [MT.T2, "Shoulder R"]}},
                 {"id": tid + "_arm", "role": "check", "name": short + " Arm 2B R", "rel": MT.ARM, "parent": tid + "_spacer", "on": "arm seat", "pose": {"fit": "Shoulder R"}}]
        sh = {"id": tid + "_shell", "role": "check" if done else "part", "name": short + " Shell", "connector": SHELL, "parent": tid + "_arm", "on": "Pad R",
              "joint": "Shell on the arm (rotate it; the pauldron rides)", "pose": {"at_pivot": True, "shift_from": [MT.ARM, "Pad R"]}}
        e = {"id": tid + "_pad", "role": "check" if done else "part", "name": short + (" (mirrored, as a right pauldron)" if left else "") + (" (yours, locked)" if done else ""),
             "rel": rel, "parent": tid + "_shell", "on": "crown", "joint": "Pauldron in the shell"}
        if done: e["pose"] = {"fit": "Pad R"}; how = "already yours (locked)"
        else:
            if rel in mine and not left: F, how = mine[rel], "your Nov 22 placement"
            elif pack(rel) in by_pack: F, r = by_pack[pack(rel)]; how = "its pack's fit (%s)" % os.path.basename(r)
            elif maker(rel) in by_maker: F, r = by_maker[maker(rel)]; how = "its maker's fit (%s)" % os.path.basename(r)
            else: F, how = mine[MT.PAD], "Shoulder Pad 1's fit (no pack or maker placement)"
            if how != "your Nov 22 placement":       # the files of a pack don't share a place: keep that fit's turn, and
                ref = r if how.startswith("its") else MT.PAD  # put this one's bounding-box centre where that pauldron's is
                Vr = B.stl_tris(lib, ref, B.sidecar(lib, ref)).reshape(-1, 3)
                V = B.stl_tris(lib, rel, B.sidecar(lib, rel)).reshape(-1, 3)
                if left: V = V * np.array([-1.0, 1, 1])
                T = np.eye(4); T[:3, 3] = (Vr.min(0) + Vr.max(0)) / 2 - (V.min(0) + V.max(0)) / 2; F = F @ T
            e["pose"] = {"in_pivot": G.flat16(F)}
            e["write"] = {"host": tid + "_arm", "socket": "Pad R", "half": "fit", "on_written_socket": True}
            if left: e["mirror_mesh"] = True; e["write"]["left"] = "Pad L"
            else: e["write"]["mirror"] = "Pad L"
            sh["note"] = "rotate the shell (the pauldron rides on it) until the pauldron sits right; nudge the pauldron itself only if it sits wrong in the shell"
            e["note"] = "its place against Arm 2B R's Pad R is its fit on every arm (starts from %s)" % how
        sh["collection"] = e["collection"] = coll
        objs += [sh, e]; log.append("%-52s %s%s" % (short[:52], how, ", left-only: mirrored" if left else ""))
    srcs = dict(MT.SRC, pads=PADS)
    spec = {"name": name, "stage": "4 (arms' sockets): pauldrons on the shell", "out": blend_out, "sources": srcs,
            "about": "Every pauldron on the full-size shell on Arm 2B R: rotate the shell (the pauldron rides on it) until the pauldron sits right. Its place against 2B R's Pad R is its fit on every arm.",
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
