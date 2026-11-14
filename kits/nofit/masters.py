"""One master a maker and armour type (Josh, Nov 14, notes 094): a fitted part's inside is the shell every other part
of its family is mated to; a part's fit is the master's, moved by how the part lies on the master. So a family that
sits wrong is put right once, at its master, never part by part.

    BL  masters.py families LIBRARY WORK [--type "Shoulder Pads"] [--maker X] [--shard I/N] [--gate 0.20]
                                         each maker's parts of the type grouped by their inside; the master of a
                                         family is its plainest fitted right part -> WORK/masters-<maker>.json
    PY  masters.py report   WORK         the families, how their members' present fits agree with the master's
    BL  masters.py one      LIBRARY WORK [--type T] [--shard I/N] [--master REL]   ONE master a maker folder (maker +
                                         armour type): every part slid onto it by the dome (seat_dome), its fit =
                                         the master's moved by that -> WORK/one-<maker>.json   (PY report-one WORK)
    PY  masters.py sheet    LIBRARY WORK [--min 2]   each master of a family of --min parts or more built on the Mar
                                         Fil body with its present fit (TIOW Inbox as installed,
                                         tests/creator/t_creator.py) -> WORK/sheet/out/m<n>_front.png, _right.png
    PY  masters.py shells   LIBRARY WORK OUT             after `one`: each folder's master's inside as an STL lying where
                                         it sits on the joint (the scene's origin = the socket) -> OUT/<maker> - <type> shell.stl
    BL  masters.py compose  WORK [--dir sheet|compare]   those pictures as one numbered sheet -> WORK/<dir>/masters.jpg
    PY  masters.py compare  LIBRARY WORK [--most 16]     after `one`: pads that lie on the master as it is and whose
                                         present fit differs, built with both fits (odd = now, even = the master's)
  BL = blender --background --factory-startup --python ... --   PY = a Python with numpy (Blender's own)

Seating (seat_any): the boxes of the two insides lined up, the master slid onto the part without turning, then left
to settle; when that does not sit, the square turns whose box fits are tried (a part lying another way in its file).
The distance is what 90% of the points are within, both ways, so the rims have to line up too. A left part is
mirrored first (its family is the right part's). An inside that is alike front and back cannot say which way round
the part is: the smallest turn is kept.
"""
import sys, os, json, glob, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
import carry_library as CL
GATE = 0.20


def q90(tree, P): return float(np.quantile(tree.query(P)[0], 0.9))
def seat(M, P, R0):
    """the master's inside M put on the part's inside P, starting with the boxes lined up after the turn R0"""
    from kb import geo
    t = (P.S.min(0) + P.S.max(0)) / 2 - R0 @ ((M.S.min(0) + M.S.max(0)) / 2)
    for _ in range(25):                                    # slide on, no turning
        d, i = P.tree.query(M.full @ R0.T + t); k = d <= np.quantile(d, 0.85); t = t + (P.tree.data[i[k]] - (M.full[k] @ R0.T + t)).mean(0)
    R, t, _ = geo.icp(M.full, P.tree, R0, t, 30)           # then settle (may turn a little)
    return max(q90(P.tree, M.full @ R.T + t), q90(M.tree, (P.full - t) @ R)), R, t
def seat_any(M, P, gate=GATE):
    from kb import carry
    s, R, t = seat(M, P, np.eye(3)); how = "frame"
    if s > gate:                                           # not lying as the master does
        c = sorted(carry.ROTS, key=lambda R0: float(np.abs(np.ptp(M.S @ R0.T, 0) - np.ptp(P.S, 0)).sum()))[:6]
        alt = min((seat(M, P, R0) for R0 in c), key=lambda x: x[0])
        if alt[0] < s - 0.05: (s, R, t), how = alt, "turned"
    return s, R, t, how


