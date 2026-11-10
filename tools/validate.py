#!/usr/bin/env python3
"""Checks to pass before every commit (CI runs the same). Standard library only, a few seconds.

  python3 tools/validate.py [--all]

  - every library sidecar parses, has a known category, well-formed rigid matrices, 'exact' naming real fits
    (and survives a merge with itself unchanged)
  - library/_sources.csv lists a row per sidecar'd part and ends in CRLF
  - no meshes or other blocked files are tracked (STL, OBJ, blend, npz, previews...)
  - nothing identifying: Windows user folders, e-mail addresses (tools/private_words.txt, untracked, adds your own)
  - joints.json agrees with the add-on, the bridge template, partTypes.json and the page
  - addons/tiow_inbox.py equals its sections
Without --all only files changed against origin/main are scanned for identifying text (the sidecar and table checks
always run in full: they are fast)."""
import csv, json, os, re, subprocess, sys
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, R)
from kb import sidecar

BLOCKED = re.compile(r"\.(stl|obj|3mf|blend|blend1|npz|npy|bin|kbp)$", re.I)
PRIVATE = [re.compile(r"[A-Za-z]:\\+Users\\+(?!<|\{|%|you\b|name\b|user\b)[^\\\s\"']+", re.I),
           re.compile(r"/(?:home|Users)/(?!claude\b|runner\b|user\b)[A-Za-z][\w.-]+/"),
           re.compile(r"[\w.+-]+@(?!anthropic\.com|example\.)[\w-]+\.(?:com|net|org|io|uk|co\.uk|me)\b", re.I)]


def git(*a): return subprocess.run(["git", "-C", R] + list(a), capture_output=True, text=True).stdout


def main():
    bad = []
    J = json.load(open(os.path.join(R, "joints.json"), encoding="utf-8"))
    types = set(J["joints"]) | set(J["noJoint"])
    tracked = [f for f in git("ls-files", "-z").split("\0") if f]
    # sidecars
    n = 0
    for f in tracked:
        if not (f.startswith("library/") and f.endswith(sidecar.SUFFIX)): continue
        n += 1
        try:
            d, st = sidecar.load(os.path.join(R, f))
        except Exception as e:
            bad.append("%s: unreadable (%s)" % (f, e)); continue
        ps = [p for p in sidecar.problems(d, types) if p != "schemaVersion isn't 1"]   # 34 early files lack it; TIOW doesn't mind
        if sidecar.merge(d, d)[0] != d: ps.append("changes when merged with itself")
        bad += ["%s: %s" % (f, p) for p in ps]
    # _sources.csv
    src = os.path.join(R, "library", "_sources.csv")
    raw = open(src, "rb").read()
    if not raw.endswith(b"\r\n"): bad.append("library/_sources.csv doesn't end in CRLF")
    # blocked files
    bad += ["tracked but blocked: " + f for f in tracked if BLOCKED.search(f)]
    # identifying text
    words = []
    pw = os.path.join(R, "tools", "private_words.txt")
    if os.path.exists(pw): words = [w.strip() for w in open(pw, encoding="utf-8") if w.strip() and not w.startswith("#")]
    scan = tracked if "--all" in sys.argv else [f for f in (git("diff", "--name-only", "origin/main") +
                                                          git("ls-files", "-o", "--exclude-standard")).split("\n") if f]
    for f in scan:
        p = os.path.join(R, f)
        if not os.path.isfile(p) or os.path.getsize(p) > 5e6: continue
        try: t = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError): continue
        for rx in PRIVATE:
            m = rx.search(t)
            if m: bad.append("%s: looks identifying: %r" % (f, m.group(0)[:60]))
        low = t.lower()
        bad += ["%s: has a private word" % f for w in words if w.lower() in low]
    for tool in ("gen_joints.py", "build_addon.py"):
        r = subprocess.run([sys.executable, os.path.join(R, "tools", tool), "--check"], capture_output=True, text=True)
        if r.returncode: bad.append("%s --check: %s" % (tool, r.stdout.strip().replace("\n", "; ")[-300:]))
    if bad:
        print("\n".join(bad[:40]) + ("\n... %d more" % (len(bad) - 40) if len(bad) > 40 else "")); sys.exit(1)
    print("ok: %d sidecars, %d tracked files, tables and add-on sections in step" % (n, len(tracked)))


if __name__ == "__main__":
    main()
