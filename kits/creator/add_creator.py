"""Add a maker's parts to the Kitbash Library in one run: helmets / heads get the Neck fit from Josh's Assault helmet 1
seat, pauldrons the Pad fit from his pad 62 (pushed out where they're thicker inside); every other type is filed
without a fit and logged. These are the steps done by hand for Springles / Redwarden (kits/rw_spr) and WarGame
Exclusive (kits/wg), driven by one JSON config per maker (kits/creator/<maker>.json; see wargame-exclusive.json).

A new maker, start to finish (about eight tool calls):
 1. PC (device_bash):  python3 on_pc.py survey "<folder in D:\\new cults>" TASK [--only GLOB] [--skip TEXT] --stage
    (on_pc.py lives in the page folder: ~/mnt/Desktop/TIOW Blender bridge/Squad Builder/add_creator_pc.py)
 2. device_stage_files the stage-NN.tgz files it lists.
 3. python3 add_creator.py unpack TASK        unpacks, sets up a fresh container, prints the survey's folders
 4. write the config (types from the survey and Josh's scope), then
    python3 add_creator.py go CONFIG          plan -> sheet -> fit -> test -> build; stops at a failed check
    Look at work/TASK/sheet.jpg once for a new frame (front, up, sculpted aquilas) and send Josh work/TASK/test/test.jpg.
 5. device_commit_files the list in work/TASK/deliver_files.json, then on the PC:
    python3 ".../_backups/TASK/deliver/on_pc.py" apply ".../_backups/TASK/deliver"     (--check first if unsure)
 6. python3 add_creator.py record CONFIG      sidecars, _sources.csv rows and hidden lines into the repo; commit.
Each step can also be run on its own: plan, sheet, fit, test, build. fit keeps what it has done (work/TASK/fits.json).

Config keys: task (the survey's), src (folder in new cults), root / prefix (library folder and name prefix), path
(default "{root}\\{category}\\{prefix} - {name}.stl"; also {folder} {stem}), scale (maker's scale, default 1),
types (first match wins: "match" a regex on the file name without .stl, "name" e.g. "Helmet {1}" ({0} the name, {1}..
the regex groups), "category" a TIOW type, "fit" "head" | "pad" | none, "why" for no-fit types, optional "in" a text
the path must contain), nofit {name: why}, hide {name: why}, skip [texts], padlift (default true), date ("Nov 9")."""
import csv, glob, hashlib, io, json, math, os, re, shutil, subprocess, sys, tarfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
UP = "/mnt/user-data/uploads"; U = UP + "/d/new cults/"; LIBU = UP + "/d/Kitbash Library/"
PY = "/home/claude/bpyenv/bin/python"; ADDONS = "/root/.config/blender/5.1/scripts/addons"
PCDIR = "~/mnt/d/Kitbash Library/_backups/"
STATE = ["_sources.csv", "_builder/index.json", "_builder/no_fit.txt", "_hidden.txt"]
REFS = {"Torso 1": "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1",
        "Legs 1A": "Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A",
        "Arm 1A R": "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R",
        "Arm 7B R": "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 7B R"}
SPLIT = 14 * 10 ** 6             # device_commit_files takes files up to ~14 MB reliably
GATES = {"head_max": 0.30,       # mm, median distance of helmet 1's neck ring after the match (WG 0.09-0.19, Springles <= 0.25)
         "pad_scale": (0.851, 1.349),   # 62's shell matched at pads.py's scale clamp = it didn't really match (WG PAD_7)
         "pad_max": 0.60}        # mm, median distance of 62's shell after the match


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def jl(p): return json.load(open(p, encoding="utf-8-sig"))
def jd(o, p, **k): json.dump(o, open(p, "w", encoding="utf-8"), **k)
def flat(M): return [round(float(x), 6) for x in M.reshape(-1)]


def load_cfg(path):
    c = jl(path); c.setdefault("scale", 1.0); c.setdefault("padlift", True)
    c.setdefault("path", "{root}\\{category}\\{prefix} - {name}.stl")
    c.setdefault("date", time.strftime("%b ") + str(int(time.strftime("%d"))))
    W = "/home/claude/work/" + c["task"]; os.makedirs(W, exist_ok=True)
    return c, W