def seat_dome(M, P):
    """ONE master a maker and armour type (Josh: the rim and what is on the pad do not matter, the dome that sits on
    the shoulder does): the master's inside slid onto the part's without turning, by the 60% of it that lies closest
    (the dome; a different rim is left out). A maker's pads share a frame, so no turning; only when a square turn
    lines the rims up far better (under 0.6 of the distance) is the part taken to lie that way in its file.
    -> (dome: median distance, rim: the 90% distance both ways, R, t, 'frame' | 'turned')"""
    from kb import carry
    def go(R0):
        t = (P.S.min(0) + P.S.max(0)) / 2 - R0 @ ((M.S.min(0) + M.S.max(0)) / 2); X = M.full @ R0.T
        for _ in range(30):
            d, i = P.tree.query(X + t); k = d <= np.quantile(d, 0.6); t = t + (P.tree.data[i[k]] - (X[k] + t)).mean(0)
        d = P.tree.query(X + t)[0]
        return float(np.median(d)), max(float(np.quantile(d, 0.9)), q90(M.tree, (P.full - t) @ R0)), R0, t
    a = go(np.eye(3)); how = "frame"
    turns = sorted((R0 for R0 in carry.ROTS if not np.allclose(R0, np.eye(3))), key=lambda R0: float(np.abs(np.ptp(M.S @ R0.T, 0) - np.ptp(P.S, 0)).sum()))[:6]
    b = min((go(R0) for R0 in turns), key=lambda x: x[1])
    if b[1] < 0.6 * a[1]: a, how = b, "turned"
    return a + (how,)


def one(lib, work, A):
    """every pad of a maker folder on that folder's one master (the head of its biggest family, or --master REL)"""
    from kb import carry
    typ = CL.opt(A, "--type", "Shoulder Pads"); i, n = CL.shard_of(A); by = collections.defaultdict(list)
    for rel, sc in CL.scan(lib, [typ])[typ]: by[CL.maker(rel)].append((rel, sc))
    def shape(rel, sc, left): return carry.Inner(carry.Shape(lib + "/" + rel + ".stl", sc.get("scale", 1.0), 0, left))
    for mk in sorted(by)[i::n]:
        f = "%s/masters-%s.json" % (work, mk); D = dict(by[mk])
        mrel = CL.opt(A, "--master") or (max(json.load(open(f, encoding="utf-8"))["families"], key=lambda x: len(x["members"]))["master"] if os.path.exists(f) else None)
        if mrel not in D: print(mk, ": no master"); continue
        FM, mleft = right_fit(D[mrel]); M = shape(mrel, D[mrel], mleft); rows = []
        for rel, sc in by[mk]:
            if rel == mrel: continue
            F0, left = right_fit(sc)
            try: P = shape(rel, sc, left)
            except (OSError, ValueError) as e: print("unreadable", rel, e); continue
            dome, rim, R, t, how = seat_dome(M, P); F = FM @ np.linalg.inv(carry.M4(R, t))
            r = {"rel": rel, "dome": round(dome, 3), "rim": round(rim, 2), "how": how, "left": left, "fitted": F0 is not None, "fit": carry.flat(F)}
            if F0 is not None: r["lib_mm"] = round(float(np.linalg.norm(carry.point("fit", F) - carry.point("fit", F0))), 2); r["lib_deg"] = round(carry.ang(F, F0), 1)
            rows.append(r); print("%-52s dome %.2f rim %.2f %-6s %s" % (os.path.basename(rel)[-52:], dome, rim, how, "library %.2f mm %.1f deg" % (r["lib_mm"], r["lib_deg"]) if F0 is not None else "no fit yet"), flush=True)
        json.dump({"maker": mk, "type": typ, "master": mrel, "parts": rows}, open("%s/one-%s.json" % (work, mk), "w", encoding="utf-8"), indent=0)


