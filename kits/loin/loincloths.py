"""Loincloths as their own part type (Josh, Oct 30: "set loincloths to be their own selection rather than bundled
into accessories; the front anchor on the belt should only apply to loincloths").

Every loincloth sidecar gets category "Loincloths" (TIOW Inbox 1.17.4 puts that type on Belt Front only). Marta's 21
already have a Belt Front fit. CyberBrush's 5 get one by the same rule as Marta's: the top edge's centre, at the
back, on the anchor; face out along the anchor's Z, top up its Y; TIOW then rocks and settles it onto the belt.
CyberBrush export them standing (Z up) with the decorated face towards -Y (renders: tests/loin/cb_sheet.jpg).

python3 loincloths.py SRC_LIB OUT_LIB    (SRC_LIB: the library or the repo's library/ mirror; STLs are needed only
for the CyberBrush ones). Writes changed sidecars under OUT_LIB at the same relative paths, LF, indent 1, as found."""
import glob, json, os, struct, sys
import numpy as np
SRC, OUT = sys.argv[1], sys.argv[2]
STLS = sys.argv[3] if len(sys.argv) > 3 else SRC
NOTE = "hangs from the front of the belt: top edge on the anchor, face out; then rocks and settles onto the belt"
BAND = 2.0          # mm: the top edge is the part within this of the top


def read_stl(p):
    b = open(p, "rb").read()
    n = struct.unpack_from("<I", b, 80)[0]
    a = np.frombuffer(b, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), count=n, offset=84)
    return a["v"].reshape(-1, 3).astype(float)


def upright_fit(V):
    """Z up, face -Y: file -> anchor frame (anchor Y up, Z out), origin the top edge's centre at the back."""
    R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # x->x, y->-z (back is +Y), z->y
    top = V[V[:, 2] > V[:, 2].max() - BAND]
    o = np.array([(top[:, 0].min() + top[:, 0].max()) / 2, top[:, 1].max(), V[:, 2].max()])
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = -R @ o
    return [round(float(x), 6) for x in M.reshape(-1)]


n = 0
for f in sorted(set(glob.glob(os.path.join(SRC, "**", "*Loincloth*.sockets.json"), recursive=True))):
    rel = os.path.relpath(f, SRC)
    d = json.load(open(f, encoding="utf-8"))
    if d.get("category") == "Loincloths" and (d.get("fits") or {}).get("Belt Front"):
        continue
    d["category"] = "Loincloths"
    if not (d.get("fits") or {}).get("Belt Front"):
        stl = os.path.join(STLS, rel[:-len(".sockets.json")] + ".stl")
        d.setdefault("fits", {})["Belt Front"] = upright_fit(read_stl(stl))
        d.setdefault("notes", {})["Belt Front"] = NOTE + " (CyberBrush: standing, face -Y)"
        d["notes"].pop("type", None)
    d.setdefault("notes", {})["category"] = "Loincloths: their own type, the only one on the belt's front anchor (Josh, Oct 30)"
    o = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(o), exist_ok=True)
    with open(o, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=1)
    n += 1
    print(rel)
print(n, "sidecars written")
