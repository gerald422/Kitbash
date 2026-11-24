"""Write a proving run's joints into the library (docs/PLAN.md, the write step): the numbers prove.py found from Josh's
cuts become each part's sockets (hosts) and fits (children), so the Squad Builder and TIOW Inbox use them.

    PY kits/connectors/write_joints.py RESULTS.json [MORE.json ...] [--lib LIB] [--skip FILE] [--dry] [--yes] [--drop-old MAKER,MAKER]
    PY kits/connectors/seat.py -- restore          (undo: puts back what the last write changed; Josh's later saves stay)
  PY = Blender's own python (numpy), e.g. "C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe"

- RESULTS: prove.py's results.json; a later file wins for a part both list (a heads run after a full run).
- What is written: a child's fit where the run gave one (sure, or near: then flagged), a host's socket where it gave one
  (sure only, prove.py's rule), each torso's Shoulder L (the right one mirrored about its waist frame), each leg's
  Shin R / Shin L. Left files were searched mirrored (prove.py --left) and come with their own left numbers.
- A mirror copy kept inside a right part's sidecar (a variant, "mirror": true) takes the right numbers mirrored
  (mirror x right x mirror, R and L swapped), only where its old numbers were that already.
- Near fits are listed in the sidecar's "check" (the page flags the part until it is corrected by hand: "exact").
- Not touched: parts the run found nothing on (they keep what they have, listed), fits Josh corrected by hand
  ("exact"), protected sockets (clicked / copied anchors: kb.sidecar.merge), the SKIP list (default
  kits/connectors/marfil_write_skip.txt: what the sheets showed wrong).
- --drop-old MAKERS (Nov 24, Josh): the makers' arms and pads keep only new-method joints (strip_old): every other
  shoulder fit, wrist (Hand) socket, pad socket and pad fit is removed, hand corrections included, even where the
  run gives nothing new (listed in the report as left without).
- Backups in _backups/connectors-joints-DATE/before (sidecars and the page index), as seat.py's, so its restore works."""
import sys, os, json, time, shutil, hashlib, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO); sys.path.insert(0, HERE)
from kb import sidecar as SC
import seat as S

MX = np.diag([-1.0, 1, 1, 1])
M4 = lambda a: np.array(a, float).reshape(4, 4)
def flat(M): return [round(float(x), 6) for x in np.asarray(M).reshape(-1)]
def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()
def opt(A, n, d=None): return A[A.index(n) + 1] if n in A else d
def swap(t): return t[:-2] + (" L" if t.endswith(" R") else " R") if t.endswith((" R", " L")) else t
SAME = 2e-3          # a variant's old numbers count as the mirror of its part's when they agree this closely
REPLACE = ("copied", "auto")   # anchors made by earlier tools (copied across kits, worked out): the cuts replace them
                               # (docs/PLAN.md: host-side cuts replace old sockets); clicked / corrected / held ones stay


def unprotect(old, types):
    """old with its copied / auto anchors of these types made ordinary, so the merge replaces them; -> (old, replaced)"""
    o = json.loads(json.dumps(old)); rep = []
    for s in o.get("sockets") or []:
        p = s.get("props") or {}
        if s.get("type") in types and p.get("tiow_anchor") in REPLACE and not p.get("tiow_corrected") and not p.get("tiow_holds"):
            rep.append("%s (%s)" % (s["type"], p.pop("tiow_anchor")))
    return o, rep


def skips(path):
    """lines 'TYPE<tab>PATH TEXT[<tab>near]': that type's parts whose path holds the text are not written (near: only
    their near fits). '#' starts a comment."""
    out = []
    if path and os.path.exists(path):
        for l in open(path, encoding="utf-8-sig"):
            l = l.split("#")[0].rstrip()
            if l.strip():
                f = [x.strip() for x in l.split("\t")]; out.append((f[0], f[1], len(f) > 2 and f[2] == "near"))
    return out


