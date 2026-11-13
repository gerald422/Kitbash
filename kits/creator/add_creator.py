"""Add a maker's parts to the Kitbash Library in one run: helmets / heads get the Neck fit from Josh's Assault helmet 1
seat, pauldrons the Pad fit from his pad 62 (pushed out where they're thicker inside); every other type is filed
without a fit and logged. These are the steps done by hand for Springles / Redwarden (kits/rw_spr) and WarGame
Exclusive (kits/wg), driven by one JSON config per maker (kits/creator/<maker>.json; see wargame-exclusive.json).

On the PC (a session in the repo clone, or Josh with "Add parts.bat"): one command, nothing staged. It runs inside the
installed Blender, which has everything it needs (numpy, its own KD tree for the matching, Decimate for the previews):

    blender --background --factory-startup --python kits/creator/add_creator.py -- add RECIPE [--src FOLDER] [--dry] [--yes]

  RECIPE   a maker's saved config in kits/creator (name or path; `recipes` lists them; left out, it asks)
  --src    the folder with the new STLs, inside D:\\new cults (default: the recipe's "src"). Files the library
           already has (their source path is in _sources.csv) are left out, so a maker's folder can be run again
           whenever it gains parts; "nothing new" ends the run.
  It surveys the folder, plans the names, lists the new files with mesh faults (for Caliper Repair.bat afterwards),
  renders the contact sheet, fits heads and pads, builds three test marines with TIOW Inbox, then asks before it adds:
  the files under their library names, sidecars, previews, index, _sources.csv, no_fit and hidden lines (checked,
  with the library's lists backed up in _backups\\TASK\\before), and the sidecars and rows into this clone for a
  commit. --dry stops before adding (`finish TASK` adds later); --yes doesn't ask (and stops at a failed test check
  unless --force); --no-open doesn't open the pictures; --no-record leaves the clone alone.
  Work files: D:\\Kitbash Library\\_backups\\TASK\\work (sheet_front.png, sheet_back.png, test\\*.png).
  A new maker needs a recipe first: copy wargame-exclusive.json, set root / prefix / types from the survey's names
  (a file no type matches stops the plan and is listed), and look at the sheet once for front, up and aquilas.

In the container (the earlier way), a new maker, start to finish (about eight tool calls):
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
the regex groups), "category" a TIOW type, "fit" "head" | "pad" | "like" | none ("like": arms, legs and torsos take
their fit / sockets from the fitted parts of the same type already in the library folder they are filed in, kb/carry.py;
what its gates drop is filed without a fit, with the number), "why" for no-fit types, optional "in" a text
the path must contain), nofit {name: why}, hide {name: why}, skip [texts], padlift (default true), date ("Nov 9")."""
import csv, glob, hashlib, io, json, math, os, re, shutil, subprocess, sys, tarfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
UP = "/mnt/user-data/uploads"; U = UP + "/d/new cults/"; LIBU = UP + "/d/Kitbash Library/"
PY = "/home/claude/bpyenv/bin/python"; ADDONS = "/root/.config/blender/5.1/scripts/addons"
PCDIR = "~/mnt/d/Kitbash Library/_backups/"
WORK, OUT = "/home/claude/work/%s", "/mnt/user-data/outputs/%s"
sys.path.insert(0, REPO); sys.path.insert(0, HERE)
PC = os.name == "nt"             # a session (or Josh) on the PC itself: the real folders, the Blender that is installed
if PC:
    import importlib.util
    _sp = importlib.util.spec_from_file_location("kbtool", os.path.join(REPO, "tools", "kb.py"))
    kbtool = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(kbtool); ROOTS = kbtool.roots()
    U = ROOTS["nc"].replace("\\", "/").rstrip("/") + "/"; LIBU = ROOTS["lib"].replace("\\", "/").rstrip("/") + "/"
    WORK, OUT = LIBU + "_backups/%s/work", LIBU + "_backups/%s/deliver"
    try:
        import bpy; BLENDER = bpy.app.binary_path
    except ImportError:
        BLENDER = os.environ.get("BLENDER", "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe")