# ---------------------------------------------------------------- unpack
def unpack(task):
    W = "/home/claude/work/" + task; os.makedirs(W + "/base", exist_ok=True)
    tgz = sorted(glob.glob(UP + "/**/" + task + "/stage/stage-*.tgz", recursive=True))
    assert tgz, "stage the stage-NN.tgz files first (on_pc.py survey ... --stage)"
    n = 0
    for f in tgz:
        with tarfile.open(f, "r:gz") as t:
            for m in t.getmembers():
                if not m.isfile(): continue
                top, rest = m.name.split("/", 1)
                dst = {"new cults": U, "Kitbash Library": LIBU, "Desktop": UP + "/Desktop/", "stage": W + "/"}[top] + rest
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as o: o.write(t.extractfile(m).read())
                n += 1
    for s in STATE:
        if os.path.exists(LIBU + s): shutil.copyfile(LIBU + s, W + "/base/" + s.replace("/", "__"))
    print("unpacked %d files from %d archive(s)" % (n, len(tgz)))
    # a fresh container: Blender module, add-ons, the old import paths; previews need fast_simplification
    zips = sorted(z for z in glob.glob(UP + "/Desktop/part_sockets_*.zip") if re.search(r"_\d+(\.\d+)*\.zip$", z))
    if zips and not os.path.exists(UP + "/Desktop/part_sockets_6.2.0.zip"): shutil.copyfile(zips[-1], UP + "/Desktop/part_sockets_6.2.0.zip")
    if os.path.exists(PY) and subprocess.run([PY, "-c", "import bpy"], capture_output=True).returncode:
        subprocess.run([PY, "-m", "pip", "install", "-q", "bpy==5.1.2", "numpy", "scipy", "pillow"], check=True)   # a venv left half made
    if not (os.path.exists(PY) and os.path.exists(ADDONS + "/part_sockets/blender_manifest.toml") and os.path.exists("/home/claude/real/fitlib.py")):
        subprocess.run(["bash", REPO + "/tools/setup_container.sh"], check=True, stdout=subprocess.DEVNULL)
    if subprocess.run([sys.executable, "-c", "import fast_simplification"], capture_output=True).returncode:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--root-user-action=ignore", "--break-system-packages", "fast_simplification"], check=True)
    S = jl(W + "/survey.json"); byf = {}
    for e in S["files"]: byf.setdefault(os.path.dirname(e["rel"]), []).append(os.path.basename(e["rel"])[:-4])
    for fo, names in sorted(byf.items()): print("  %-50s %3d  %s" % (fo[-50:], len(names), ", ".join(names[:5])[:80]))
    bi = S["base"].get("page/build_index.py")
    if bi and bi != md5(REPO + "/squad-builder/build_index.py"):
        print("!! the page's build_index.py on the PC differs from the repo's: previews/index entries may not match Prepare's")


# ---------------------------------------------------------------- plan
def joint_types():
    s = open(REPO + "/addons/tiow_inbox.py", encoding="utf-8").read()
    block = s[s.index("DEFAULT_JOINTS = {"):]; block = block[:block.index("\n}")]
    t = set(re.findall(r'^\s+"([^"]+)": \{', block, re.M))
    try: t |= set(jl(REPO + "/library-tools/partTypes.json"))
    except (ValueError, TypeError, OSError): pass
    return t | {"Unsorted"}


