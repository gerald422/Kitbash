#!/usr/bin/env python3
"""kb/ keeps its promises: merge never loses Josh's or Prepare's work, sidecars stay byte-identical through
load / save, and a delivery is applied only onto the files the work started from (backed up first).

    python3 tests/kb/t_kb.py

Standard library only, no Blender, about a second; tools/validate.py (and so CI) runs it. Exit code 1 on a failure."""
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, R)
from kb import deliver, sidecar

fails, count = [], [0]


def ok(cond, what):
    count[0] += 1
    if not cond: fails.append(what)


def M(x=0.0):
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def S(t, x, **props):
    return dict({"type": t, "matrix": M(x)}, **({"props": props} if props else {}))


def at(d, t, holds=""):
    return [s["matrix"][3] for s in d["sockets"] if s["type"] == t and str((s.get("props") or {}).get("tiow_holds") or "") == holds]


# ---------------------------------------------------------------- merge
old = {"schemaVersion": 1, "category": "Arms", "upright": M(9),
       "sockets": [S("Pad", 1, tiow_anchor="clicked"), S("Hand", 2), S("Wrist", 3, tiow_corrected=True),
                   S("Elbow", 4, tiow_anchor="copied"), S("Cuff", 5, tiow_anchor="auto"), S("Grip", 6, tiow_anchor="pose"),
                   S("Spot", 7, tiow_holds="A"), S("Old Only", 8)],
       "fits": {"Arm R": M(1), "Arm L": M(2)}, "exact": ["Arm R"], "notes": {"Arm R": "by hand", "Arm L": "old rule"},
       "variants": [{"name": "Left", "side": "L", "sidecar": {"fits": {"Arm L": M(1)}, "exact": ["Arm L"]}},
                    {"name": "Gone", "side": "R", "sidecar": {"fits": {"Arm R": M(5)}}}]}
new = {"schemaVersion": 1, "category": "Melee",
       "sockets": [S("Pad", 11), S("Hand", 12), S("Wrist", 13), S("Elbow", 14), S("Cuff", 15), S("Grip", 16),
                   S("Spot", 17, tiow_holds="A"), S("Spot", 18, tiow_holds="B"), S("Neck", 19)],
       "fits": {"Arm R": M(21), "Arm L": M(22), "Torso": M(23)}, "exact": ["Torso"], "notes": {"Arm L": "new rule"},
       "variants": [{"name": "Left", "side": "L", "sidecar": {"fits": {"Arm L": M(31), "Arm R": M(32)}}},
                    {"name": "Extra", "side": "L", "sidecar": {"fits": {"Arm L": M(33)}}}]}
o0, n0 = copy.deepcopy(old), copy.deepcopy(new)
m, kept = sidecar.merge(new, old)
ok(old == o0 and new == n0, "merge changed what it was given")
for t, x in (("Pad", 1), ("Wrist", 3), ("Elbow", 4), ("Cuff", 5)):
    ok(at(m, t) == [x], "merge lost a clicked / corrected / copied / auto socket: " + t)
ok(at(m, "Spot", "A") == [7], "merge lost a socket that holds a part")
ok(at(m, "Spot", "B") == [18], "merge dropped a new spot beside a held one of the same type")
ok(at(m, "Hand") == [12] and at(m, "Grip") == [16], "merge kept an unprotected socket instead of the new one")
ok(at(m, "Old Only") == [8] and at(m, "Neck") == [19], "merge lost a socket only one side has")
ok([s["type"] for s in m["sockets"]][:3] == ["Pad", "Hand", "Wrist"], "merge reordered the old sockets")
ok(m["fits"]["Arm R"] == M(1), "merge replaced a fit placed by hand (exact)")
ok(m["fits"]["Arm L"] == M(22) and m["fits"]["Torso"] == M(23), "merge didn't take the new fits")
ok(m["exact"] == ["Arm R", "Torso"], "exact isn't the union")
ok(m["notes"] == {"Arm R": "by hand", "Arm L": "new rule"}, "notes don't follow their fits")
ok(m["upright"] == M(9) and m["category"] == "Melee", "top-level keys: old ones must stay, new ones replace")
ok("socket Pad" in kept and "fit Arm R (exact)" in kept, "merge doesn't report what of the old it kept")
v = {x["name"]: x for x in m["variants"]}
ok(set(v) == {"Left", "Gone", "Extra"}, "merge lost a variant")
ok(v["Left"]["sidecar"]["fits"] == {"Arm L": M(1), "Arm R": M(32)}, "a variant's exact fit was replaced")
ok(sidecar.merge(new, None) == (new, []) and sidecar.merge(new, None)[0] is not new, "merge into nothing isn't a copy of new")
ok(sidecar.merge(m, m)[0] == m, "a merged sidecar changes when merged with itself")
ok(sidecar.problems(m, {"Melee"}) == [], "the merged sidecar has problems: %s" % sidecar.problems(m, {"Melee"}))

# ---------------------------------------------------------------- problems
bad = {"schemaVersion": 1, "category": "Nope", "fits": {"A": [2.0] + M()[1:]}, "exact": ["B"], "sockets": [{"matrix": M()}]}
p = " | ".join(sidecar.problems(bad, {"Arms"}))
for word in ("known part type", "orthonormal", "no fit", "no type"):
    ok(word in p, "problems() misses: " + word)