def run_bpy(script, *args, addons=False):
    """a Blender script as its own process: the bpy venv in the container; on the PC the installed Blender, started
    clean, or with Josh's add-ons loaded (addons=True) for a TIOW Inbox test"""
    cmd = ([BLENDER, "--background"] + ([] if addons else ["--factory-startup"]) + ["--python", script, "--"]) if PC else [PY, script, "--"]
    return subprocess.run(cmd + list(args), capture_output=True, text=True, encoding="utf-8", errors="replace")


def _link(src, dst):
    try: os.symlink(src, dst)
    except OSError: shutil.copyfile(src, dst)        # Windows without the privilege, or exFAT: a copy
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
    W = WORK % c["task"]; os.makedirs(W, exist_ok=True)
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


def plan(c, W, skip_have=False):
    """skip_have: files the library already holds (their source path is in _sources.csv) are left out, so a maker's
    folder can be run again when it gains parts"""
    S = jl(W + "/survey.json"); assert S["task"] == c["task"]
    types = [(re.compile(t["match"], re.I), t) for t in c["types"]]
    ok_types = joint_types(); have, have_src = set(), set()
    if os.path.exists(W + "/base/_sources.csv"):
        rows = [r for r in csv.reader(open(W + "/base/_sources.csv", encoding="utf-8-sig")) if r]
        have = {r[0].lower() for r in rows}; have_src = {r[1].replace("\\", "/").lower() for r in rows if len(r) > 1}
    P, bad, skipped, already = [], [], [], []
    for e in S["files"]:
        rel = e["rel"]; stem = os.path.basename(rel)[:-4]; folder = os.path.basename(os.path.dirname(rel))
        if not rel.startswith(c["src"] + "/"): continue
        if any(s.lower() in rel.lower() for s in c.get("skip", [])): skipped.append(rel); continue
        if skip_have and rel.lower() in have_src: already.append(stem); continue
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
    unk = set(c.get("nofit", {})) | set(c.get("hide", {})); unk -= {p["stem"] for p in P} | set(already)
    bad += [(n, "nofit/hide name not in the plan") for n in sorted(unk)]
    jd(P, W + "/plan.json", indent=0)
    cnt = {}
    for p in P: k = (p["category"], p["fit"] or "-"); cnt[k] = cnt.get(k, 0) + 1
    print("plan: %d parts (%d skipped by the config%s)" % (len(P), len(skipped), ", %d already in the library" % len(already) if skip_have else ""))
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
    r = run_bpy(HERE + "/sheet.py", W + "/sheet_job.json")
    if r.returncode: sys.exit(r.stderr[-2000:])
    print("sheet: %s (%d parts, numbered in plan order; categories: %s)" % (W + ("/sheet_front.png, sheet_back.png" if PC else "/sheet.jpg"), len(P), ", ".join(sorted({p["category"] for p in P}))))


# ---------------------------------------------------------------- fit
def worklib(W, P=None, sc=None):
    """W/worklib: MarFil/<ref> (links to the staged library files), NEW/<library name> (the maker's file + its sidecar)."""
    L = W + "/worklib"; os.makedirs(L + "/MarFil", exist_ok=True); os.makedirs(L + "/NEW", exist_ok=True)
    for ref in REFS.values():
        for ext in (".stl", ".sockets.json"):
            d = L + "/MarFil/" + os.path.basename(ref) + ext
            if not os.path.exists(d): _link(LIBU + ref + ext, d)
    for p in P or []:
        b = L + "/NEW/" + os.path.basename(p["lib"].replace("\\", "/"))[:-4]
        if not os.path.exists(b + ".stl"): _link(U + p["rel"], b + ".stl")
        shutil.copyfile(sc + "/" + p["rel"][:-4] + ".sockets.json", b + ".sockets.json")
    return L


_REFS = {}
def like_refs(p):
    """the fitted parts of the same type already in the library folder this part will be filed in"""
    from kb import carry
    d = LIBU + os.path.dirname(p["lib"].replace("\\", "/")); refs = []
    if (d, p["category"]) in _REFS: return _REFS[(d, p["category"])]      # one reading of a folder's parts for the whole run
    _REFS[(d, p["category"])] = refs
    for f in sorted(glob.glob(glob.escape(d) + "/*.sockets.json")):
        sc = jl(f)
        if sc.get("category") == p["category"] and carry.joints(p["category"], sc) and os.path.exists(f[:-13] + ".stl"):
            refs.append(carry.Ref(os.path.basename(f)[:-13], sc, f[:-13] + ".stl"))
    return refs