def plan(c, W):
    S = jl(W + "/survey.json"); assert S["task"] == c["task"]
    types = [(re.compile(t["match"], re.I), t) for t in c["types"]]
    ok_types = joint_types(); have = set()
    if os.path.exists(W + "/base/_sources.csv"):
        have = {r[0].lower() for r in csv.reader(open(W + "/base/_sources.csv", encoding="utf-8-sig")) if r}
    P, bad, skipped = [], [], []
    for e in S["files"]:
        rel = e["rel"]; stem = os.path.basename(rel)[:-4]; folder = os.path.basename(os.path.dirname(rel))
        if not rel.startswith(c["src"] + "/"): continue
        if any(s.lower() in rel.lower() for s in c.get("skip", [])): skipped.append(rel); continue
        if e["ascii"]: bad.append((rel, "ascii STL: convert it first")); continue
        hit = next(((t, r.fullmatch(stem)) for r, t in types if r.fullmatch(stem) and t.get("in", "").lower() in rel.lower()), None)
        if hit is None: bad.append((rel, "no type in the config matches")); continue
        t, mo = hit
        if t["category"] not in ok_types: bad.append((rel, "not a TIOW type: " + t["category"])); continue
        name = t["name"].format(stem, *mo.groups())
        lib = c["path"].format(root=c["root"], category=t["category"], prefix=c["prefix"], name=name, folder=folder, stem=stem)
        why = c.get("nofit", {}).get(stem)
        P.append(dict(rel=rel, stem=stem, folder=folder, category=t["category"], name=name, lib=lib, md5=e["md5"],
                      fit=None if why else t.get("fit"), why=why or t.get("why", "no spot for it yet")))
    libs = [p["lib"].lower() for p in P]
    bad += [(p["rel"], "library name used twice: " + p["lib"]) for p in P if libs.count(p["lib"].lower()) > 1]
    bad += [(p["rel"], "already in the library: " + p["lib"]) for p in P if p["lib"].lower() in have]
    unk = set(c.get("nofit", {})) | set(c.get("hide", {})); unk -= {p["stem"] for p in P}
    bad += [(n, "nofit/hide name not in the plan") for n in sorted(unk)]
    jd(P, W + "/plan.json", indent=0)
    cnt = {}
    for p in P: k = (p["category"], p["fit"] or "-"); cnt[k] = cnt.get(k, 0) + 1
    print("plan: %d parts (%d skipped by the config)" % (len(P), len(skipped)))
    for (cat, f), k in sorted(cnt.items()): print("  %-18s fit %-5s %3d   e.g. %s" % (cat, f, k, next(p["lib"].split("\\")[-1] for p in P if (p["category"], p["fit"] or "-") == (cat, f))))
    if bad:
        for r, w in bad[:30]: print("  !! %s: %s" % (r, w))
        sys.exit("plan: %d problem(s) to settle in the config" % len(bad))
    return P


# ---------------------------------------------------------------- sheet
def sheet(c, W):
    P = jl(W + "/plan.json")
    if len(P) > 120:                 # keep the sheet readable: 10 a type
        k = {}; P = [p for p in P if k.setdefault(p["category"], []).append(1) or len(k[p["category"]]) <= 10]
    job = {"items": [[U + p["rel"], p["name"]] for p in P], "scale": c["scale"], "out": W + "/sheet.jpg"}
    jd(job, W + "/sheet_job.json")
    r = subprocess.run([PY, HERE + "/sheet.py", "--", W + "/sheet_job.json"], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-2000:])
    print("sheet: %s (%d parts, numbered in plan order; categories: %s)" % (W + "/sheet.jpg", len(P), ", ".join(sorted({p["category"] for p in P}))))


# ---------------------------------------------------------------- fit
def worklib(W, P=None, sc=None):
    """W/worklib: MarFil/<ref> (links to the staged library files), NEW/<library name> (the maker's file + its sidecar)."""
    L = W + "/worklib"; os.makedirs(L + "/MarFil", exist_ok=True); os.makedirs(L + "/NEW", exist_ok=True)
    for ref in REFS.values():
        for ext in (".stl", ".sockets.json"):
            d = L + "/MarFil/" + os.path.basename(ref) + ext
            if not os.path.exists(d): os.symlink(LIBU + ref + ext, d)
    for p in P or []:
        b = L + "/NEW/" + os.path.basename(p["lib"].replace("\\", "/"))[:-4]
        if not os.path.exists(b + ".stl"): os.symlink(U + p["rel"], b + ".stl")
        shutil.copyfile(sc + "/" + p["rel"][:-4] + ".sockets.json", b + ".sockets.json")
    return L


