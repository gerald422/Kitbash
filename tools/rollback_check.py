"""Roll-back check (notes 140): every joint written from a batch since stage 1 (props.kb_josh sockets, exact fits)
against the library now. Run with any Python 3 on the PC: python tools/rollback_check.py"""
import subprocess, json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); L = "D:/Kitbash Library"
git = lambda *a: subprocess.run(["git", "-C", R] + list(a), capture_output=True, text=True, encoding="utf-8").stdout
commits = git("log", "--reverse", "--format=%h", "b64b58fc~1..HEAD", "--", "library").split()
def joints(d, var=""):
    out = {}
    for s in d.get("sockets") or []:
        if (s.get("props") or {}).get("kb_josh"): out[(var, "socket", s["type"])] = s["matrix"]
    for t in d.get("exact") or []:
        if t in (d.get("fits") or {}): out[(var, "fit", t)] = d["fits"][t]
    for v in d.get("variants") or []:
        if isinstance(v.get("sidecar"), dict): out.update(joints(v["sidecar"], v.get("name", "?")))
    return out
first = {}
for c in commits:
    for f in git("diff-tree", "--no-commit-id", "--name-only", "-r", c, "--", "library").splitlines():
        if not f.endswith(".sockets.json"): continue
        txt = git("show", "%s:%s" % (c, f))
        if not txt.strip(): continue
        for k, m in joints(json.loads(txt.lstrip("\ufeff"))).items():
            first.setdefault((f,) + k, (c, m))
bad, n = [], 0
for (f, var, kind, t), (c, m) in first.items():
    p = os.path.join(L, f[len("library/"):]); d = json.load(open(p, encoding="utf-8-sig")); now = joints(d)
    n += 1; m2 = now.get((var, kind, t))
    if m2 is None: bad.append("GONE   %s %s %s %s (first %s)" % (f[-60:], var, kind, t, c))
    elif max(abs(a - b) for a, b in zip(m, m2)) > 1e-6: bad.append("CHANGED %s %s %s %s (first %s)" % (f[-60:], var, kind, t, c))
print("%d commits, %d written joints checked against D:, %d rolled back or gone" % (len(commits), n, len(bad)))
print("\n".join(bad[:40]))
