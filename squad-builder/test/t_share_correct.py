"""share_server.py /correct: only the owner's sign-in saves a fit; the sockets file changes in that fit and "exact" only;
backed up once; logged; stale or malformed saves refused. Then the page in shared mode saves through it.
    python3 t_share_correct.py INDEX_JSON REPO_LIBRARY_DIR [PREVIEWS_DIR]
Makes its own throwaway library and users (test passwords), runs the server on port 8791."""
import base64, json, os, shutil, subprocess, sys, tempfile, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); SB = os.path.dirname(HERE)
INDEX, REPO_LIB = sys.argv[1], sys.argv[2]; PREV = sys.argv[3] if len(sys.argv) > 3 else None
T = tempfile.mkdtemp(); lib = os.path.join(T, "lib"); os.makedirs(os.path.join(lib, "_builder"))
shutil.copy(INDEX, os.path.join(lib, "_builder", "index.json")); open(os.path.join(lib, "_hidden.txt"), "w").close()
if PREV: os.symlink(PREV, os.path.join(lib, "_builder", "previews"))
idx = json.load(open(INDEX, encoding="utf-8")); by = {p["name"]: p for p in idx["parts"]}
sword, arm = by["MarFil Assault - Chain Sword 1 R"], by["MarFil Assault - Arm 1B R"]
def sc(p): return p["path"].replace("\\", "/")[:-4] + ".sockets.json"
for p in (sword, arm):
    os.makedirs(os.path.dirname(os.path.join(lib, sc(p))), exist_ok=True); shutil.copy(os.path.join(REPO_LIB, sc(p)), os.path.join(lib, sc(p)))
users = os.path.join(T, "users.json"); srv = os.path.join(SB, "share_server.py")
for n, pw in (("owner1", "test-owner-pass-1"), ("friend1", "test-friend-pass-1")):
    subprocess.run([sys.executable, srv, "--users", users, "--add-user", n, "--password-stdin"], input=pw + "\n", text=True, check=True, capture_output=True)
fails = 0
def ck(label, ok, detail=None):
    global fails; print(("  ok   " if ok else "  FAIL ") + label + ("" if ok else "  " + repr(detail))); fails += not ok