def report_one(work):
    for f in sorted(glob.glob(glob.escape(work) + "/one-*.json")):
        D = json.load(open(f, encoding="utf-8")); P = D["parts"]; X = [p for p in P if p["fitted"]]; U = [p for p in P if not p["fitted"]]
        a = [p for p in X if p["lib_mm"] <= 0.5 and p["lib_deg"] <= 3]; b = [p for p in X if p["lib_mm"] <= 1.0 and p["lib_deg"] <= 6]
        print("%s  master: %s" % (D["maker"], os.path.basename(D["master"])))
        print("   %d fitted pads on it: %d within 0.5 mm / 3 deg of their present fit, %d within 1 mm / 6 deg; dome sits: median %.2f, worst %.2f mm; %d taken as lying turned" % (
            len(X), len(a), len(b), np.median([p["dome"] for p in X]) if X else 0, max([p["dome"] for p in X] or [0]), sum(p["how"] == "turned" for p in X)))
        for p in sorted((p for p in X if p not in b), key=lambda p: -p["lib_deg"])[:40]:
            print("      differs: %-46s %.1f mm %5.1f deg  (dome %.2f, rim %.2f, %s)" % (os.path.basename(p["rel"])[-46:], p["lib_mm"], p["lib_deg"], p["dome"], p["rim"], p["how"]))
        if U: print("   %d without a fit: %s" % (len(U), "; ".join("%s %.2f" % (os.path.basename(p["rel"]).split(" - ", 1)[-1][:28], p["dome"]) for p in U)))


def shells(lib, work, out, A):
    """Josh, Nov 14: the shell at the centre of a scene, every part moved to it and mated there. One STL a maker
    folder: its master's inside faces, moved to where the master sits on the joint (the master's fit), so the scene's
    origin is the socket and every maker's shell lies at the same place (an adaptor between two is the gap between
    them). A part's place on the shell (`fit` in one-*.json: part -> shell) then is all a part needs; the shell's own
    place on the socket is the one fit a maker and armour type, Josh's to set."""
    from kb import carry
    os.makedirs(out, exist_ok=True); bins = 60
    for f in sorted(glob.glob(glob.escape(work) + "/one-*.json")):
        D = json.load(open(f, encoding="utf-8")); sc = json.load(open(lib + "/" + D["master"] + ".sockets.json", encoding="utf-8-sig")); F, left = right_fit(sc)
        tri = carry.soup(lib + "/" + D["master"] + ".stl", sc.get("scale", 1.0)) * (np.array([-1.0, 1, 1]) if left else 1.0)
        I = carry.inner(carry.sample(tri, 60000, 0)); C = carry._centre(I)
        def cell(P):
            d = P - C; r = np.linalg.norm(d, axis=1); u = d / np.maximum(r, 1e-9)[:, None]
            th = np.arccos(np.clip(u[:, 2], -1, 1)); ph = np.arctan2(u[:, 1], u[:, 0]) + np.pi
            return np.minimum((th / np.pi * bins).astype(int), bins - 1) * (2 * bins) + np.minimum((ph / (2 * np.pi) * 2 * bins).astype(int), 2 * bins - 1), r
        k, r = cell(I); far = np.full(2 * bins * bins, -1.0); np.maximum.at(far, k, r)       # how far the inside reaches, a direction
        kc, rc = cell(tri.mean(1)); keep = rc <= far[kc] + 0.15; T = tri[keep]
        T = (np.c_[T.reshape(-1, 3), np.ones(len(T) * 3)] @ F.T)[:, :3].reshape(-1, 3, 3)       # to the socket's own space
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]); rec["n"], rec["v"] = n, T
        name = "%s - %s shell" % (D["maker"], D["type"])
        with open("%s/%s.stl" % (out, name), "wb") as fo: fo.write(b"shell".ljust(80, b" ")); fo.write(np.uint32(len(T)).tobytes()); fo.write(rec.tobytes())
        c = T.reshape(-1, 3); print("%-46s %6d of %6d faces, from %s; box %s to %s" % (name, len(T), len(tri), os.path.basename(D["master"]), c.min(0).round(1), c.max(0).round(1)))


def right_fit(sc):
    """(the part's fit as a right part, is it a left part) or (None, False)"""
    from kb import carry
    fits = sc.get("fits") or {}
    k = next((k for k in fits if k.endswith(" R")), None) or next(iter(fits), None)
    if k is None: return None, False
    F = np.array(fits[k]).reshape(4, 4); left = k.endswith(" L")
    return (carry.MX @ F @ carry.MX if left else F), left