def fit_like(c, p):
    from kb import carry
    got = carry.like(p["category"], carry.Shape(U + p["rel"], c["scale"]), like_refs(p),
                     stem=os.path.basename(p["lib"].replace("\\", "/"))[:-4], gates=c.get("gates", {}).get("like"))
    return dict(method="like", **got)


def fit(c, W):
    P = jl(W + "/plan.json"); F = jl(W + "/fits.json") if os.path.exists(W + "/fits.json") else {}
    todo = [p for p in P if p["fit"] in ("head", "pad", "like") and p["rel"] not in F]
    from kb import fit as KF                     # the Nov 9 head / pad rules (kits/rw_spr), without the container's paths
    sc = c["scale"]; t0 = time.time(); lib = LIBU.rstrip("/")
    HM = KF.Heads(lib) if any(p["fit"] == "head" for p in todo) else None
    PM = KF.Pads(lib) if any(p["fit"] == "pad" for p in todo) else None
    for k, p in enumerate(todo):
        if k and k % 10 == 0: print("  fitted %d of %d (%.0f s)" % (k, len(todo), time.time() - t0), flush=True)
        if p["fit"] == "like":
            F[p["rel"]] = fit_like(c, p); jd(F, W + "/fits.json", indent=0); continue
        V, T = KF.load(U + p["rel"], sc)
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
        r = run_bpy(REPO + "/kits/wg/padlift.py", W + "/padlift_in.json", L, W + "/padlift.json", U, LIBU)
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
        if r["method"] == "like" and not r["fits"] and not r["sockets"]:
            out[p["rel"]] = "; ".join("%s: %s" % (n, w) if n != "*" else w for n, w in r["rejected"].items()) or "nothing to carry"
        if r["method"] == "head" and r["med"] > g["head_max"]:
            out[p["rel"]] = "helmet 1's neck ring didn't match it (%.2f mm off): place it by eye" % r["med"]
        if r["method"] == "pad":
            lo, hi = g["pad_scale"]
            if not lo < r["scale_vs_62"] < hi: out[p["rel"]] = "pad 62 only matched it at the scale limit (x%.2f): place it by eye" % r["scale_vs_62"]
            elif r["med"] > g["pad_max"]: out[p["rel"]] = "pad 62 didn't match it (%.2f mm off): place it by eye" % r["med"]
    jd(out, W + "/gated.json", indent=0)
    lk = [(p, F[p["rel"]]) for p in P if p["fit"] == "like" and p["rel"] in F]
    if lk:
        modes = {}
        for p, r in lk:
            for n, h in r["how"].items():
                if n in r["fits"] or any(s["type"] == n for s in r["sockets"]): modes[h["mode"]] = modes.get(h["mode"], 0) + 1
        print("like: %d, carried %d (joints: %s), filed without a fit %d" % (len(lk), sum(1 for p, r in lk if p["rel"] not in out),
              ", ".join("%s %d" % kv for kv in sorted(modes.items())) or "none", sum(1 for p, r in lk if p["rel"] in out)))
        for p, r in lk:
            if p["rel"] in out: print("   no fit: %s - %s" % (p["name"], out[p["rel"]][:150]))
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
        elif r and r["method"] == "like":
            d["fits"].update(r["fits"]); d["sockets"] = r["sockets"]
            for n, h in r["how"].items():
                if n in r["fits"] or any(s["type"] == n for s in r["sockets"]):
                    d["notes"][n] = "carried from %s (%s): region match %.2f mm, whole shape %.2f mm" % (h["from"], h["mode"], h["match"], h["whole"])
            for n, w in r["rejected"].items(): d["notes"]["no " + n] = w
        else:
            d["notes"]["category"] = "filed without a fit (%s): %s" % (c["date"], G.get(p["rel"], p["why"]))
        o = SC + "/" + p["rel"][:-4] + ".sockets.json"; os.makedirs(os.path.dirname(o), exist_ok=True)
        jd(d, o, indent=1)
    return SC


