"""Move library parts to another armour mark folder (Nov 9: Marta's thicc/termi parts filed under Tacticus or Gravis ->
Terminator, the heavy sets filed under Tacticus -> Gravis) and carry every reference along, so Prepare needn't redo them:
the STL + sidecar, _sources.csv (first column), _builder/index.json (path, id = sha1(path.lower())[:12], prev; the
preview file is renamed), _builder/anchors_done.txt, _builder/no_fit.txt, _hidden.txt; each move is logged in
_renamed.csv ("moved (armour mark)"). Text files keep their bytes (BOM, CRLF) apart from the changed paths; back them up
first (--backup DIR). No deletes: files are renamed.
    python3 move_marks.py LIBRARY MOVES.json --backup DIR [--dry]
MOVES.json: [[old library path, new library path, type], ...] (backslashes, as in _sources.csv)."""
import hashlib, json, os, shutil, sys

LIB, MV = sys.argv[1], sys.argv[2]
DRY = "--dry" in sys.argv
BK = sys.argv[sys.argv.index("--backup") + 1]
moves = [(a, b) for a, b, *_ in json.load(open(MV, encoding="utf-8"))]
old2new = dict(moves)
assert len(old2new) == len(moves)


def fs(p):
    return os.path.join(LIB, *p.split("\\"))


def pid(p):
    return hashlib.sha1(p.lower().encode("utf-8")).hexdigest()[:12]


# 1. checks
for a, b in moves:
    assert os.path.isfile(fs(a)), a
    assert not os.path.exists(fs(b)), b
texts = ["_sources.csv", "_hidden.txt", "_renamed.csv", "_builder/anchors_done.txt", "_builder/no_fit.txt", "_builder/index.json"]
texts = [t for t in texts if os.path.exists(os.path.join(LIB, t))]
if not DRY:
    for t in texts:
        d = os.path.join(BK, t); os.makedirs(os.path.dirname(d), exist_ok=True)
        if not os.path.exists(d): shutil.copyfile(os.path.join(LIB, t), d)


def write_in_place(path, data):
    with open(path, "r+b") as f:
        f.write(data); f.truncate()


# 2. the index (compact, ASCII-escaped or UTF-8 as found)
ip = os.path.join(LIB, "_builder", "index.json"); raw = open(ip, "rb").read(); idx = json.loads(raw)
ASCII = next(x for x in (True, False) if json.dumps(idx, separators=(",", ":"), ensure_ascii=x).encode("utf-8") == raw)
ren_prev = []
n_idx = 0
for e in idx["parts"]:
    nb = old2new.get(e["path"])
    if not nb: continue
    nid = pid(nb); assert e["id"] == pid(e["path"]), e["path"]
    newprev = "previews/%s.bin" % nid
    ren_prev.append((e["prev"], newprev))
    e["path"], e["id"], e["prev"] = nb, nid, newprev; n_idx += 1

# 3. text files: whole-line path swaps
def swap_lines(name, key_of):
    p = os.path.join(LIB, name)
    if not os.path.exists(p): return 0
    b = open(p, "rb").read(); bom = b.startswith(b"\xef\xbb\xbf"); s = b.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in s else "\n"; lines = s.split(nl); n = 0
    for i, l in enumerate(lines):
        r = key_of(l)
        if r: lines[i] = r; n += 1
    out = nl.join(lines).encode("utf-8")
    if bom: out = b"\xef\xbb\xbf" + out
    if not DRY and n: write_in_place(p, out)
    return n

def src_row(l):
    for q in ('"',):
        if l.startswith(q):
            end = l.find('",', 1); key = l[1:end]
            return ('"' + old2new[key] + l[end:]) if key in old2new else None
    key = l.split(",", 1)[0]
    return (old2new[key] + l[len(key):]) if key in old2new else None

def whole_line(l):
    k = l.strip()
    return l.replace(k, old2new[k]) if k in old2new else None

def any_path(l):
    for a, b in moves:
        if a in l: return l.replace(a, b)
    return None

counts = {"index": n_idx}
counts["_sources.csv"] = swap_lines("_sources.csv", src_row)
counts["_hidden.txt"] = swap_lines("_hidden.txt", whole_line)
counts["anchors_done"] = swap_lines(os.path.join("_builder", "anchors_done.txt"), whole_line)
counts["no_fit"] = swap_lines(os.path.join("_builder", "no_fit.txt"), any_path)

# 4. the files themselves, then the previews and the index, then the log
if not DRY:
    for a, b in moves:
        os.makedirs(os.path.dirname(fs(b)), exist_ok=True)
        os.rename(fs(a), fs(b))
        sa, sb = fs(a)[:-4] + ".sockets.json", fs(b)[:-4] + ".sockets.json"
        if os.path.exists(sa): os.rename(sa, sb)
    for a, b in ren_prev:
        pa, pb = os.path.join(LIB, "_builder", a), os.path.join(LIB, "_builder", b)
        if os.path.exists(pa) and not os.path.exists(pb): os.rename(pa, pb)
    write_in_place(ip, json.dumps(idx, separators=(",", ":"), ensure_ascii=ASCII).encode("utf-8"))
    lp = os.path.join(LIB, "_renamed.csv"); s = open(lp, "rb").read()
    nl = b"\r\n" if b"\r\n" in s else b"\n"
    add = b"".join(('"%s","%s",moved (armour mark)' % (a, b)).encode("utf-8") + nl for a, b in moves)
    with open(lp, "ab") as f:
        if s and not s.endswith(nl): f.write(nl)
        f.write(add)
counts["files"] = len(moves); counts["previews"] = len(ren_prev)
print(("DRY " if DRY else "") + json.dumps(counts))