def families(lib, work, A):
    from kb import carry, geo
    typ = CL.opt(A, "--type", "Shoulder Pads"); i, n = CL.shard_of(A); only = CL.opt(A, "--maker"); gate = float(CL.opt(A, "--gate", GATE))
    by = collections.defaultdict(list)
    for rel, sc in CL.scan(lib, [typ])[typ]: by[CL.maker(rel)].append((rel, sc))
    for mk in sorted(by)[i::n]:
        if only and only not in mk: continue
        parts = []
        for rel, sc in by[mk]:
            F, left = right_fit(sc)
            try: sh = carry.Shape(lib + "/" + rel + ".stl", sc.get("scale", 1.0), 0, left)
            except (OSError, ValueError) as e: print("unreadable", rel, e); continue
            parts.append({"rel": rel, "F": F, "left": left, "vol": float(np.prod(sh.ext)), "I": carry.Inner(sh)})
        def member(h, p, s, R, t, how):
            m = {"rel": p["rel"], "seat": round(s, 3), "turn": round(geo.ang(R), 1), "how": how, "left": p["left"], "fitted": p["F"] is not None}
            if p["F"] is not None:
                F = h["F"] @ np.linalg.inv(carry.M4(R, t))
                m["lib_mm"] = round(float(np.linalg.norm(carry.point("fit", F) - carry.point("fit", p["F"]))), 3); m["lib_deg"] = round(carry.ang(F, p["F"]), 2)
            return m
        def best_head(p, heads):
            best = None
            for h in heads:
                if np.abs(h["I"].ext - p["I"].ext).sum() > 1.5: continue          # another size: not this inside
                s, R, t, how = seat_any(h["I"], p["I"], gate)
                if best is None or s < best[1]: best = (h, s, R, t, how)
            return best
        heads, nomaster = [], []
        for p in sorted((p for p in parts if p["F"] is not None), key=lambda p: (p["left"], p["vol"])):   # right and plainest first
            b = best_head(p, heads)
            if b and b[1] <= gate: b[0]["members"].append(member(*((b[0], p) + b[1:])))
            else: p["members"] = []; heads.append(p)
            print("%-56s %s" % (os.path.basename(p["rel"])[-56:], "on %s (%.2f mm)" % (os.path.basename(b[0]["rel"])[-40:], b[1]) if b and b[1] <= gate else "a master"), flush=True)
        for p in (p for p in parts if p["F"] is None):
            b = best_head(p, heads)
            if b and b[1] <= gate: b[0]["members"].append(member(*((b[0], p) + b[1:])))
            else: nomaster.append({"rel": p["rel"], "best": None if not b else [os.path.basename(b[0]["rel"]), round(b[1], 2)]})
            print("%-56s no fit yet: %s" % (os.path.basename(p["rel"])[-56:], "on %s (%.2f mm)" % (os.path.basename(b[0]["rel"])[-40:], b[1]) if b and b[1] <= gate else "no master"), flush=True)
        out = {"maker": mk, "type": typ, "gate": gate, "nomaster": nomaster,
               "families": [{"master": h["rel"], "left": h["left"], "members": h["members"]} for h in heads]}
        json.dump(out, open("%s/masters-%s.json" % (work, mk), "w", encoding="utf-8"), indent=0)


def load(work): return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(glob.escape(work) + "/masters-*.json"))]
def report(work):
    k = 0
    for D in load(work):
        F = D["families"]; n = sum(1 + len(f["members"]) for f in F)
        print("%s: %d %s with a fit in %d families; %d without a fit have no master" % (D["maker"], n, D["type"].lower(), len(F), len(D["nomaster"])))
        for f in sorted(F, key=lambda f: -len(f["members"])):
            k += 1; M = [m for m in f["members"] if m["fitted"]]; ok = [m for m in M if m["lib_mm"] <= 0.5 and m["lib_deg"] <= 3]; new = [m for m in f["members"] if not m["fitted"]]
            print("  %3d %-46s + %2d fitted (%2d agree with it; worst %.1f mm %.0f deg)%s" % (k, os.path.basename(f["master"])[-46:], len(M), len(ok),
                  max([m["lib_mm"] for m in M] or [0]), max([m["lib_deg"] for m in M] or [0]), "  + %d without a fit" % len(new) if new else ""))
        for x in D["nomaster"]: print("      no master: %-44s nearest %s" % (os.path.basename(x["rel"])[-44:], x["best"]))