def fit(c, W):
    P = jl(W + "/plan.json"); F = jl(W + "/fits.json") if os.path.exists(W + "/fits.json") else {}
    todo = [p for p in P if p["fit"] in ("head", "pad") and p["rel"] not in F]
    sys.path.insert(0, REPO + "/kits/rw_spr")
    import common
    sc = c["scale"]; t0 = time.time()
    if any(p["fit"] == "head" for p in todo):
        import heads as HM
    if any(p["fit"] == "pad" for p in todo):
        import pads as PM
    for p in todo:
        V, T = common.load(p["rel"], sc)
        if p["fit"] == "head":
            Fn, m = HM.neck_fit(V, T); F[p["rel"]] = {"method": "head", "fit": flat(Fn), "med": round(m, 4)}
        else:
            side, Fn, s, m = PM.pad_fit(V, T)
            F[p["rel"]] = {"method": "pad", "side": side, "fit": flat(Fn), "scale_vs_62": round(float(s), 4), "med": round(m, 4)}
        jd(F, W + "/fits.json", indent=0)            # after each part, so a stop loses nothing
    if todo: print("fitted %d parts in %.0f s" % (len(todo), time.time() - t0))
    pads = {p["rel"]: F[p["rel"]] for p in P if p["fit"] == "pad" and p["rel"] in F}
    if c["padlift"] and pads and not any("cut_after" in r for r in pads.values()):
        jd({r: {"fit": v["fit"], "scale": sc} for r, v in pads.items()}, W + "/padlift_in.json")
        L = worklib(W)
        r = subprocess.run([PY, REPO + "/kits/wg/padlift.py", "--", W + "/padlift_in.json", L, W + "/padlift.json"], capture_output=True, text=True)
        if r.returncode: sys.exit(r.stderr[-2000:])
        for rel, x in jl(W + "/padlift.json").items():
            F[rel].update(cut_before=x["cut_before"], cut_after=x["cut_after"])
            if x["moved_mm"] > 0: F[rel].update(fit=x["fit"], lift=x["moved_mm"])
        jd(F, W + "/fits.json", indent=0)
    gate(c, W, P, F)


def gate(c, W, P, F):
    """the checks that send a part to 'filed without a fit' (it stays in the plan, logged)."""
    g = dict(GATES, **c.get("gates", {})); out = {}
    for p in P:
        r = F.get(p["rel"])
        if not p["fit"] or r is None: continue
        if r["method"] == "head" and r["med"] > g["head_max"]:
            out[p["rel"]] = "helmet 1's neck ring didn't match it (%.2f mm off): place it by eye" % r["med"]
        if r["method"] == "pad":
            lo, hi = g["pad_scale"]
            if not lo < r["scale_vs_62"] < hi: out[p["rel"]] = "pad 62 only matched it at the scale limit (x%.2f): place it by eye" % r["scale_vs_62"]
            elif r["med"] > g["pad_max"]: out[p["rel"]] = "pad 62 didn't match it (%.2f mm off): place it by eye" % r["med"]
    jd(out, W + "/gated.json", indent=0)
    for meth in ("head", "pad"):
        R = [(p, F[p["rel"]]) for p in P if p["fit"] == meth and p["rel"] in F]
        if not R: continue
        med = sorted(r["med"] for _, r in R)
        line = "%s: %d, match %.3f-%.3f mm" % (meth, len(R), med[0], med[-1])
        if meth == "pad":
            s = sorted(r["scale_vs_62"] for _, r in R); cut = [r for _, r in R if "cut_after" in r]
            line += ", x%.2f-%.2f of 62, %d L-side" % (s[0], s[-1], sum(r["side"] == "Pad L" for _, r in R))
            if cut: line += ", pushed out %d (cut after %.2f-%.2f)" % (sum("lift" in r for r in cut), min(r["cut_after"] for r in cut), max(r["cut_after"] for r in cut))
        print(line)
        for p, r in R:
            if p["rel"] in out: print("   no fit: %s - %s" % (p["name"], out[p["rel"]]))
            elif r.get("cut_after", 0) > 0.65: print("   flag: %s still cuts %.2f mm (Fix the Part if it looks sunk)" % (p["name"], r["cut_after"]))