out = subprocess.run([sys.executable, srv, "--users", users, "--list-users"], capture_output=True, text=True).stdout
ck("until an owner is set, the first person added is the owner", "owner1  (owner" in out and "friend1  (owner" not in out, out)
subprocess.run([sys.executable, srv, "--users", users, "--owner", "friend1"], check=True, capture_output=True)
subprocess.run([sys.executable, srv, "--users", users, "--owner", "owner1"], check=True, capture_output=True)
u = json.load(open(users)); ck("--owner marks one person only", u["owner1"].get("owner") is True and "owner" not in u["friend1"], u)
proc = subprocess.Popen([sys.executable, srv, "--users", users, "--lib", lib, "--libpath", "D:\\Kitbash Library", "--port", "8791"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(1.2)
def call(path, user, pw, body=None):
    r = urllib.request.Request("http://127.0.0.1:8791" + path, data=None if body is None else json.dumps(body).encode(), method="GET" if body is None else "POST")
    r.add_header("Authorization", "Basic " + base64.b64encode(("%s:%s" % (user, pw)).encode()).decode())
    if body is not None: r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r) as f: return f.status, f.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
O, F = ("owner1", "test-owner-pass-1"), ("friend1", "test-friend-pass-1")
try:
    path = os.path.join(lib, sc(sword)); orig = open(path, "rb").read(); d0 = json.loads(orig.decode("utf-8-sig"))
    before = d0["fits"]["Hand R"]; c, s_ = 0.9396926208, 0.3420201433
    after = [c, 0, s_, before[3] + 0.4, 0, 1, 0, before[7], -s_, 0, c, before[11], 0, 0, 0, 1]
    fix = {"part": sword["path"], "name": sword["name"], "v": None, "sock": "Hand R", "host": arm["path"], "before": before, "after": after, "mm": 0.4, "deg": 20}
    ck("someone else's sign-in can't save a fit (403), and nothing changes", call("/correct", *F, fix)[0] == 403 and open(path, "rb").read() == orig)
    ck("no sign-in, no save (401)", call("/correct", "owner1", "wrong-password-x", fix)[0] == 401)
    st, _ = call("/correct", *O, fix); new = open(path, "rb").read(); d1 = json.loads(new.decode("utf-8-sig"))
    ck("the owner's save is written (200): fit and exact", st == 200 and all(abs(a - b) < 1e-9 for a, b in zip(d1["fits"]["Hand R"], after)) and "Hand R" in d1["exact"], st)
    strip = lambda d: {k: (dict((a, b) for a, b in v.items() if a != "Hand R") if k == "fits" else v) for k, v in d.items() if k != "exact"}
    la, lb = orig.decode().splitlines(), new.decode().splitlines()
    ck("nothing else in the file changes; untouched lines keep their text", strip(d0) == strip(d1) and len([l for l in lb if l not in la]) <= 20 and (b"\r\n" in orig) == (b"\r\n" in new))
    bdir = os.path.join(lib, "_backups", "page-corrections", time.strftime("%Y-%m-%d"), sc(sword))
    ck("the old file is backed up", os.path.exists(bdir) and open(bdir, "rb").read() == orig)
    log = [json.loads(l) for l in open(os.path.join(lib, "_builder", "corrections.jsonl"), encoding="utf-8")]
    ck("one log line: who, part, socket, before, after", len(log) == 1 and log[0]["by"] == "owner1" and log[0]["part"] == sword["path"] and log[0]["sock"] == "Hand R" and log[0]["before"] == before)
    ck("saving the same again is fine", call("/correct", *O, fix)[0] == 200)
    stale = dict(fix, before=[1, 0, 0, 9, 0, 1, 0, 9, 0, 0, 1, 9, 0, 0, 0, 1], after=[1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1])
    ck("a save made from an out-of-date page is refused (409)", call("/correct", *O, stale)[0] == 409 and open(path, "rb").read() == new)
    for label, bad in (("a part that isn't in the library", dict(fix, part="..\\..\\Windows\\x.stl")), ("a fit that isn't a rigid placement", dict(fix, after=[2] * 16)),
                       ("a socket name with odd characters", dict(fix, sock="Hand R/../x")), ("a copy that doesn't exist", dict(fix, v=9))):
        ck("refused (400): " + label, call("/correct", *O, bad)[0] == 400 and open(path, "rb").read() == new)
    apath = os.path.join(lib, sc(arm)); a0 = json.loads(open(apath, "rb").read().decode("utf-8-sig")); vb = a0["variants"][0]["sidecar"]["fits"]["Shoulder L"]
    va = vb[:3] + [vb[3] + 0.3] + vb[4:]
    st, _ = call("/correct", *O, {"part": arm["path"], "v": 0, "sock": "Shoulder L", "before": vb, "after": va}); a1 = json.loads(open(apath, "rb").read().decode("utf-8-sig"))
    ck("a maker's copy is saved in its own entry", st == 200 and a1["variants"][0]["sidecar"]["fits"]["Shoulder L"][3] == round(va[3], 9) and a1["fits"] == a0["fits"] and "Shoulder L" in a1["variants"][0]["sidecar"]["exact"], st)
    ck("everyone signed in can read the corrections log (the page replays it)", call("/lib/_builder/corrections.jsonl", *F)[0] == 200)
    sys.path.insert(0, os.path.join(SB, "..")); from kb import sidecar
    d, style = sidecar.load(path); ck("the library tools read the saved file and write it back identically", not [p for p in sidecar.problems(d) if "schema" not in p] and sidecar.dumps(d, style) == new)
    if PREV:                                   # the page, shared: Save fit goes through the server
        r = subprocess.run(["node", os.path.join(HERE, "t_share_adjust.js"), "http://127.0.0.1:8791/", O[0], O[1], F[0], F[1]], capture_output=True, text=True)
        print(r.stdout.rstrip()); fails += r.returncode != 0
        d2 = json.loads(open(path, "rb").read().decode("utf-8-sig")); log = [json.loads(l) for l in open(os.path.join(lib, "_builder", "corrections.jsonl"), encoding="utf-8")]
        ck("the page's save reached the sockets file and the log", any(abs(a - b) > 1e-6 for a, b in zip(d2["fits"]["Hand R"], after)) and log[-1]["sock"] == "Hand R" and log[-1]["by"] == "owner1" and abs(log[-1]["deg"] - 7) < 0.01, log[-1].get("deg"))
finally:
    proc.terminate(); shutil.rmtree(T, ignore_errors=True)
print("FAILS: %d" % fails if fails else "all passed"); sys.exit(1 if fails else 0)