def plan_part(r, sc_file, G, back, skip):
    """what the run's numbers write into one part: (new {fits, notes, sockets}, check list, what was left out)"""
    fits, notes, socks, check, left_out = {}, {}, [], [], []
    tofile_fit = (lambda F: F) if back is None else (lambda F: F @ back)          # maker coordinates -> the file as it is now
    tofile_sock = (lambda M: M) if G is None else (lambda M: G @ M)
    day = time.strftime("%b %d").replace(" 0", " "); sk = [s for s in skip if s[0] == r["cat"] and s[1] in r["rel"]]
    J = r.get("joints") or {}
    for jk, d in sorted(J.items()):
        jn, role = jk.split(":")
        if jk == "shin:host":
            for sn, sd in sorted((d.get("sides") or {}).items()):
                if "matrix" not in sd: continue
                socks.append({"type": sn, "matrix": flat(tofile_sock(M4(sd["matrix"]))), "cut": sd.get("cut") or d.get("cut"), "level": sd.get("level")})
                if sd.get("note"): check.append(sn)
            continue
        if "matrix" not in d: continue
        near = d.get("level") != "sure" or bool(d.get("note"))
        if role == "child":
            if any(not s[2] or near for s in sk): left_out.append("%s (skip list)" % d.get("fit")); continue
            k = d["fit"]; fits[k] = flat(tofile_fit(M4(d["matrix"])))
            notes[k] = "cut %s, %s (%.4f mm, %.0f%% on), write_joints %s%s" % (d.get("cut"), d.get("level"), d.get("match") or 0, 100 * (d.get("cover") or 0),
                                                                              day, ": NEAR, check by eye" + (" (" + d["note"] + ")" if d.get("note") else "") if near else "")
            if near: check.append(k)
        else:
            socks.append({"type": d["socket"], "matrix": flat(tofile_sock(M4(d["matrix"]))), "cut": d.get("cut"), "level": d.get("level")})
            if near: check.append(d["socket"])
    if r["cat"] == "Chests" and "matrix" in J.get("shoulder:host", {}) and "matrix" in J.get("waist:host", {}):
        Sw, Sr = M4(J["waist:host"]["matrix"]), M4(J["shoulder:host"]["matrix"])     # Shoulder L: the right mirrored about the waist
        socks.append({"type": "Shoulder L", "matrix": flat(tofile_sock(Sw @ MX @ np.linalg.inv(Sw) @ Sr @ MX)), "cut": J["shoulder:host"].get("cut") + " (mirrored)", "level": J["shoulder:host"].get("level")})
    new = {}
    if fits: new["fits"], new["notes"] = fits, notes
    if socks:
        name = sc_file.get("part") or os.path.basename(r["rel"])
        new["sockets"] = [{"type": s["type"], "name": "%s_socket_%s" % (name, s["type"]), "matrix": s["matrix"],
                           "props": {"tiow_from": "cut %s, %s (write_joints %s)" % (s["cut"], s["level"], day)}} for s in socks]
    return new, check, left_out


