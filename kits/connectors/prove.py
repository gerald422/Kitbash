"""The proving run (docs/PLAN.md, Order 1): Josh's reference file read, its cuts searched on a small set of parts, test
marines assembled from the numbers alone. Nothing is written to the library.

    blender --background --factory-startup --python kits/connectors/prove.py -- run [--lib LIB] [--ref BLEND] [--out DIR] [--reuse]
                                                                                [--maker "Mar Fil - Tacticus"] [--per 4] [--workers 8]
Output in DIR (default ~/Desktop/mar fil connectors/proving): report.txt, results.json, "proving set.blend".
For each part and joint: the cut found (sure / look / none), and how far the new socket or fit is from the library's
(for information: the library's is not used). Roll: the file's (the search prefers no turn from the maker's frame)."""
import sys, os, json, time, subprocess, tempfile, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO); sys.path.insert(0, HERE)
from kb import connect as C, geo
import seat as S, reference as RF
C.KEYED_KEEPS_SHAPE = True       # a cut with a notch keeps its own turn; only round cuts take the file's roll (Josh, Nov 16)

MX = np.diag([-1.0, 1, 1, 1])
BIKE = ("ChaplainOnBike", "Outriders")    # bike torsos and riding legs: their own cuts later (Josh, Nov 16)
# The search looks for the SHAPE of Josh's cut surface only: never triangle counts, never the part's whole mesh or
# geometry compared (Josh, Nov 13 / 17; it has slipped back before). The region below only narrows where to look.
PLACE = {"wrist": "shoulder", "pad": "shoulder", "shin": "waist"}   # spots on a host, and the joint that places that host
TOL = {"wrist": 4.0, "pad": 2.5, "shin": 4.0, "buckle": 3.0}        # mm either way of the reference's distance from it
BUCKLE_FLAG = 3.0     # deg: the buckle turns the legs more than this from the waist's own turn: written, flagged
HOST_NEAR_IN_REGION = False   # tried Nov 17: a near host match inside the region, written. The Intercessor arm's near pad
                              # spot sat flipped behind the shoulder: a different sculpt is not found by narrowing where
                              # to look. Hosts stay sure only (Josh, Nov 16); the region only keeps answers in the right place.
def opt(A, n, d=None): return A[A.index(n) + 1] if n in A else d
def M4(a): return np.array(a, float).reshape(4, 4)
def flat(M): return [round(float(x), 6) for x in np.asarray(M).reshape(-1)]


def pick(lib, maker, per, ref_rels):
    """a small spread of the maker's right / unsided parts per type, one kit after another; the reference's parts first"""
    idx = json.load(open(lib + "/_builder/index.json", encoding="utf-8")); hidden = set()
    try: hidden = {l.strip().lower() for l in open(lib + "/_hidden.txt", encoding="utf-8-sig") if l.strip() and not l.startswith("#")}
    except OSError: pass
    types = sorted({t for j in RF.JOINTS.values() for t in j[4] + j[5]}); out = []
    for t in types:
        es = [e for e in idx["parts"] if e["path"].startswith(maker) and e["type"] == t and e.get("side") in (None, "R")
              and not (t in ("Chests", "Legs") and any(k in e["path"] for k in BIKE))
              and not any(x in e["path"].replace("\\", "/") for x in RF.EXCLUDE)
              and e["path"].lower() not in hidden and not any(w in e["name"].lower() for w in ("no hand", "handless"))]
        bykit = collections.defaultdict(list)
        for e in sorted(es, key=lambda e: e["name"]): bykit[e["path"].split("\\")[1]].append(e)
        got = [e for e in es if e["path"][:-4].replace("\\", "/") in ref_rels]; kits = sorted(bykit, key=lambda k: -len(bykit[k])); i = 0
        while len(got) < per + len([e for e in es if e["path"][:-4].replace("\\", "/") in ref_rels]) and any(bykit.values()):
            k = kits[i % len(kits)]; i += 1
            if bykit[k]:
                e = bykit[k].pop(0)
                if e not in got: got.append(e)
        out += [(t, e["path"][:-4].replace("\\", "/")) for e in got]
    return out