# ---------------------------------------------------------------- sidecars
def sidecars(c, W):
    P = jl(W + "/plan.json"); F = jl(W + "/fits.json") if os.path.exists(W + "/fits.json") else {}
    G = jl(W + "/gated.json") if os.path.exists(W + "/gated.json") else {}
    SC = W + "/sc"; shutil.rmtree(SC, ignore_errors=True)
    for p in P:
        d = {"schemaVersion": 1, "part": p["stem"], "sockets": [], "fits": {}, "notes": {},
             "original": {"name": p["stem"], "folder": p["folder"], "path": p["rel"].replace("/", "\\")}, "category": p["category"]}
        if c["scale"] != 1: d["scale"] = c["scale"]
        r = F.get(p["rel"]) if p["fit"] and p["rel"] not in G else None
        if p["fit"] and r is None and p["rel"] not in G: sys.exit("no fit yet for %s: run fit" % p["rel"])
        if r and r["method"] == "head":
            d["fits"]["Neck"] = r["fit"]; d["notes"]["Neck"] = "Josh's Assault helmet 1 neck seat matched onto it (match %.3f mm)" % r["med"]
        elif r and r["method"] == "pad":
            d["fits"][r["side"]] = r["fit"]
            d["notes"]["Pad"] = "Josh's pad 62 matched onto it (x%.2f, match %.3f mm), his Pad R fit carried across about 62's shell centre" % (r["scale_vs_62"], r["med"])
            if r.get("lift"): d["notes"]["Pad"] += "; pushed out %.2f mm off the shoulder (thicker inside than 62; padlift.py: %.2f mm into Arm 1A R after)" % (r["lift"], r["cut_after"])
        else:
            d["notes"]["category"] = "filed without a fit (%s): %s" % (c["date"], G.get(p["rel"], p["why"]))
        o = SC + "/" + p["rel"][:-4] + ".sockets.json"; os.makedirs(os.path.dirname(o), exist_ok=True)
        jd(d, o, indent=1)
    return SC


# ---------------------------------------------------------------- test
def test(c, W):
    P = jl(W + "/plan.json"); F = jl(W + "/fits.json") if os.path.exists(W + "/fits.json") else {}
    G = jl(W + "/gated.json") if os.path.exists(W + "/gated.json") else {}
    SC = sidecars(c, W)
    ok = [p for p in P if p["rel"] in F and p["rel"] not in G]
    heads = sorted((p for p in ok if p["fit"] == "head"), key=lambda p: -F[p["rel"]]["med"])
    pads = sorted((p for p in ok if p["fit"] == "pad"), key=lambda p: -F[p["rel"]].get("cut_after", F[p["rel"]]["med"]))
    if not heads and not pads: print("test: nothing with a fit to test"); return True
    L = worklib(W, heads + pads, SC)
    def nb(p): return "NEW/" + os.path.basename(p["lib"].replace("\\", "/"))[:-4]
    def pick(lst, i, k):             # models 1-2: the worst fits; model 3: the middle ones
        if not lst: return []
        j = i * k if i < 2 else len(lst) // 2
        return [lst[(j + q) % len(lst)] for q in range(min(k, len(lst)))]
    body = [["MarFil/" + os.path.basename(REFS["Torso 1"]), "Chests", None], ["MarFil/" + os.path.basename(REFS["Legs 1A"]), "Legs", "Waist"],
            ["MarFil/" + os.path.basename(REFS["Arm 1A R"]), "Arms", "Shoulder R"], ["MarFil/" + os.path.basename(REFS["Arm 7B R"]), "Arms", "Shoulder L"]]
    n = min(3, max(len(heads), math.ceil(len(pads) / 2)))
    models = {}
    for i in range(n):
        m = list(body)
        for p, s in zip(pick(pads, i, 2), ("Pad R", "Pad L")): m.append([nb(p), "Shoulder Pads", s])
        for p in pick(heads, i, 1): m.append([nb(p), "Heads", "Neck"])
        models["m%d" % (i + 1)] = m
    job = {"worklib": L, "tiow": REPO + "/addons/tiow_inbox.py", "out": W + "/test", "new": "NEW/", "models": models}
    jd(job, W + "/test_job.json", indent=0)
    r = subprocess.run([PY, REPO + "/tests/creator/t_creator.py", "--", W + "/test_job.json"], capture_output=True, text=True)
    R = jl(W + "/test/results.json") if os.path.exists(W + "/test/results.json") else None
    if R is None: sys.exit(r.stdout[-1500:] + r.stderr[-1500:])
    for x in R["parts"]: print("  %s %-34s %-6s closest %.2f, cut %.2f" % (x["model"], x["part"][:34], x["socket"], x["closest"], x["cut"]))
    print("test: %s; sheet %s" % ("all ok" if not R["fails"] else "FAILS %s" % R["fails"], W + "/test/test.jpg"))
    return not R["fails"]