def sheet(lib, work, A):
    """each master on the Mar Fil body with the fit it has now"""
    sys.path.insert(0, REPO + "/kits/creator"); import add_creator as AC
    W = work + "/sheet"; os.makedirs(W + "/worklib", exist_ok=True); ref = lambda k: lib + "/" + AC.REFS[k]
    body = [[ref("Torso 1"), "Chests", None], [ref("Legs 1A"), "Legs", "Waist"], [ref("Arm 1A R"), "Arms", "Shoulder R"], [ref("Arm 7B R"), "Arms", "Shoulder L"]]
    models, names, k = {}, {}, 0; least = int(CL.opt(A, "--min", "2"))
    for D in load(work):
        for f in sorted(D["families"], key=lambda f: -len(f["members"])):
            k += 1                                                         # report's number
            if 1 + len(f["members"]) < least: continue
            models["m%02d" % k] = body + [[lib + "/" + f["master"], D["type"], "Pad L" if f["left"] else "Pad R"]]
            names["m%02d" % k] = [D["maker"], os.path.basename(f["master"]), 1 + len(f["members"])]
    json.dump({"worklib": W + "/worklib", "tiow": None, "out": W + "/out", "new": "NEW/", "models": models, "nocut": [], "check": []}, open(W + "/job.json", "w"), indent=0)
    json.dump(names, open(W + "/names.json", "w"), indent=0)
    r = AC.run_bpy(REPO + "/tests/creator/t_creator.py", W + "/job.json", addons=True)
    print("\n".join(l for l in (r.stdout or "").splitlines() if "FAIL" in l or "passed" in l)); print("%d masters built -> %s/out" % (len(models), W))
    if r.returncode: print((r.stderr or "")[-1500:])