# ---------------------------------------------------------------- test
_FLAT = {}
def flat_torso(p):
    """a torso of the same maker that has a Flat Waist socket (library path without .stl), for standing flat legs under"""
    maker = p["lib"].replace("\\", "/").split("/")[0]
    if maker not in _FLAT:
        _FLAT[maker] = None
        for f in sorted(glob.glob(glob.escape(LIBU + maker) + "/**/*.sockets.json", recursive=True)):
            try: sc = jl(f)
            except ValueError: continue
            if sc.get("category") == "Chests" and any(s.get("type") == "Flat Waist" for s in sc.get("sockets") or []) and os.path.exists(f[:-13] + ".stl"):
                _FLAT[maker] = f[:-13]; break
    return _FLAT[maker]


def test(c, W):
    P = jl(W + "/plan.json"); F = jl(W + "/fits.json") if os.path.exists(W + "/fits.json") else {}
    G = jl(W + "/gated.json") if os.path.exists(W + "/gated.json") else {}
    SC = sidecars(c, W)
    ok = [p for p in P if p["rel"] in F and p["rel"] not in G]
    heads = sorted((p for p in ok if p["fit"] == "head"), key=lambda p: -F[p["rel"]]["med"])
    pads = sorted((p for p in ok if p["fit"] == "pad"), key=lambda p: -F[p["rel"]].get("cut_after", F[p["rel"]]["med"]))
    likes = sorted((p for p in ok if p["fit"] == "like"), key=lambda p: -max([h["match"] for h in F[p["rel"]]["how"].values()] or [0]))
    tl = [p for cat in ("Arms", "Legs", "Chests") for p in [q for q in likes if q["category"] == cat][:2]]   # the loosest two a type
    if not heads and not pads and not tl: print("test: nothing with a fit to test"); return True
    L = worklib(W, heads + pads + tl, SC)
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
    for p in tl:                    # a carried arm / legs on the Mar Fil body, a carried torso under the Mar Fil parts
        r = F[p["rel"]]; me = nb(p); key = next(iter(r["fits"]), None)
        if p["category"] == "Arms":
            if key not in ("Shoulder R", "Shoulder L"): continue
            m = [body[0], body[1], [me, "Arms", key], body[3] if key == "Shoulder R" else body[2]]
        elif p["category"] == "Legs":
            if key == "Waist": m = [body[0], [me, "Legs", "Waist"], body[2], body[3]]
            else:
                host = flat_torso(p)
                if not host: print("  %s: no torso with a Flat Waist socket found to stand it under, not test-built" % p["name"]); continue
                m = [[host, "Chests", None], [me, "Legs", key]]
        else: m = [[me, "Chests", None], body[1], body[2], body[3]]
        models["like%d" % (len(models) + 1)] = m
    if not models: print("test: nothing to build"); return True
    job = {"worklib": L, "tiow": None if PC else REPO + "/addons/tiow_inbox.py", "out": W + "/test", "new": "NEW/", "models": models,
           "nocut": [os.path.basename(nb(p)) for p in tl]}
    jd(job, W + "/test_job.json", indent=0)
    if os.path.exists(W + "/test/results.json"): os.remove(W + "/test/results.json")
    r = run_bpy(REPO + "/tests/creator/t_creator.py", W + "/test_job.json", addons=True)
    R = jl(W + "/test/results.json") if os.path.exists(W + "/test/results.json") else None
    if R is None: sys.exit(r.stdout[-1500:] + r.stderr[-1500:])
    for x in R["parts"]: print("  %s %-34s %-6s closest %.2f, cut %.2f" % (x["model"], x["part"][:34], x["socket"], x["closest"], x["cut"]))
    print("test: %s; pictures in %s" % ("all ok" if not R["fails"] else "FAILS %s" % R["fails"], W + ("/test/" if PC else "/test/test.jpg")))
    return not R["fails"]


