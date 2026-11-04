"""Share Squad Builder with a few people, each with their own username and password (see README.txt, "Sharing").

Serves only the page, the library's _builder\\index.json, its previews and _hidden.txt - never an STL - to people
who sign in. Their "Send for printing" is checked against the index (library parts only) and saved under
<library>\\_builder\\received\\<name>\\<date-time>\\, as the same request files the page writes when you press
Send to Blender, so you choose when Blender builds them (--build). Listens on this PC only (127.0.0.1); a tunnel such
as cloudflared gives it an https address to share. Python's standard library only (Blender's own Python will do).

  python share_server.py --add-user NAME         set or change a password (asked for, stored hashed)
  python share_server.py --remove-user NAME
  python share_server.py --list-users
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
            if urlsplit(self.path).path != "/send":
                return self.send_plain(404, "Not found")
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                n = -1
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
        u[a.add_user] = hash_pw(pw)
        save_users(a.users, u)
        print("Saved", a.add_user, "(%d people can sign in)." % len(u))
        return
    if a.remove_user:
        u = load_users(a.users)
        print("Removed" if u.pop(a.remove_user, None) else "No such name:", a.remove_user)
        save_users(a.users, u)
        return
    if a.list_users:
        print("\n".join(sorted(load_users(a.users))) or "Nobody yet: add people with --add-user NAME")
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