# ---------------------------------------------------------------- load / save keep the bytes
T = tempfile.mkdtemp(prefix="t_kb_")
try:
    d = {"schemaVersion": 1, "category": "Arms", "part": "Café – Arm", "fits": {"Arm R": M(1.5)}}
    for name, raw in (("lf", json.dumps(d, indent=1, ensure_ascii=False).encode("utf-8")),
                      ("lf-newline", (json.dumps(d, indent=1, ensure_ascii=False) + "\n").encode("utf-8")),
                      ("crlf", json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n").encode("utf-8")),
                      ("escaped", json.dumps(d, indent=1, ensure_ascii=True).encode("utf-8")),
                      ("escaped-crlf", (json.dumps(d, indent=1, ensure_ascii=True) + "\n").replace("\n", "\r\n").encode("utf-8"))):
        f = os.path.join(T, name + sidecar.SUFFIX)
        open(f, "wb").write(raw)
        got, style = sidecar.load(f)
        ok(got == d, "load reads %s wrongly" % name)
        sidecar.save(f, got)
        ok(open(f, "rb").read() == raw, "save doesn't keep a %s file byte for byte" % name)
        got["fits"]["Arm R"] = M(2.5); sidecar.save(f, got)
        back = open(f, "rb").read()
        ok((b"\r\n" in back) == (b"\r\n" in raw) and back.endswith(b"\n") == raw.endswith(b"\n")
           and (b"\\u00e9" in back) == (b"\\u00e9" in raw), "a changed %s file loses its newline / escaping style" % name)

    # ------------------------------------------------------------ deliver + kb.py apply
    lib, nc = os.path.join(T, "lib"), os.path.join(T, "nc")
    os.makedirs(os.path.join(lib, "_builder")); os.makedirs(nc)
    put = lambda root, rel, b: open(os.path.join(root, *rel.split("/")), "wb").write(b)
    get = lambda root, rel: open(os.path.join(root, *rel.split("/")), "rb").read()
    md5 = lambda b: hashlib.md5(b).hexdigest()
    put(lib, "_builder/index.json", b"index 1"); put(lib, "_sources.csv", b"a,b\r\n"); put(nc, "maker.bin", b"mesh")
    env = dict(os.environ, KB_ROOT_LIB=lib, KB_ROOT_NC=nc, KB_ROOT_BRIDGE=os.path.join(T, "bridge"), KB_ROOT_ADDONS=os.path.join(T, "addons"))

    def make(task, index_base=b"index 1"):
        out = os.path.join(T, task)
        D = deliver.Delivery(task, out)
        D.new("lib", "Bits/X/Part.sockets.json", b"{}")
        D.replace("lib", "_builder/index.json", b"index 2", md5(index_base))
        D.append("lib", "_sources.csv", b"c,d\r\n", md5(b"a,b\r\n"), b"a,b\r\n")
        D.copy("nc", "maker.bin", "lib", "Bits/X/Part.bin", md5(b"mesh"))
        D.build()
        return out

    def run(*a):
        r = subprocess.run([sys.executable, os.path.join(R, "tools", "kb.py"), "apply"] + list(a), env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    out = make("t1")
    code, text = run(out, "--check")
    ok(code == 0 and "1 new, 1 copied on the PC, 1 replaced, 1 added to" in text, "apply --check: " + text.strip())
    ok(get(lib, "_builder/index.json") == b"index 1" and not os.path.exists(os.path.join(lib, "Bits")), "apply --check wrote something")
    code, text = run(out)
    ok(code == 0 and "every md5 matches" in text, "apply: " + text.strip())
    ok(get(lib, "_builder/index.json") == b"index 2" and get(lib, "_sources.csv") == b"a,b\r\nc,d\r\n"
       and get(lib, "Bits/X/Part.sockets.json") == b"{}" and get(lib, "Bits/X/Part.bin") == b"mesh", "apply wrote the wrong contents")
    B = os.path.join(lib, "_backups", "t1", "before", "lib")
    ok(get(B, "_builder/index.json") == b"index 1" and get(B, "_sources.csv") == b"a,b\r\n", "apply didn't back up what it replaced")
    code, text = run(out)
    ok(code == 0 and "4 already in place" in text, "applying the same delivery twice isn't a no-op: " + text.strip())
    ok(get(lib, "_sources.csv") == b"a,b\r\nc,d\r\n", "a second apply appended again")
    put(lib, "_builder/index.json", b"edited on the PC"); put(lib, "Bits/X/Part.sockets.json", b'{"his": 1}')
    code, text = run(make("t2"))
    ok(code != 0 and "changed since the work started" in text and "already there with other contents" in text,
       "apply didn't refuse files changed on the PC: " + text.strip())
    ok(get(lib, "_builder/index.json") == b"edited on the PC" and get(lib, "Bits/X/Part.sockets.json") == b'{"his": 1}',
       "a refused apply still wrote")
    pay = os.path.join(out, "payload-00.tgz"); open(pay, "ab").write(b"x")
    code, text = run(out, "--check")
    ok(code != 0 and "damaged" in text, "apply accepted a damaged payload")
finally:
    shutil.rmtree(T, ignore_errors=True)

if fails:
    print("%d of %d kb checks failed:\n  %s" % (len(fails), count[0], "\n  ".join(fails))); sys.exit(1)
print("all %d kb checks pass" % count[0])
