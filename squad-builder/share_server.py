"""Share Squad Builder with a few people, each with their own username and password (see README.txt, "Sharing").

Serves only the page, the library's _builder\\index.json, its previews, _hidden.txt and the corrections log - never
an STL - to people who sign in. The owner's "Save fit" (Adjust) is written into that part's sockets file and the
corrections log, as the page does on this PC; everyone else's lasts only for their visit. Their "Send for printing" is checked against the index (library parts only) and saved under
<library>\\_builder\\received\\<name>\\<date-time>\\, as the same request files the page writes when you press
Send to Blender, so you choose when Blender builds them (--build). Listens on this PC only (127.0.0.1); a tunnel such
as cloudflared gives it an https address to share. Python's standard library only (Blender's own Python will do).

  python share_server.py --add-user NAME         set or change a password (asked for, stored hashed)
  python share_server.py --remove-user NAME
  python share_server.py --list-users
  python share_server.py --owner NAME            whose sign-in may save fits from the page's Adjust (one person;
                                                 until it is set, the first name added)
  python share_server.py [--lib "D:\\Kitbash Library"] [--port 8765]          run it (Ctrl+C stops)
  python share_server.py --build [NAME]          the newest received models (anyone's, or NAME's) into
                                                 _builder\\inbox, where Blender with TIOW Inbox builds them
"""
import argparse, base64, getpass, hashlib, hmac, json, os, re, secrets, shutil, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "Squad Builder.html")
USERS = os.path.join(HERE, "share_users.json")
ITER = 240000                      # PBKDF2-SHA256 rounds per password check (then cached for the session)
MAX_BODY = 512 * 1024              # one send: at most 512 KB ...
MAX_REQS = 400                     # ... and 400 parts
SENDS_PER_HOUR = 30                # per person
FAILS, LOCK_MIN = 8, 15            # 8 wrong passwords within 10 minutes locks that address out for 15 minutes
PREVIEW = re.compile(r"^/lib/_builder/previews/[0-9a-f]{6,64}\.bin$")
NAME_OK = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
MAX_FIX = 64 * 1024                # one saved fit
SOCKET_OK = re.compile(r"^[A-Za-z0-9 ]{1,40}$")
KEYS = ("schemaVersion", "path", "name", "title", "category", "tags", "itemId", "sentAt", "model", "socket", "at")


# ------------------------------------------------------------------ users
def load_users(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_users(path, users):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=1)
    os.replace(tmp, path)


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    return {"salt": salt, "iter": ITER, "hash": hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), ITER).hex()}


def check_pw(rec, pw):
    h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(rec["salt"]), int(rec["iter"])).hex()
    return hmac.compare_digest(h, rec["hash"])


# ------------------------------------------------------------------ the library
class Library:
    def __init__(self, lib, libpath):
        self.lib, self.libpath = lib, libpath
        self.index_file = os.path.join(lib, "_builder", "index.json")
        self._mt, self._parts = None, {}
        self.lock = threading.Lock()

    def parts(self):
        """request path (as the page builds it, lower case) -> index entry; re-read when Prepare changes the index"""
        with self.lock:
            mt = os.path.getmtime(self.index_file)
            if mt != self._mt:
                with open(self.index_file, encoding="utf-8") as f:
                    idx = json.load(f)
                self._parts = {(self.libpath.rstrip("\\/") + "\\" + p["path"]).lower(): p for p in idx["parts"]}
                self._mt = mt
            return self._parts