# ---------------------------------------------------------------- build
def bl_preview(stl, k, target):
    """a light copy of the part for the page, by Blender's Decimate: what Prepare makes on the PC
    (squad-builder/prepare_builder.py), for when this runs inside Blender"""
    import bpy, numpy as np
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import('EXEC_DEFAULT', filepath=stl)
    ob = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    try:
        tris = sum(len(q.vertices) - 2 for q in ob.data.polygons)
        if tris > target:
            ob.modifiers.new("preview", 'DECIMATE').ratio = max(0.001, target / tris)
        dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles()
        V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V)
        Tr = np.empty(len(me.loop_triangles) * 3, dtype=np.int32); me.loop_triangles.foreach_get("vertices", Tr)
        ev.to_mesh_clear()
        return V.reshape(-1, 3) * k, Tr.reshape(-1, 3)
    finally:
        me_ = ob.data; bpy.data.objects.remove(ob)
        if me_.users == 0: bpy.data.meshes.remove(me_)


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
    build_index.build(ML, preview_fn=bl_preview if PC else None)
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
    O = OUT % c["task"]; shutil.rmtree(O, ignore_errors=True); os.makedirs(O)
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
        if not PC and os.path.getsize(O + "/" + f) > SPLIT:          # too big for one device_commit_files: parts, joined by apply
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
    if PC: return O
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


# ---------------------------------------------------------------- on the PC: one command
def recipes():
    return sorted(glob.glob(HERE + "/*.json"))


def pc_setup(recipe, src=None, task=None):
    """the recipe with this run's folder and task name, its work folder, and the survey done in place"""
    import on_pc
    if not recipe:
        R = recipes()
        for i, f in enumerate(R): print("  %d  %s  (%s)" % (i + 1, os.path.basename(f)[:-5], jl(f).get("root", "")))
        a = input("Which maker's recipe? number: ").strip().lstrip(chr(0xfeff))
        if not a.isdigit() or not 1 <= int(a) <= len(R): sys.exit("no recipe chosen: nothing done")
        recipe = R[int(a) - 1]
    elif not os.path.isfile(recipe): recipe = HERE + "/" + recipe + ("" if recipe.endswith(".json") else ".json")
    c = jl(recipe); c.setdefault("scale", 1.0); c.setdefault("padlift", True)
    c.setdefault("path", "{root}\\{category}\\{prefix} - {name}.stl")
    c.setdefault("date", time.strftime("%b ") + str(int(time.strftime("%d"))))
    if src:
        a = os.path.abspath(src).replace("\\", "/")
        if a.lower().startswith(U.lower()): src = a[len(U):]
        src = src.replace("\\", "/").strip("/")
        if not os.path.isdir(U + src): sys.exit("the folder has to be inside %s: %s" % (U, src))
        c["src"] = src
    name = os.path.basename(recipe)[:-5]
    if not task:
        task = "%s-%s" % (name, time.strftime("%Y-%m-%d")); n = 1
        while os.path.exists(LIBU + "_backups/" + task): n += 1; task = "%s-%s-%d" % (name, time.strftime("%Y-%m-%d"), n)
    c["task"] = task; W = WORK % task; os.makedirs(W + "/base", exist_ok=True)
    on_pc.set_roots(U.rstrip("/"), LIBU.rstrip("/"), os.path.join(ROOTS["page"], "build_index.py"))
    if not os.path.exists(W + "/survey.json"):
        on_pc.survey([c["src"], task])
        shutil.copyfile(LIBU + "_backups/" + task + "/stage/survey.json", W + "/survey.json")
        for st in STATE:
            if os.path.exists(LIBU + st): shutil.copyfile(LIBU + st, W + "/base/" + st.replace("/", "__"))
    jd(c, W + "/config.json", indent=1)
    return c, W


def mesh_faults(c, W):
    """the new files with open / non-manifold edges or flipped faces (library-tools/caliper_swap.py's test): told, not
    stopped; Caliper Repair.bat mends them once they are in the library"""
    sys.path.insert(0, REPO + "/library-tools"); import caliper_swap as CS
    P = jl(W + "/plan.json"); out = {}
    for p in P:
        h, V, T = CS.load(U + p["rel"])
        if V is None or not len(T): continue
        f = CS.faults(T)
        if any(f.values()): out[p["rel"]] = f
    jd(out, W + "/faults.json", indent=0)
    print("mesh faults: %d of %d new files%s" % (len(out), len(P), "" if not out else " (run Caliper Repair.bat on the library folder afterwards): "
          + ", ".join(os.path.basename(r)[:-4] for r in list(out)[:8]) + (" ..." if len(out) > 8 else "")))