# ---------------------------------------------------------------- build
def build(c, W):
    P = jl(W + "/plan.json"); SC = sidecars(c, W)
    ML = W + "/minilib"; shutil.rmtree(ML, ignore_errors=True); os.makedirs(ML)
    sys.path.insert(0, REPO + "/squad-builder"); import build_index
    rows = []
    for p in P:
        dst = ML + "/" + p["lib"].replace("\\", "/"); os.makedirs(os.path.dirname(dst), exist_ok=True)
        try: os.link(U + p["rel"], dst)
        except OSError: shutil.copyfile(U + p["rel"], dst)
        shutil.copyfile(SC + "/" + p["rel"][:-4] + ".sockets.json", dst[:-4] + ".sockets.json")
        rows.append([p["lib"], p["rel"].replace("/", "\\"), p["category"], ""])
    buf = io.StringIO(newline=""); w = csv.writer(buf, lineterminator="\r\n")
    for r in rows: w.writerow(r)
    open(ML + "/_rows.csv", "w", newline="", encoding="utf-8").write(buf.getvalue())
    open(ML + "/_sources.csv", "w", newline="", encoding="utf-8-sig").write("library path,copied from (D:\\new cults),type,folder fits folded in\r\n" + buf.getvalue())
    shutil.copyfile(REPO + "/bridge/_library.json", ML + "/_library.json")
    build_index.build(ML)
    nofit = [l.rstrip("\n") for l in open(ML + "/_builder/no_fit.txt", encoding="utf-8") if "\t" in l]
    # the PC's index with the new parts added (kept compact, ASCII-escaped or not as it was)
    raw = open(W + "/base/_builder__index.json", "rb").read(); d = json.loads(raw)
    ASCII = next(a for a in (True, False) if json.dumps(d, separators=(",", ":"), ensure_ascii=a).encode("utf-8") == raw)
    new = jl(ML + "/_builder/index.json"); have = {e["path"] for e in d["parts"]}
    add = [e for e in new["parts"] if e["path"] not in have]
    assert len(add) == len(new["parts"]) == len(P), "some parts are already in the index"
    d["parts"].extend(add)
    hide = []
    for p in P:
        if p["stem"] in c.get("hide", {}): hide += ["# " + c["hide"][p["stem"]], p["lib"]]
    # the delivery
    O = "/mnt/user-data/outputs/" + c["task"]; shutil.rmtree(O, ignore_errors=True); os.makedirs(O)
    def tgz(name, pairs):
        with tarfile.open(O + "/" + name, "w:gz") as t:
            for arc, src in pairs: t.add(src, arcname=arc)
    tgz("source_sidecars.tgz", [(p["rel"][:-4] + ".sockets.json", SC + "/" + p["rel"][:-4] + ".sockets.json") for p in P])
    tgz("library_sidecars.tgz", [(p["lib"].replace("\\", "/")[:-4] + ".sockets.json", ML + "/" + p["lib"].replace("\\", "/")[:-4] + ".sockets.json") for p in P])
    tgz("previews.tgz", [(e["prev"], ML + "/_builder/" + e["prev"]) for e in add if e.get("prev")])
    open(O + "/index.json", "wb").write(json.dumps(d, separators=(",", ":"), ensure_ascii=ASCII).encode("utf-8"))
    shutil.copyfile(ML + "/_rows.csv", O + "/rows.csv"); shutil.copyfile(HERE + "/on_pc.py", O + "/on_pc.py")
    base = {"_sources.csv": md5(W + "/base/_sources.csv"), "_builder/index.json": md5(W + "/base/_builder__index.json")}
    if nofit: base["_builder/no_fit.txt"] = md5(W + "/base/_builder__no_fit.txt")
    if hide: base["_hidden.txt"] = md5(W + "/base/_hidden.txt")
    files = {f: md5(O + "/" + f) for f in sorted(os.listdir(O))}
    split = {}
    for f in list(files):
        if os.path.getsize(O + "/" + f) > SPLIT:          # too big for one device_commit_files: parts, joined by apply
            data = open(O + "/" + f, "rb").read(); split[f] = []
            for i in range(0, len(data), SPLIT):
                q = "%s.part%02d" % (f, i // SPLIT); open(O + "/" + q, "wb").write(data[i:i + SPLIT]); split[f].append(q)
            os.remove(O + "/" + f)
    M = {"task": c["task"], "base": base, "copies": [[p["rel"], p["lib"].replace("\\", "/"), p["md5"]] for p in P],
         "files": files, "split": split, "nofit": nofit, "hide": hide}
    jd(M, O + "/manifest.json", indent=0)
    K = PCDIR + c["task"] + "/deliver/"
    jd([{"devicePath": K + f, "stagedPath": O + "/" + f} for f in sorted(os.listdir(O))], W + "/deliver_files.json", indent=0)
    jd({"minilib": ML, "nofit": nofit, "hide": hide}, W + "/built.json", indent=0)
    nf = sum(1 for p in P if not jl(SC + "/" + p["rel"][:-4] + ".sockets.json")["fits"])
    print("build: %d parts (%d with fits, %d filed without), %d previews, %d no_fit lines, %d hidden; index %d -> %d parts" % (
        len(P), len(P) - nf, nf, sum(1 for e in add if e.get("prev")), len(nofit), len(hide) // 2, len(d["parts"]) - len(add), len(d["parts"])))
    print("deliver: %d files (%.1f MB) -> %s  (list: %s)" % (len(os.listdir(O)), sum(os.path.getsize(O + "/" + f) for f in os.listdir(O)) / 1e6, K, W + "/deliver_files.json"))
    print('then: python3 "$HOME/mnt/d/Kitbash Library/_backups/%s/deliver/on_pc.py" apply "$HOME/mnt/d/Kitbash Library/_backups/%s/deliver"' % (c["task"], c["task"]))


# ---------------------------------------------------------------- record
def record(c, W):
    B = jl(W + "/built.json"); ML = B["minilib"]; P = jl(W + "/plan.json"); n = 0
    for p in P:
        rel = p["lib"].replace("\\", "/")[:-4] + ".sockets.json"; dst = REPO + "/library/" + rel
        assert not os.path.exists(dst), "already in the repo: " + rel
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(ML + "/" + rel, dst); n += 1
    s = REPO + "/library/_sources.csv"; rows = open(ML + "/_rows.csv", "rb").read()
    t = open(s, "rb").read(); assert t.endswith(b"\r\n"); open(s, "wb").write(t + rows)
    if B["hide"]:
        h = REPO + "/library/_hidden.txt"; t = open(h, "rb").read(); nl = b"\r\n" if b"\r\n" in t else b"\n"
        open(h, "wb").write(t + (b"" if t.endswith(nl) else nl) + nl.join(x.encode() for x in B["hide"]) + nl)
    print("record: %d sidecars, %d _sources.csv rows, %d hidden lines into the repo" % (n, rows.count(b"\r\n"), len(B["hide"]) // 2))


if __name__ == "__main__":
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "unpack": unpack(arg); sys.exit()
    c, W = load_cfg(arg)
    if cmd == "go":
        plan(c, W); sheet(c, W); fit(c, W)
        if not test(c, W): sys.exit("stopped: a test check failed (look at test/test.jpg; fix the config or gates, or run build anyway)")
        build(c, W)
    else:
        {"plan": plan, "sheet": sheet, "fit": fit, "test": test, "build": build, "record": record, "sidecars": sidecars}[cmd](c, W)