def compare(lib, work, A):
    """the pads whose inside lies on the one master as it is (rim too) and whose present fit is not the master's:
    each built twice on the Mar Fil body, odd number = the fit it has now, even = the master's fit moved onto it"""
    import shutil
    from kb import carry
    sys.path.insert(0, REPO + "/kits/creator"); import add_creator as AC
    W = work + "/compare"; NEW = W + "/worklib/NEW"; os.makedirs(NEW, exist_ok=True); ref = lambda k: lib + "/" + AC.REFS[k]
    body = [[ref("Torso 1"), "Chests", None], [ref("Legs 1A"), "Legs", "Waist"], [ref("Arm 1A R"), "Arms", "Shoulder R"], [ref("Arm 7B R"), "Arms", "Shoulder L"]]
    rim = float(CL.opt(A, "--rim", "0.35")); most = int(CL.opt(A, "--most", "16")); pick = []
    for f in sorted(glob.glob(glob.escape(work) + "/one-*.json")):
        D = json.load(open(f, encoding="utf-8"))
        X = [p for p in D["parts"] if p["fitted"] and p["rim"] <= rim and p["how"] == "frame" and (p["lib_deg"] > 6 or p["lib_mm"] > 1)]
        pick += [(D, p) for p in sorted(X, key=lambda p: -p["lib_deg"])[:3]]
    models, names = {}, {}
    for n, (D, p) in enumerate(pick[:most]):
        nm = os.path.basename(p["rel"]); sc = json.load(open(lib + "/" + p["rel"] + ".sockets.json", encoding="utf-8-sig")); side = "Pad L" if p["left"] else "Pad R"
        F = np.array(p["fit"]).reshape(4, 4); sc["fits"] = {side: carry.flat(carry.MX @ F @ carry.MX if p["left"] else F)}
        shutil.copyfile(lib + "/" + p["rel"] + ".stl", NEW + "/" + nm + ".stl"); json.dump(sc, open(NEW + "/" + nm + ".sockets.json", "w", encoding="utf-8"))
        a, b = "m%02d" % (2 * n + 1), "m%02d" % (2 * n + 2)
        models[a] = body + [[lib + "/" + p["rel"], D["type"], side]]; models[b] = body + [["NEW/" + nm, D["type"], side]]
        names[a] = [D["maker"], nm, "now"]; names[b] = [D["maker"], nm, "from the master %s: %.1f mm %.0f deg from now" % (os.path.basename(D["master"]), p["lib_mm"], p["lib_deg"])]
    json.dump({"worklib": W + "/worklib", "tiow": None, "out": W + "/out", "new": "NEW/", "models": models, "nocut": [], "check": []}, open(W + "/job.json", "w"), indent=0)
    json.dump(names, open(W + "/names.json", "w"), indent=0)
    r = AC.run_bpy(REPO + "/tests/creator/t_creator.py", W + "/job.json", addons=True)
    print("\n".join(l for l in (r.stdout or "").splitlines() if "FAIL" in l or "closest" in l)); print("%d pads, each twice -> %s/out" % (len(models) // 2, W))
    for k in sorted(names): print(int(k[1:]), "|", names[k][1], "|", names[k][2])
    if r.returncode: print((r.stderr or "")[-1500:])


FONT = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111", "4": "101101111001001",
        "5": "111100111001111", "6": "111100111101111", "7": "111001001001001", "8": "111101111101111", "9": "111101111001111"}
def compose(work, A):
    import bpy
    W = work + "/" + CL.opt(A, "--dir", "sheet"); names = json.load(open(W + "/names.json")); keys = sorted(names); cols, t = 4, 210
    def pic(p, x0, y0):                                    # the shoulder, as rendered (t_creator's 420 px pictures)
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)[::-1, :, :3]; bpy.data.images.remove(im); return a[y0:y0 + t, x0:x0 + t]
    rows = -(-len(keys) // cols); C = np.zeros((rows * t, cols * 2 * t, 3), np.float32)
    for n, k in enumerate(keys):
        r, c = divmod(n, cols); cell = np.hstack([pic("%s/out/%s_front.png" % (W, k), 40, 20), pic("%s/out/%s_right.png" % (W, k), 95, 20)])
        for j, ch in enumerate(k[1:].lstrip("0") or "0"):                  # the number, top left, yellow
            g = np.array([int(x) for x in FONT[ch]], bool).reshape(5, 3).repeat(5, 0).repeat(5, 1); y, x = 6, 6 + j * 20
            cell[y:y + 25, x:x + 15][g] = (1.0, 0.85, 0.1)
        cell[:, -1] = 0.5; cell[-1, :] = 0.5; C[r * t:(r + 1) * t, c * 2 * t:(c + 1) * 2 * t] = cell
    H, Wd = C.shape[:2]; out = bpy.data.images.new("sheet", Wd, H); out.pixels.foreach_set(np.dstack([C[::-1], np.ones((H, Wd, 1), np.float32)]).ravel())
    out.filepath_raw = W + "/masters.jpg"; out.file_format = "JPEG"; out.save(); print("sheet: %d masters -> %s/masters.jpg (%d x %d)" % (len(keys), W, Wd, H))


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if not A: sys.exit(__doc__)
    if A[0] == "families": families(A[1], A[2], A)
    elif A[0] == "report": report(A[1])
    elif A[0] == "one": one(A[1], A[2], A)
    elif A[0] == "shells": shells(A[1], A[2], A[3], A)
    elif A[0] == "report-one": report_one(A[1])
    elif A[0] == "sheet": sheet(A[1], A[2], A)
    elif A[0] == "compose": compose(A[1], A)
    elif A[0] == "compare": compare(A[1], A[2], A)
    else: sys.exit(__doc__)
