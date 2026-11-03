"""Merge the seated plate / buckle / trophy spots (tn_seat.py results) into the legs' sidecars, like the Assault legs
(build_tiow.py): sockets Plate R, Plate L, Buckle, Trophy R, Trophy L; every other socket and key is kept; same file
style (indent, line ends). python tn_sidecars.py SEAT_JSON OUT_DIR"""
import json, os, sys
SEAT, OUT = sys.argv[1:3]
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "library")
WHY = {"Plate L": "Mar Fil hip plate seated by rule (tn_seat.py): contact points on the hip armour, top edge on the belt, 26 deg roll, top edge level",
       "Plate R": "Mar Fil hip plate (mirror variant) seated by rule, as Plate L",
       "Buckle": "Mar Fil buckle part seated over the belt front by rule (Josh: Mar Fil buckle part on Turtle Ninja legs)",
       "Trophy R": "belt rule 45 deg right of the way the buckle faces, at these legs' belt height",
       "Trophy L": "belt rule 45 deg left of the way the buckle faces, at these legs' belt height"}
SIZE = {"Plate R": 2.0, "Plate L": 2.0, "Buckle": 1.5, "Trophy R": 1.5, "Trophy L": 1.5}
res = json.load(open(SEAT)); n = 0
for rel, r in res.items():
    f = os.path.join(LIB, rel + ".sockets.json"); b = open(f, "rb").read(); bom = b.startswith(b"\xef\xbb\xbf"); raw = b.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in raw else "\n"; second = raw.split(nl)[1] if nl in raw else ""; ind = len(second) - len(second.lstrip(" ")) or None
    d = json.loads(raw)
    keep = [s for s in d.get("sockets", []) if s["type"] not in WHY]
    new = [{"type": t, "name": t, "matrix": [round(float(x), 6) for row in r["sockets"][t] for x in row], "display_type": "ARROWS",
            "display_size": SIZE[t], "props": {"tiow_from": WHY[t]}} for t in ("Plate R", "Plate L", "Buckle", "Trophy R", "Trophy L")]
    d["sockets"] = keep + new
    txt = json.dumps(d, indent=ind, ensure_ascii=False)
    if nl != "\n": txt = txt.replace("\n", nl)
    q = os.path.join(OUT, rel + ".sockets.json"); os.makedirs(os.path.dirname(q), exist_ok=True)
    open(q, "wb").write((b"\xef\xbb\xbf" if bom else b"") + txt.encode("utf-8")); n += 1
print(n, "sidecars")