def mirror_variants(new, check, sc_file):
    """the mirror copies inside the sidecar ("mirror": true, the part's mesh mirrored in its file coordinates): the new
    numbers mirrored (mirror x right x mirror, R and L swapped). Checked once per copy: its old fit must be its part's
    old fit mirrored (the library's convention; Nov 19: all agree to 0.0), else the copy is left as it is. Old sockets
    that weren't mirrors (copied anchors) are replaced all the same, as on the part."""
    out, notes = [], []
    for v in sc_file.get("variants") or []:
        vs = v.get("sidecar")
        if not v.get("mirror") or not isinstance(vs, dict): continue
        pairs = [(M4(m), M4((vs.get("fits") or {})[swap(k)])) for k, m in (sc_file.get("fits") or {}).items() if swap(k) in (vs.get("fits") or {})]
        if pairs and min(np.abs(b - MX @ a @ MX).max() for a, b in pairs) > SAME:
            notes.append("variant %s: its old fit isn't its part's mirrored: left as it is" % v.get("name")); continue
        vf = {swap(k): flat(MX @ M4(m) @ MX) for k, m in (new.get("fits") or {}).items()}; ok = list(vf)
        vsock = {s.get("type"): s for s in vs.get("sockets") or []}; vsk = []
        for s in new.get("sockets") or []:
            if s["type"] == "Shoulder L": continue
            t2 = swap(s["type"]); b = vsock.get(t2)
            vsk.append(dict(s, type=t2, name=((b or {}).get("name") or s["name"].replace(s["type"], t2)), matrix=flat(MX @ M4(s["matrix"]) @ MX))); ok.append(t2)
        if not (vf or vsk): continue
        sub = {}
        if vf: sub["fits"] = vf; sub["notes"] = {k: (new.get("notes") or {}).get(swap(k), "") + " (mirrored)" for k in vf}
        if vsk: sub["sockets"] = vsk
        vc = sorted({swap(t) for t in check if swap(t) in ok} | {t for t in vs.get("check") or [] if t not in ok})
        if vc or vs.get("check"): sub["check"] = vc
        out.append({"name": v.get("name"), "side": v.get("side"), "sidecar": sub})
    return out, notes


def cut_made(new, vars_, kept):
    """The joints this write made from the cuts, for the page's cut-only list (_builder/cut_only.json): the part's own
    and each mirror copy's, less what the merge kept of the old sidecar (protected sockets, exact fits)."""
    k = {x.split(" (")[0] for x in kept or []}
    e = {"fits": sorted(t for t in new.get("fits") or {} if "fit " + t not in k),
         "sockets": sorted({s["type"] for s in new.get("sockets") or []} - {x[7:] for x in k if x.startswith("socket ")})}
    vs = {"%s|%s" % (v.get("name"), v.get("side")): {"fits": sorted(v["sidecar"].get("fits") or {}), "sockets": sorted({s["type"] for s in v["sidecar"].get("sockets") or []})}
          for v in vars_ or []}
    if vs: e["variants"] = vs
    return e


def keep_list(lib, cutj):
    """Add this write's parts to _builder/cut_only.json (a part written again takes its new list). Returns whether the
    page is in cut-only mode ("on", Josh's switch; a new list starts off)."""
    p = lib + "/_builder/cut_only.json"
    d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"on": False, "about": "the parts and joints the cuts made (write_joints.py); "
        "'on': true shows only these on the Squad Builder (Josh, Nov 19), false shows everything"}
    d.setdefault("parts", {}).update({rel.replace("/", "\\") + ".stl": e for rel, e in cutj.items()})
    tmp = p + ".tmp"; json.dump(d, open(tmp, "w", encoding="utf-8"), indent=1, sort_keys=True); os.replace(tmp, p)
    return bool(d.get("on"))


DROP_SOCK = ("Hand R", "Hand L", "Pad R", "Pad L")          # --drop-old: the arm and pad joints the new method makes
DROP_FIT = ("Shoulder R", "Shoulder L", "Pad R", "Pad L")
DROP_CATS = ("Arms", "Shoulder Pads")


def new_method(t, text):
    """made by the new method: a pad joint from the guide seats (the auto pad spot cuts, the pad's pose in the guide);
    a shoulder / wrist from a cut write (write_joints). The Nov 20 pad joints were cut-made but in the old pad frame."""
    text = str(text or "")
    return ("guide" in text or "(auto)" in text) if t.startswith("Pad") else "write_joints" in text