def search(work, i, n):
    ref = json.load(open(work + "/ref.json", encoding="utf-8")); lib = ref["lib"]; jobs = json.load(open(work + "/jobs.json", encoding="utf-8"))[i::n]
    cons = {}
    def con(c):
        if c["cut"] not in cons: cons[c["cut"]] = C.Connector(np.load(work + "/" + c["npy"]), c["cut"])
        return cons[c["cut"]]
    def region(c, jn, placeF):
        """the shell round the host's placing joint where this cut should be (Josh, Nov 17), or None"""
        F = placeF.get(PLACE.get(jn, ""))
        if F is None or "Jplace" not in c: return None
        d = float(np.linalg.norm(S_tf(con(c).c[None], np.linalg.inv(M4(c["Jplace"])))[0]))
        return (np.linalg.inv(F)[:3, 3], max(0.0, d - TOL[jn]), d + TOL[jn])
    out = open("%s/res_%d.jsonl" % (work, i), "a", encoding="utf-8")
    for cat, rel in jobs:
        t0 = time.time(); r = {"cat": cat, "rel": rel, "joints": {}}
        try:
            sc, G, back = S.maker(lib + "/" + rel + S.SC.SUFFIX); tri = S.unmoved(C.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)), back)
            surf = C.Surface(tri); V = tri.reshape(-1, 3)[::max(1, len(tri) * 3 // 400)]; Fw = None; placeF = {}; placeSure = {}
            for jn, j in ref["joints"].items():
                for role, key in (("host", "hosts"), ("child", "children")):
                    if cat not in j[role + "_types"]: continue
                    if jn == "shin" and role == "host":       # each shin on its own, sides from the legs' waist (as on the torso)
                        r["joints"]["shin:host"] = shins(j, con, tri, Fw, lambda c: region(c, "shin", placeF), placeSure.get("waist", False)); continue
                    best = None
                    for c in j[key]:
                        rg = region(c, jn, placeF) if role == "host" else None
                        f = C.find(con(c), surf, region=rg); f["cut"] = c["cut"]; f["J"] = c["J"]; f["rg"] = rg
                        rank = ({"sure": 0, "look": 1, "none": 2}[f["level"]], f["match"])
                        if best is None or rank < best[0]: best = (rank, f)
                    f = best[1]; d = {"role": role, "cut": f["cut"], "level": f["level"], "match": f["match"], "cover": f["cover"],
                                      "turned": f.get("turned"), "round": f.get("round"), "ambiguous": bool(f.get("ambiguous"))}
                    near_ok = role == "child" or (HOST_NEAR_IN_REGION and f["rg"] is not None and placeSure.get(PLACE[jn], False))
                    if f["rg"] is not None: d["region"] = "%.1f-%.1f mm from its %s" % (f["rg"][1], f["rg"][2], PLACE[jn])
                    if role == "host" and f["level"] == "look":
                        d["note"] = ("near, inside the region round its sure %s: written, flagged" % PLACE[jn]) if near_ok else "near only, no region: a host anchor needs a sure match (Josh, Nov 16): cut this"
                    if f["level"] == "sure" or (f["level"] == "look" and near_ok):
                        MJ = f["M"] @ M4(f["J"])
                        if role == "host":
                            d["socket"] = j["socket"]; d["matrix"] = flat(MJ)
                            old = next((M4(s["matrix"]) for s in sc.get("sockets") or [] if s.get("type") == j["socket"]), None)
                            if old is not None: d["lib_mm"] = round(float(np.linalg.norm(old[:3, 3] - MJ[:3, 3])), 2); d["lib_deg"] = round(geo.ang(old[:3, :3].T @ MJ[:3, :3]), 1)
                        else:
                            F = np.linalg.inv(MJ)
                            if jn == "waist" and ref.get("buckle"): F = buckle(ref["buckle"], ref["joints"]["waist"], con, surf, F, d)
                            d["fit"] = j["fit"]; d["matrix"] = flat(F); placeF[jn] = F; placeSure[jn] = f["level"] == "sure"
                            if jn == "waist": Fw = F
                            fits = sc.get("fits") or {}; old = next((M4(fits[k]) for k in (j["fit"], j["fit"].replace(" R", "")) if k in fits), None)
                            if old is not None:
                                d["lib_mm"] = round(float(np.median(np.linalg.norm(S_tf(V, F) - S_tf(V, old), axis=1))), 2); d["lib_deg"] = round(geo.ang(F[:3, :3] @ old[:3, :3].T), 1)
                    r["joints"][jn + ":" + role] = d
        except Exception as e:
            r["error"] = repr(e)
        r["secs"] = round(time.time() - t0); out.write(json.dumps(r) + "\n"); out.flush()


def S_tf(V, M): return V @ M[:3, :3].T + M[:3, 3]


def buckle(b, wj, con, surf, F, d):
    """the legs' turn about the waist from the belt buckle (Josh, Nov 17): the buckle sits forward of the waist, so it
    points the way the legs face with a long lever. Found (sure) -> the legs are turned about the waist's axis until
    their buckle lies the way the reference's does; the waist still gives the place and tilt. Not found -> the notch."""
    cb = con(b); Qr = S_tf(cb.c[None], np.linalg.inv(M4(b["Jplace"])))[0]; dr = float(np.linalg.norm(Qr))
    rg = (np.linalg.inv(F)[:3, 3], max(0.0, dr - TOL["buckle"]), dr + TOL["buckle"])
    f = C.find(cb, surf, region=rg); d["buckle"] = {"level": f["level"], "match": f["match"], "cover": f["cover"]}
    if f["level"] != "sure": return F
    w = wj["children"][0]; ax = np.linalg.inv(M4(w["J"]))[:3, :3] @ con(w).axis; ax /= np.linalg.norm(ax)   # the waist's axis, joint frame
    Qn = S_tf(S_tf(cb.c[None], f["M"]), F)[0]
    pr = lambda q: q - ax * (q @ ax); a, b_ = pr(Qn), pr(Qr)
    deg = float(np.degrees(np.arctan2(np.cross(a, b_) @ ax, a @ b_))); d["buckle"]["deg"] = round(deg, 1)
    if abs(deg) > BUCKLE_FLAG: d["note"] = "the buckle turned the legs %.1f deg from the waist's own turn: flagged" % deg
    Rz = np.eye(4); Rz[:3, :3] = C._rot(ax, deg); return Rz @ F


def shins(j, con, tri, Fw, region=lambda c: None, place_sure=False):
    """both shin spots, each searched on its own leg. Right / left is decided in the waist joint's frame (the torso's:
    +X is the marine's right), not the file's: some legs are turned in their file (Outrider legs, 90 deg). The left
    shin: with a left shin spot cut (Josh's left pad placed by eye: Nov 17), that cut on the left leg as it is; without
    one, the right cut on the left leg mirrored about the legs' own middle plane, its socket the mirror of a right one
    (Shin L = mirror x right x mirror, as the library keeps left sockets). Either way the left pad is the right pad
    mirrored (left = right mirrored)."""
    if Fw is None: Fw = np.eye(4)                              # no waist found: the file's own axes
    Fi = np.linalg.inv(Fw); P = Fi @ MX @ Fw                   # the mirror about the legs' middle plane, in file coordinates
    xw = S_tf(tri.mean(1), Fw)[:, 0]
    out = {"role": "host", "level": "none", "match": 9.0, "cover": 0.0, "cut": "-", "sides": {}}
    own_left = [c for c in j["hosts"] if c.get("side") == "L"]; rights = [c for c in j["hosts"] if c.get("side", "R") == "R"]
    for side, keep in (("Shin R", xw > 0), ("Shin L", xw < 0)):
        T = tri[keep]; mir = side == "Shin L" and not own_left
        if len(T) < 50: continue
        if mir: T = S_tf(T.reshape(-1, 3), P).reshape(-1, 3, 3)[:, [0, 2, 1]]   # mirrored, faces kept outward
        surf = C.Surface(T); best = None
        for c in (own_left if side == "Shin L" and own_left else rights):
            rg = region(c); f = C.find(con(c), surf, region=rg); f["cut"] = c["cut"]; f["J"] = c["J"]; f["rg"] = rg
            rank = ({"sure": 0, "look": 1, "none": 2}[f["level"]], f["match"])
            if best is None or rank < best[0]: best = (rank, f)
        f = best[1]; s = {"level": f["level"], "match": f["match"], "cover": f["cover"], "cut": f["cut"]}
        # a host anchor: sure, or near inside the region round a sure waist (Josh, Nov 16 / 17)
        if f["level"] == "sure" or (HOST_NEAR_IN_REGION and f["level"] == "look" and f["rg"] is not None and place_sure):
            MJ = f["M"] @ M4(f["J"]); s["matrix"] = flat(P @ MJ @ MX if mir else MJ)
        out["sides"][side] = s
    R_ = out["sides"].get("Shin R")
    if R_:
        out.update({k: R_[k] for k in ("level", "match", "cover", "cut")}); out["socket"] = "Shin R"
        if R_["level"] == "look" and "matrix" in R_: out["note"] = "near, inside the region round its sure waist: written, flagged"
        if "matrix" in R_: out["matrix"] = R_["matrix"]
    L_ = out["sides"].get("Shin L")
    if L_ and "matrix" in L_: out["other"] = {"socket": "Shin L", "matrix": L_["matrix"], "level": L_["level"], "match": L_["match"]}
    return out


def place_joint(ref, pj, obj):
    """the placing joint (shoulder / waist) of a part in the reference's world: from the nearest torso (a copy of a torso
    with that joint known) within 40 mm; None = the part sits on no torso, no region for its spots"""
    P = ref["parts"]; HJ = ref["joints"][pj]["host_J"]; best = None
    for key, J in HJ.items():
        rel, sd = key.rsplit("|", 1)
        for pn, p in P.items():
            if p["rel"] == rel and pn != obj:
                d = float(np.linalg.norm(p["mid"] - P[obj]["mid"]))
                if best is None or d < best[0]: best = (d, P[pn]["Wm"] @ J)
    return best[1] if best and best[0] <= 40 else None


def run(A):
    import bpy
    from mathutils import Matrix
    lib = opt(A, "--lib", "D:/Kitbash Library"); blend = opt(A, "--ref", os.path.expanduser("~/Desktop/mar fil connectors/Kitbash reference.blend"))
    out = opt(A, "--out", os.path.expanduser("~/Desktop/mar fil connectors/proving")); maker = opt(A, "--maker", "Mar Fil - Tacticus")
    os.makedirs(out, exist_ok=True); work = tempfile.mkdtemp(prefix="kitbash-prove-"); t0 = time.time()
    import add_reference_parts as AR, make_reference as MR     # the files the reference is built from: a renamed object is known by its mesh
    pool = sorted({MR.TORSO} | {p[0] for p in MR.PARTS} | {AR.TORSO, AR.ARM, AR.SWORD, AR.PAD, AR.JUMP, AR.PACK} | {g[1] for g in AR.GROUPS} | {p[0] for g in AR.GROUPS for p in g[2]}
                  | {AR.MF + "AssaultMarines-V2/Knee Pads/MarFil Assault - Shin Pad 1"})
    ref = RF.read(blend, lib, pool); print("reference: %d parts, joints %s" % (len(ref["parts"]), ", ".join(ref["joints"])), flush=True)
    for n in ref["notes"]: print("  note: " + n, flush=True)
    dump = {"lib": lib, "joints": {}}; k = 0
    for jn, j in ref["joints"].items():
        d = {x: j[x] for x in ("socket", "fit", "host_types", "child_types", "frame")}
        for key in ("hosts", "children"):
            d[key] = []
            for c in j[key]:
                k += 1; np.save("%s/cut%02d.npy" % (work, k), c["tri"]); e = {"cut": c["cut"], "part": c["part"], "npy": "cut%02d.npy" % k, "J": flat(c["J"])}
                if "side" in c: e["side"] = c["side"]
                if key == "hosts" and jn in PLACE and PLACE[jn] in ref["joints"]:   # the placing joint in the cut's part coordinates
                    Jp = place_joint(ref, PLACE[jn], c["obj"])
                    if Jp is not None: e["Jplace"] = flat(np.linalg.inv(ref["parts"][c["obj"]]["Wm"]) @ Jp)
                d[key].append(e)
        dump["joints"][jn] = d
    for b in ref.get("spots", {}).get("legs buckle", [])[:1]:
        if "waist" in ref["joints"]:
            k += 1; np.save("%s/cut%02d.npy" % (work, k), b["tri"])
            Jp = place_joint(ref, "waist", b["obj"])
            if Jp is not None: dump["buckle"] = {"cut": b["cut"], "part": b["part"], "npy": "cut%02d.npy" % k, "Jplace": flat(np.linalg.inv(b["Wm"]) @ Jp)}
    json.dump(dump, open(work + "/ref.json", "w", encoding="utf-8"))
    jobs = pick(lib, maker, int(opt(A, "--per", 4)), {p["rel"] for p in ref["parts"].values()})
    json.dump(jobs, open(work + "/jobs.json", "w", encoding="utf-8")); n = 0 if "--reuse" in A else min(int(opt(A, "--workers", 8)), len(jobs))
    if "--reuse" in A:                      # the report and test marines again from DIR/results.json, no search
        old = json.load(open(out + "/results.json", encoding="utf-8"))["results"]
        for x in old: open(work + "/res_0.jsonl", "a", encoding="utf-8").write(json.dumps(x) + "\n")
        n = 1; jobs = [(x["cat"], x["rel"]) for x in old]
    else: print("searching %d parts with %d workers..." % (len(jobs), n), flush=True)
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    procs = [] if "--reuse" in A else [subprocess.Popen([bpy.app.binary_path, "--background", "--factory-startup", "--python", os.path.abspath(__file__), "--", "search", work, str(i), str(n)],
                              stdout=open("%s/worker_%d.log" % (work, i), "w"), stderr=subprocess.STDOUT, env=env) for i in range(n)]
    last = -1
    while any(p.poll() is None for p in procs):
        time.sleep(15); done = sum(sum(1 for _ in open(f, encoding="utf-8")) for f in ("%s/res_%d.jsonl" % (work, i) for i in range(n)) if os.path.exists(f))
        if done != last: print("  %d of %d, %.0f min" % (done, len(jobs), (time.time() - t0) / 60), flush=True); last = done
    R = [json.loads(l) for i in range(n) if os.path.exists("%s/res_%d.jsonl" % (work, i)) for l in open("%s/res_%d.jsonl" % (work, i), encoding="utf-8")]
    order = {tuple(j): i for i, j in enumerate(map(tuple, jobs))}; R.sort(key=lambda r: order.get((r["cat"], r["rel"]), 0))
    json.dump({"reference": dump["joints"], "notes": ref["notes"], "results": R}, open(out + "/results.json", "w", encoding="utf-8"), indent=1)
    # ---- report
    W = ["Proving run: %s, %d parts, reference %s (%s)" % (maker, len(R), os.path.basename(blend), time.strftime("%Y-%m-%d %H:%M")), ""]
    W += ["note: " + x for x in ref["notes"]] + [""]
    cnt = collections.defaultdict(collections.Counter)
    for r in R:
        for jk, d in r["joints"].items(): cnt[jk][d["level"]] += 1
    W.append("%-16s %5s %5s %5s" % ("joint:side", "sure", "look", "none"))
    for jk, c in cnt.items(): W.append("%-16s %5d %5d %5d" % (jk, c["sure"], c["look"], c["none"]))
    W.append("")
    for r in R:
        W.append("%s  [%s]%s" % (r["rel"].split("/", 1)[1], r["cat"], "  ERROR " + r["error"] if r.get("error") else ""))
        for jk, d in r["joints"].items():
            W.append("    %-15s %-5s %.4f mm %3.0f%%  cut %-34s%s%s%s%s%s%s" % (jk, d["level"], d["match"], 100 * d["cover"], d["cut"][:34],
                     "  roll moved %.1f deg to the file's" % d["turned"] if d.get("turned") else "",
                     "  library's is %.2f mm / %.1f deg away" % (d["lib_mm"], d["lib_deg"]) if "lib_mm" in d else ("  (library has none)" if d["level"] != "none" else ""),
                     "  left shin: %s" % d["other"]["level"] if d.get("other") else "",
                     "  buckle %s%s" % (d["buckle"]["level"], " turned %.1f deg" % d["buckle"]["deg"] if "deg" in d["buckle"] else "") if d.get("buckle") else "",
                     "  [" + d["region"] + "]" if d.get("region") else "", "  (" + d["note"] + ")" if d.get("note") else ""))
    open(out + "/report.txt", "w", encoding="utf-8").write("\n".join(W) + "\n")
    # ---- test marines from the numbers alone
    by = collections.defaultdict(list)
    for r in R: by[r["cat"]].append(r)
    def got(r, jk): d = (r or {}).get("joints", {}).get(jk); return M4(d["matrix"]) if d and "matrix" in d else None
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    made = []; nm = max(len(by["Chests"]), 4)
    def put(rel, Wm, coll):
        sc, G, back = S.maker(lib + "/" + rel + S.SC.SUFFIX); bpy.ops.wm.stl_import(filepath=lib + "/" + rel + ".stl")
        o = bpy.context.selected_objects[0]; o.name = os.path.basename(rel)
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o); o.matrix_world = Matrix((Wm if back is None else Wm @ back).tolist())
    for m in range(nm):
        nth = lambda t, off=0: by[t][(m + off) % len(by[t])] if by[t] else None
        torso = nth("Chests"); coll = bpy.data.collections.new("marine %d" % (m + 1)); bpy.context.scene.collection.children.link(coll)
        Wt = np.eye(4); Wt[0, 3] = 70.0 * m; put(torso["rel"], Wt, coll); line = ["marine %d: %s" % (m + 1, os.path.basename(torso["rel"]))]
        def hang(child, jn, Wh, host):
            Sx, F = got(host, jn + ":host"), got(child, jn + ":child")
            if child is None: return None
            if Sx is None or F is None:
                line.append("   %s NOT placed (%s: %s)" % (os.path.basename(child["rel"]), jn, "no socket on its host" if Sx is None else "its cut not found")); return None
            Wc = Wh @ Sx @ F; put(child["rel"], Wc, coll)
            line.append("   %-44s %s: host %s, part %s" % (os.path.basename(child["rel"])[:44], jn, host["joints"][jn + ":host"]["level"], child["joints"][jn + ":child"]["level"])); return Wc
        arm, legs = nth("Arms"), nth("Legs")
        Wa = hang(arm, "shoulder", Wt, torso); Wl = hang(legs, "waist", Wt, torso); hang(nth("Heads"), "neck", Wt, torso)
        hang(nth("Jump Packs") if m % 2 == 0 else nth("Backpacks", m // 2), "back", Wt, torso)
        if Wa is not None:
            hang(nth("Shoulder Pads"), "pad", Wa, arm); hang((by["Melee"] + by["Pistols"])[m % max(1, len(by["Melee"] + by["Pistols"]))] if by["Melee"] + by["Pistols"] else None, "wrist", Wa, arm)
        if Wl is not None:
            pad = nth("Knee Pads")
            if hang(pad, "shin", Wl, legs) is not None:             # and the left: the same pad mirrored (left = right mirrored)
                o = (legs["joints"].get("shin:host") or {}).get("other")
                if o:
                    put(pad["rel"], Wl @ M4(o["matrix"]) @ MX @ got(pad, "shin:child"), coll)
                    line.append("   %-44s shin L: host %s (mirrored)" % (os.path.basename(pad["rel"])[:44], o["level"]))
                else: line.append("   left shin pad NOT placed: the left shin spot was not found")
        made += line
    bpy.ops.wm.save_as_mainfile(filepath=out + "/proving set.blend")
    open(out + "/report.txt", "a", encoding="utf-8").write("\nTest marines in 'proving set.blend' (70 mm apart, from the numbers alone):\n" + "\n".join(made) + "\n")
    print("\n".join(W[:len(ref["notes"]) + 4 + len(cnt) + 1])); print("\n".join(made)); print("done in %.0f min: %s" % ((time.time() - t0) / 60, out))


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if A and A[0] == "run": run(A[1:])
    elif A and A[0] == "search": search(A[1], int(A[2]), int(A[3]))
    else: print(__doc__)