def clean_requests(body, lib, user):
    """the requests to save, or raise ValueError: only parts in the index, only the fields the page sends"""
    reqs = body.get("requests") if isinstance(body, dict) else None
    if not isinstance(reqs, list) or not 0 < len(reqs) <= MAX_REQS:
        raise ValueError("nothing to send")
    parts, out = lib.parts(), []
    for r in reqs:
        if not isinstance(r, dict):
            raise ValueError("bad request")
        p = parts.get(str(r.get("path", "")).lower())
        if p is None:
            raise ValueError("not a library part: " + str(r.get("name", ""))[:60])
        if str(r.get("category", "")) != p.get("type"):
            raise ValueError("wrong type for " + p["name"])
        q = {k: r[k] for k in KEYS if k in r}
        q["path"] = lib.libpath.rstrip("\\/") + "\\" + p["path"]
        q["name"] = q["title"] = p["name"]
        q["tags"], q["itemId"], q["schemaVersion"] = [], "", 1
        if "socket" in q and not (isinstance(q["socket"], str) and SOCKET_OK.match(q["socket"])):
            raise ValueError("bad socket")
        if "at" in q:
            at = q["at"]
            if not (isinstance(at, list) and len(at) == 3 and all(isinstance(x, (int, float)) and abs(x) < 1e5 for x in at)):
                raise ValueError("bad position")
        model = re.sub(r"[^A-Za-z0-9_.-]", "", str(q.get("model", "")))[:60]
        q["model"] = user + "-" + (model or "squad")
        q["sentAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        out.append(q)
    return out


def owner_of(users):
    """the one name whose sign-in may save fits: the one marked, else the first added"""
    marked = [n for n, r in users.items() if isinstance(r, dict) and r.get("owner")]
    return marked[0] if marked else next(iter(users), None)


def _near(a, b):
    return isinstance(a, list) and isinstance(b, list) and len(a) == len(b) == 16 and all(abs(x - y) <= 1e-6 for x, y in zip(a, b))


def save_fit(lib, c, user):
    """One fit saved from the page's Adjust: into the part's sockets file (fits + exact) and the corrections log.
    Returns the log line, or raises ValueError (bad request) / RuntimeError (the file has changed, or isn't as expected).
    Only library parts, only that one fit; the file is otherwise rewritten exactly as it was, and backed up once a day."""
    if not isinstance(c, dict):
        raise ValueError("bad request")
    p = lib.parts().get((lib.libpath.rstrip("\\/") + "\\" + str(c.get("part", ""))).lower())
    if p is None:
        raise ValueError("not a library part")
    sock, v, after, before = c.get("sock"), c.get("v"), c.get("after"), c.get("before")
    if not (isinstance(sock, str) and SOCKET_OK.match(sock)) or not (v is None or (isinstance(v, int) and not isinstance(v, bool) and 0 <= v < 64)):
        raise ValueError("bad socket")
    ok = isinstance(after, list) and len(after) == 16 and all(isinstance(x, (int, float)) and not isinstance(x, bool) and abs(x) < 1e4 for x in after)
    if ok:
        r = [after[0:3], after[4:7], after[8:11]]
        ok = [round(x, 6) for x in after[12:]] == [0, 0, 0, 1] and all(
            abs(sum(r[k][i] * r[k][j] for k in range(3)) - (1.0 if i == j else 0.0)) < 2e-3 for i in range(3) for j in range(3))
    if not ok:
        raise ValueError("bad fit")
    after = [float(round(x, 9)) + 0.0 for x in after]
    rel = re.split(r"[\\/]", re.sub(r"\.stl$", "", p["path"], flags=re.I) + ".sockets.json")
    path = os.path.join(lib.lib, *rel)
    with lib.lock:
        try:
            raw = open(path, "rb").read()
        except FileNotFoundError:
            raw = None
        if raw is None:
            d, crlf, end, asc = {"schemaVersion": 1, "part": p["name"]}, False, "", False
        else:
            text = raw.decode("utf-8-sig")
            body = text.replace("\r\n", "\n")
            d, crlf, end = json.loads(body), "\r\n" in text, "\n" if body.endswith("\n") else ""
            asc = next((a for a in (False, True) if json.dumps(d, indent=1, ensure_ascii=a) == body.rstrip("\n")), None)
            if asc is None or raw.startswith(b"\xef\xbb\xbf"):
                raise RuntimeError("that part's sockets file isn't in the usual form: save this one on the PC")
        sub = d
        if v is not None:
            try:
                sub = d["variants"][v].setdefault("sidecar", {})
            except (KeyError, IndexError, TypeError, AttributeError):
                raise ValueError("no such copy of that part")
        fits = sub.setdefault("fits", {})
        cur = fits.get(sock)
        if cur is not None and not _near(cur, before) and not _near(cur, after):
            raise RuntimeError("that fit has changed since the page loaded it: reload the page and try again")
        if raw is not None:
            b = os.path.join(lib.lib, "_backups", "page-corrections", time.strftime("%Y-%m-%d"), *rel)
            if not os.path.exists(b):
                os.makedirs(os.path.dirname(b), exist_ok=True)
                with open(b, "wb") as f:
                    f.write(raw)
        fits[sock] = after
        ex = sub.setdefault("exact", [])
        if sock not in ex:
            ex.append(sock)
        out = json.dumps(d, indent=1, ensure_ascii=bool(asc)) + end
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "wb") as f:
            f.write((out.replace("\n", "\r\n") if crlf else out).encode("utf-8"))
        os.replace(path + ".tmp", path)
        line = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "by": user, "part": p["path"], "name": str(c.get("name", ""))[:120], "v": v, "sock": sock,
                "host": c.get("host") if isinstance(c.get("host"), str) and len(c["host"]) < 400 else None,
                "before": before if isinstance(before, list) and len(before) == 16 and all(isinstance(x, (int, float)) for x in before) else None, "after": after,
                "mm": c.get("mm") if isinstance(c.get("mm"), (int, float)) else None, "deg": c.get("deg") if isinstance(c.get("deg"), (int, float)) else None}
        with open(os.path.join(lib.lib, "_builder", "corrections.jsonl"), "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return line


def save_received(lib, user, reqs):
    when = time.strftime("%Y-%m-%d_%H%M%S")
    d = os.path.join(lib.lib, "_builder", "received", user, when)
    os.makedirs(d, exist_ok=True)
    stamp = int(time.time() * 1000)
    for i, r in enumerate(reqs):
        with open(os.path.join(d, "sb-%d-%03d.json" % (stamp, i)), "w", encoding="utf-8") as f:
            json.dump(r, f, separators=(",", ":"), ensure_ascii=False)
    return d


def build(lib, who=None):
    """copy the newest received models (anyone's, or who's) into _builder\\inbox; marks the folder .built"""
    root = os.path.join(lib, "_builder", "received")
    sets = []
    for u in (os.listdir(root) if os.path.isdir(root) else []):
        if who and u.lower() != who.lower():
            continue
        for s in os.listdir(os.path.join(root, u)):
            d = os.path.join(root, u, s)
            if os.path.isdir(d) and not os.path.exists(os.path.join(d, ".built")):
                sets.append((s, u, d))
    if not sets:
        print("Nothing new in", root)
        return
    s, u, d = max(sets)
    inbox = os.path.join(lib, "_builder", "inbox")
    os.makedirs(inbox, exist_ok=True)
    fs = sorted(f for f in os.listdir(d) if f.endswith(".json"))
    for f in fs:
        shutil.copyfile(os.path.join(d, f), os.path.join(inbox, f))
    open(os.path.join(d, ".built"), "w").close()
    print("%d parts from %s (%s) put in %s: Blender with TIOW Inbox builds them now." % (len(fs), u, s, inbox))
    if len(sets) > 1:
        print("%d more received set(s) waiting: run it again for the next." % (len(sets) - 1))


# ------------------------------------------------------------------ the server
class State:
    def __init__(self, lib, users_file):
        self.lib, self.users_file = lib, users_file
        self.sessions = {}                 # sha256(Authorization header) -> (user, expiry)
        self.fails = {}                    # address -> [times]
        self.locked = {}                   # address -> until
        self.sends = {}                    # user -> [times]
        self.lock = threading.Lock()


def make_handler(st):
    class H(BaseHTTPRequestHandler):
        server_version = "SquadBuilderShare"
        sys_version = ""

        def log_message(self, fmt, *args):          # quiet: only sign-in failures and sends are printed
            pass

        def addr(self):
            return self.headers.get("CF-Connecting-IP") or self.client_address[0]

        def send_plain(self, code, text, extra=None):
            b = text.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.common()
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(b)

        def common(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")

        def who(self):
            """the signed-in name, or None after answering 401 / 429"""
            a, now = self.addr(), time.time()
            with st.lock:
                if st.locked.get(a, 0) > now:
                    self.send_plain(429, "Too many wrong passwords: try again later.")
                    return None
            h = self.headers.get("Authorization", "")
            key = hashlib.sha256(h.encode("utf-8")).hexdigest()
            with st.lock:
                s = st.sessions.get(key)
                if s and s[1] > now:
                    return s[0]
            user = None
            if h.startswith("Basic "):
                try:
                    name, pw = base64.b64decode(h[6:], validate=True).decode("utf-8").split(":", 1)
                    rec = load_users(st.users_file).get(name)
                    if rec and check_pw(rec, pw):
                        user = name
                except (ValueError, UnicodeDecodeError):
                    pass
            if user:
                with st.lock:
                    st.sessions[key] = (user, now + 12 * 3600)
                    st.fails.pop(a, None)
                return user
            if h:
                with st.lock:
                    t = [x for x in st.fails.get(a, []) if x > now - 600] + [now]
                    st.fails[a] = t
                    if len(t) >= FAILS:
                        st.locked[a] = now + LOCK_MIN * 60
                        print(time.strftime("%H:%M:%S"), "locked out", a, "for", LOCK_MIN, "minutes")
                print(time.strftime("%H:%M:%S"), "wrong password from", a)
            self.send_plain(401, "Sign in to use Squad Builder.", {"WWW-Authenticate": 'Basic realm="Squad Builder", charset="UTF-8"'})
            return None

        def file(self, path, ctype, cache):
            try:
                size = os.path.getsize(path)
                f = open(path, "rb")
            except OSError:
                return self.send_plain(404, "Not found")
            with f:
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", cache)
                self.common()
                self.end_headers()
                if self.command != "HEAD":
                    shutil.copyfileobj(f, self.wfile, 256 * 1024)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if self.who() is None:
                return
            path = unquote(urlsplit(self.path).path)
            lib = st.lib.lib
            if path == "/":
                q = "share=1&lib=/lib/&libpath=" + quote(st.lib.libpath, safe="")
                self.send_response(302)
                self.send_header("Location", "/Squad%20Builder.html?" + q)
                self.send_header("Content-Length", "0")
                self.common()
                self.end_headers()
            elif path == "/Squad Builder.html":
                self.file(PAGE, "text/html; charset=utf-8", "no-store")
            elif path == "/lib/_builder/index.json":
                self.file(os.path.join(lib, "_builder", "index.json"), "application/json", "private, no-cache")
            elif path == "/lib/_builder/corrections.jsonl":
                self.file(os.path.join(lib, "_builder", "corrections.jsonl"), "text/plain; charset=utf-8", "private, no-cache")
            elif path == "/lib/_hidden.txt":
                self.file(os.path.join(lib, "_hidden.txt"), "text/plain; charset=utf-8", "private, no-cache")
            elif PREVIEW.match(path):
                self.file(os.path.join(lib, "_builder", "previews", path.rsplit("/", 1)[1]), "application/octet-stream", "private, max-age=86400")
            else:
                self.send_plain(404, "Not found")

        def do_POST(self):
            user = self.who()
            if user is None:
                return
            what = urlsplit(self.path).path
            if what not in ("/send", "/correct"):
                return self.send_plain(404, "Not found")
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                n = -1
            if what == "/correct":             # a fit saved from Adjust: the owner's sign-in only
                if user != owner_of(load_users(st.users_file)):
                    return self.send_plain(403, "Saving fits needs the owner's sign-in.")
                if not 0 < n <= MAX_FIX:
                    return self.send_plain(413, "Too big.")
                try:
                    line = save_fit(st.lib, json.loads(self.rfile.read(n).decode("utf-8")), user)
                except (ValueError, UnicodeDecodeError) as e:
                    return self.send_plain(400, str(e))
                except RuntimeError as e:
                    return self.send_plain(409, str(e))
                print(time.strftime("%H:%M:%S"), "%s saved a fit: %s on %s" % (user, line["part"], line["sock"]))
                return self.send_plain(200, "saved")
            if not 0 < n <= MAX_BODY:
                return self.send_plain(413, "Too big to send.")
            now = time.time()
            with st.lock:
                t = [x for x in st.sends.get(user, []) if x > now - 3600]
                if len(t) >= SENDS_PER_HOUR:
                    return self.send_plain(429, "That's a lot of sends this hour: try again later.")
                st.sends[user] = t + [now]
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                reqs = clean_requests(body, st.lib, user)
            except (ValueError, UnicodeDecodeError) as e:
                return self.send_plain(400, str(e))
            d = save_received(st.lib, user, reqs)
            models = len({r["model"] for r in reqs})
            print(time.strftime("%H:%M:%S"), "%s sent %d parts for %d model(s): %s" % (user, len(reqs), models, d))
            b = json.dumps({"parts": len(reqs), "models": models}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.common()
            self.end_headers()
            self.wfile.write(b)

    return H


def main():
    ap = argparse.ArgumentParser(description="Share Squad Builder with a username and password per person.")
    ap.add_argument("--lib", default=r"D:\Kitbash Library", help="the Kitbash Library folder")
    ap.add_argument("--libpath", help="the library path written in the requests (default: --lib)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--users", default=USERS, help=argparse.SUPPRESS)
    ap.add_argument("--add-user", metavar="NAME")
    ap.add_argument("--password-stdin", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--remove-user", metavar="NAME")
    ap.add_argument("--list-users", action="store_true")
    ap.add_argument("--owner", metavar="NAME", help="whose sign-in may save fits from Adjust")
    ap.add_argument("--build", nargs="?", const="", metavar="NAME")
    a = ap.parse_args()
    if a.add_user is not None:
        if not NAME_OK.match(a.add_user):
            sys.exit("Names: letters, numbers, . _ - (up to 32).")
        if a.password_stdin:
            pw = sys.stdin.readline().rstrip("\r\n")
        else:
            pw = getpass.getpass("Password for %s: " % a.add_user)
            if pw != getpass.getpass("Again: "):
                sys.exit("The passwords don't match: nothing changed.")
        if len(pw) < 10:
            sys.exit("Use at least 10 characters: nothing changed.")
        u = load_users(a.users)
        was_owner = isinstance(u.get(a.add_user), dict) and u[a.add_user].get("owner")
        u[a.add_user] = hash_pw(pw)
        if was_owner:
            u[a.add_user]["owner"] = True
        save_users(a.users, u)
        print("Saved", a.add_user, "(%d people can sign in)." % len(u))
        return
    if a.remove_user:
        u = load_users(a.users)
        print("Removed" if u.pop(a.remove_user, None) else "No such name:", a.remove_user)
        save_users(a.users, u)
        return
    if a.owner:
        u = load_users(a.users)
        if a.owner not in u:
            sys.exit("No such name: add them first with --add-user " + a.owner)
        for n, r in u.items():
            r.pop("owner", None)
        u[a.owner]["owner"] = True
        save_users(a.users, u)
        print(a.owner, "may now save fits from the shared page. Nobody else can.")
        return
    if a.list_users:
        u = load_users(a.users)
        print("\n".join(n + ("  (owner: may save fits)" if n == owner_of(u) else "") for n in sorted(u)) or "Nobody yet: add people with --add-user NAME")
        return
    if a.build is not None:
        return build(a.lib, a.build or None)
    if not load_users(a.users):
        sys.exit("Nobody can sign in yet: add people first with --add-user NAME.")
    lib = Library(a.lib, a.libpath or a.lib)
    lib.parts()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(State(lib, a.users)))
    srv.daemon_threads = True
    print("Squad Builder shared on http://localhost:%d (this PC only; the tunnel gives the https address)." % a.port)
    print("People:", ", ".join(sorted(load_users(a.users))), "- Ctrl+C or close this window to stop sharing.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