def strip_old(d):
    """--drop-old (Nov 24, Josh: "remove all of the old fits ... this is the method we want to use going forward"): takes
    out of a sidecar (and its mirror copies) every arm / pad joint the new method didn't make, hand corrections
    ("exact") included (they were in the old pad frame). Returns what it removed, as 'socket T' / 'fit T (exact)'."""
    out = []
    def one(x, pre):
        keep = []
        for sk in x.get("sockets") or []:
            t = sk.get("type")
            if t in DROP_SOCK and not new_method(t, (sk.get("props") or {}).get("tiow_from")): out.append(pre + "socket " + t); continue
            keep.append(sk)
        if "sockets" in x: x["sockets"] = keep
        ex = x.get("exact") or []
        for t in list((x.get("fits") or {})):
            if t in DROP_FIT and not new_method(t, (x.get("notes") or {}).get(t)):
                x["fits"].pop(t); (x.get("notes") or {}).pop(t, None); out.append(pre + "fit " + t + (" (exact)" if t in ex else ""))
        if ex: x["exact"] = [t for t in ex if t in (x.get("fits") or {})]
        if x.get("check"): x["check"] = [t for t in x["check"] if t in (x.get("fits") or {}) or any(sk.get("type") == t for sk in x.get("sockets") or [])]
    one(d, "")
    for v in d.get("variants") or []:
        if isinstance(v.get("sidecar"), dict): one(v["sidecar"], "copy %s: " % v.get("name"))
    return out


def in_scope(rel, d, makers): return rel.split("/")[0] in makers and d.get("category") in DROP_CATS


def drop_rest(lib, makers, plan, w):
    """the in-scope sidecars this write doesn't otherwise touch: their old arm / pad joints removed (added to the plan,
    so backed up and restorable with the rest). Returns the report lines."""
    cnt = collections.Counter(); exact = []; bare = collections.Counter()
    for mk in makers:
        for root, _dirs, files in os.walk(lib + "/" + mk):
            if "_backups" in root.replace("\\", "/").split("/"): continue
            for f in files:
                if not f.endswith(SC.SUFFIX): continue
                rel = os.path.relpath(os.path.join(root, f), lib).replace("\\", "/")[:-len(SC.SUFFIX)]
                if rel in plan: d = plan[rel][0]; gone = plan[rel][2] if len(plan[rel]) > 2 else []
                else:
                    d, style = SC.load(lib + "/" + rel + SC.SUFFIX)
                    if not in_scope(rel, d, makers): continue
                    gone = strip_old(d)
                    if gone: plan[rel] = (d, style); w("  drop old   %-70s %s" % (rel.split("/", 1)[1][:70], ", ".join(gone)))
                if not in_scope(rel, d, makers): continue
                for g in gone: cnt[(mk.split(" -")[0], g.split(": ")[-1].replace(" (exact)", "").rsplit(" ", 1)[0])] += 1
                exact += [rel.split("/")[-1] + " " + g for g in gone if "(exact)" in g]
                fl = d.get("fits") or {}; sk = {x.get("type") for x in d.get("sockets") or []}
                if d.get("category") == "Arms":
                    if not any(t in fl for t in ("Shoulder R", "Shoulder L")): bare[(mk.split(" -")[0], "arms with no shoulder fit")] += 1
                    if not sk & {"Pad R", "Pad L"}: bare[(mk.split(" -")[0], "arms with no pad socket")] += 1
                    if not sk & {"Hand R", "Hand L"}: bare[(mk.split(" -")[0], "arms with no wrist socket")] += 1
                elif not any(t in fl for t in ("Pad R", "Pad L")): bare[(mk.split(" -")[0], "pads with no fit")] += 1
    out = ["", "Old arm / pad joints removed (--drop-old): " + ", ".join("%s %s %d" % (m, j, n) for (m, j), n in sorted(cnt.items()))]
    if exact: out.append("Hand corrections removed (old pad frame): " + "; ".join(exact))
    out.append("Left without (until their cuts are fixed): " + ", ".join("%s %s %d" % (m, j, n) for (m, j), n in sorted(bare.items())))
    return out