def pc_check(c, W):
    """plan -> faults -> sheet -> fit -> test. None when the library already has every file, else the test's
    failed checks (an empty list when all passed)"""
    P = plan(c, W, skip_have=True)
    if not P:
        print("nothing new: the library already has every STL in " + c["src"])
        shutil.rmtree(LIBU + "_backups/" + c["task"], ignore_errors=True)      # this run's own, just made
        return None
    mesh_faults(c, W); sheet(c, W); fit(c, W)
    if test(c, W): return []
    return jl(W + "/test/results.json")["fails"]


def pc_finish(c, W, rec=True):
    """build -> check -> apply (backups in _backups\\TASK\\before) -> the sidecars and rows into the repo clone"""
    import on_pc
    on_pc.set_roots(U.rstrip("/"), LIBU.rstrip("/"), os.path.join(ROOTS["page"], "build_index.py"))
    O = build(c, W)
    on_pc.apply([O, "--check"]); on_pc.apply([O])
    if rec:
        record(c, W); print("the sidecars and rows are in the repo clone, not committed yet")
    print("added to %s%s; the Squad Builder shows the new parts on its next load" % (LIBU, c["root"]))


def pc_main(A):
    flag = lambda f: f in A
    opt = lambda f: A[A.index(f) + 1] if f in A else None
    pos = [a for i, a in enumerate(A[1:]) if not a.startswith("--") and A[i] not in ("--src", "--task")]
    cmd = A[0]
    if cmd == "recipes":
        for f in recipes(): print("%-28s %s" % (os.path.basename(f)[:-5], jl(f).get("root", "")))
    elif cmd == "add":
        c, W = pc_setup(pos[0] if pos else None, opt("--src"), opt("--task"))
        fails = pc_check(c, W)
        if fails is None: return
        P = jl(W + "/plan.json")
        if fails:
            print("%d test check(s) did not pass. The parts can still go in and be put right in Blender with Save Correction:" % len(fails))
            for f in fails: print("   " + f)
        if flag("--dry"): print("dry run: nothing added. To add them: finish %s" % c["task"]); return
        if flag("--yes"):
            if fails and not flag("--force"): sys.exit("stopped at the failed checks (pictures in %s/test). To add them anyway: finish %s" % (W, c["task"]))
        else:
            if not flag("--no-open"):
                for f in [W + "/sheet_front.png"] + sorted(glob.glob(W + "/test/*_front.png"))[:3]:
                    if os.path.exists(f): os.startfile(f.replace("/", "\\"))
            print("sheet and test pictures: " + W.replace("/", "\\"))
            if input("Add these %d parts to the library? [y/N] " % len(P)).strip().lstrip(chr(0xfeff)).lower() not in ("y", "yes"):
                print("nothing added. To add them later: finish %s" % c["task"]); return
        pc_finish(c, W, not flag("--no-record"))
    elif cmd == "finish":
        W = WORK % pos[0]; c = jl(W + "/config.json")
        pc_finish(c, W, not flag("--no-record"))


def main(A):
    cmd = A[0] if A else ""
    if PC and cmd in ("add", "finish", "recipes"): return pc_main(A)
    if len(A) < 2: sys.exit(__doc__)
    arg = A[1]
    if cmd == "unpack": unpack(arg); return
    c, W = load_cfg(arg)
    if cmd == "go":
        plan(c, W); sheet(c, W); fit(c, W)
        if not test(c, W): sys.exit("stopped: a test check failed (look at test/test.jpg; fix the config or gates, or run build anyway)")
        build(c, W)
    else:
        {"plan": plan, "sheet": sheet, "fit": fit, "test": test, "build": build, "record": record, "sidecars": sidecars}[cmd](c, W)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    try:
        main(A)
    except SystemExit as e:              # inside Blender a message given to sys.exit is not printed
        if isinstance(e.code, str):
            print(e.code); sys.exit(1)
        raise