def main(A):
    lib = opt(A, "--lib", "D:/Kitbash Library"); res = [a for a in A if a.endswith(".json") and not a.startswith("--")]
    skip_path = opt(A, "--skip", os.path.join(HERE, "marfil_write_skip.txt")); skip = skips(skip_path)
    by = {}
    for f in res:
        for r in json.load(open(f, encoding="utf-8"))["results"]: by[r["rel"]] = r          # a later run wins
    task = "connectors-joints-" + time.strftime("%Y-%m-%d"); k = 1
    while os.path.exists(lib + "/_backups/" + task): k += 1; task = "connectors-joints-%s-%d" % (time.strftime("%Y-%m-%d"), k)
    T = lib + "/_backups/" + task
    W, plan, cnt, cutj, made = [], {}, collections.Counter(), {}, {}
    makers = [m for m in (opt(A, "--drop-old") or "").split(",") if m]
    w = W.append
    for rel, r in sorted(by.items()):
        path = lib + "/" + rel + SC.SUFFIX
        if r.get("error") or not os.path.exists(path): cnt["unreadable"] += 1; w("  unreadable  %s %s" % (rel, r.get("error", "")[:80])); continue
        old, style = SC.load(path); _, G, back = S.maker(path)
        new, check, left_out = plan_part(r, old, G, back, skip)
        written = set(new.get("fits") or {}) | {s["type"] for s in new.get("sockets") or []}
        ck = sorted(set(check) | {t for t in old.get("check") or [] if t not in written})
        if ck or old.get("check"): new["check"] = ck
        vars_, vnotes = mirror_variants(new, check, old) if (new.get("fits") or new.get("sockets")) else ([], [])
        if vars_: new["variants"] = vars_
        none = [jk for jk, d in (r.get("joints") or {}).items() if "matrix" not in d and jk != "shin:host" and not (jk.endswith(":host") and d.get("level") == "look")]
        hostnear = [jk for jk, d in (r.get("joints") or {}).items() if jk.endswith(":host") and jk != "shin:host" and "matrix" not in d and d.get("level") == "look"]
        if not (new.get("fits") or new.get("sockets")):
            cnt["nothing to write"] += 1; w("  nothing     %-70s %s" % (rel.split("/", 1)[1][:70], ", ".join(none + hostnear + left_out))); continue
        old2, replaced = unprotect(old, {s["type"] for s in new.get("sockets") or []})
        gone = strip_old(old2) if makers and in_scope(rel, old, makers) else []   # before the merge: no old exact fit outlives it
        vrep = []
        for v in old2.get("variants") or []:
            if isinstance(v.get("sidecar"), dict) and any(x["name"] == v.get("name") and x["side"] == v.get("side") for x in vars_):
                v["sidecar"], rp = unprotect(v["sidecar"], {s["type"] for x in vars_ if x["name"] == v.get("name") for s in x["sidecar"].get("sockets") or []}); vrep += rp
        merged, kept = SC.merge(new, old2); was = SC.problems(old); bad = [x for x in SC.problems(merged) if x not in was]
        cnt["replaced anchors"] += len(replaced) + len(vrep)
        if bad: cnt["refused"] += 1; w("  REFUSED     %s: %s" % (rel, bad[:2])); continue
        plan[rel] = (merged, style, gone); made[rel] = (written, kept or [])
        cutj[rel] = cut_made(new, vars_, kept)
        cnt[r["cat"]] += 1; cnt["fits"] += len(new.get("fits") or {}); cnt["sockets"] += len(new.get("sockets") or []); cnt["near"] += len(check)
        cnt["variants"] += len(vars_)
        extra = [x for x in (["kept: " + ", ".join(kept)] if kept else []) + (["replaced " + ", ".join(replaced)] if replaced else []) + (["not found: " + ", ".join(none)] if none else []) +
                 (["host near only, not written: " + ", ".join(hostnear)] if hostnear else []) + (["left out: " + ", ".join(left_out)] if left_out else []) + vnotes +
                 (["old dropped: " + ", ".join(gone)] if gone else [])]
        w("  %-11s %-70s %s%s" % ("NEAR" if check else "write", rel.split("/", 1)[1][:70], ", ".join(sorted(written)), ("   [" + "; ".join(extra) + "]") if extra else ""))
    conv = drop_rest(lib, makers, plan, w) if makers else None
    head = ["Write joints: %s  (%d parts in %s)" % (task, len(by), ", ".join(os.path.basename(os.path.dirname(f)) for f in res)), "",
            "Will write %d parts: %d fits, %d sockets (%d near, flagged), %d mirror copies inside sidecars; %d copied / auto anchors replaced." % (len(plan), cnt["fits"], cnt["sockets"], cnt["near"], cnt["variants"], cnt["replaced anchors"]),
            "By type: " + ", ".join("%s %d" % (t, cnt[t]) for t in sorted({r["cat"] for r in by.values()}) if cnt[t]),
            "Left as they are: %d parts with nothing found, %d unreadable, %d refused (the merge would break the sidecar)." % (cnt["nothing to write"], cnt["unreadable"], cnt["refused"]),
            "Skip list: %s (%d lines)" % (skip_path, len(skip))] + (conv or []) + [""]
    text = "\r\n".join(head + W) + "\r\n"
    os.makedirs(T, exist_ok=True); open(T + "/report.txt", "wb").write(text.encode("utf-8"))
    print("\n".join(head)); print("The full list: %s/report.txt" % T)
    if "--dry" in A: print("dry run: nothing written"); return
    if "--yes" not in A:
        try: os.startfile(os.path.normpath(T + "/report.txt"))
        except (AttributeError, OSError): pass
        if input("Write these %d parts into the library? [y/N] " % len(plan)).strip().lstrip(chr(0xfeff)).lower() not in ("y", "yes"): print("nothing written"); return
    from kb.index import Index
    B = T + "/before"; wrote = {}
    for rel, (merged, style, *_g) in plan.items():
        path = lib + "/" + rel + SC.SUFFIX; b = B + "/" + rel + SC.SUFFIX
        os.makedirs(os.path.dirname(b), exist_ok=True); shutil.copyfile(path, b)
        SC.save(path, merged, style); wrote[rel] = md5(path)
    ip = lib + "/_builder/index.json"; cl = lib + "/_builder/cut_only.json"; note = ""
    os.makedirs(B + "/_builder", exist_ok=True)
    for f in (ip, cl):
        if os.path.exists(f): shutil.copyfile(f, B + "/_builder/" + os.path.basename(f))
    on = keep_list(lib, {r: cutj[r] for r in wrote if r in cutj})   # a part only stripped (--drop-old) keeps its list
    try:
        if on:                                      # the page shows only what the cuts made: the whole index again
            sys.path.insert(0, os.path.join(REPO, "squad-builder")); import build_index
            build_index.build(lib, previews=False); note = "page index rebuilt (cut-only)"
        else:
            idx = Index.load(ip); n = 0
            for rel in wrote:
                kk = rel.replace("/", "\\") + ".stl"
                if kk in idx.by_path: idx.update_part(kk, SC.load(lib + "/" + rel + SC.SUFFIX)[0]); n += 1
            open(ip, "wb").write(idx.dumps()); note = "page index: %d parts refreshed" % n
    except (ValueError, OSError) as ex: note = "page index NOT refreshed (%s): run Prepare" % ex
    json.dump({"wrote": wrote, "index": md5(ip) if os.path.exists(ip) else None}, open(T + "/written.json", "w", encoding="utf-8"), indent=1)
    print("wrote %d sidecars (backups in %s); %s" % (len(wrote), B.replace("/", "\\"), note))
    print('To undo: "Seat connectors.bat" restore   (or seat.py -- restore %s)' % task)


if __name__ == "__main__":
    A = sys.argv[1:]
    if not A or A[0] in ("-h", "--help"): print(__doc__)
    else: main(A)
