"""The online demo of the Squad Builder: a sample of the demo library (lighter
previews packed into a few files) and the page set to read them."""
import base64, json, os, re, struct, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index as B

H = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(H, "demolib", "_builder")
OUT = os.path.join(H, "demo")
KITS = {("MarFil", "Assault"), ("MarFil", "Veteran"), ("MarFil", "Jump Chaplain"), ("MarFil", "Helmets"),
        ("TN", "Mk10 Assault"), ("TN", "Mk6 Assault")}
PACK = 9_000_000

idx = json.load(open(os.path.join(SRC, "index.json")))
keep = [p for p in idx["parts"] if (p["maker"], p["kit"]) in KITS or p["maker"] == "Marta"
        or p["type"] in ("Bases", "Adapters")]
os.makedirs(os.path.join(OUT, "builder"), exist_ok=True)
packs, cur, n = [], bytearray(), 0


def flush():
    global cur
    if cur:
        name = f"pack{len(packs)}.txt"
        open(os.path.join(OUT, "builder", name), "wb").write(base64.b64encode(bytes(cur)))
        packs.append(name)
        cur = bytearray()


for p in keep:
    if not p.get("prev"):
        continue
    b = open(os.path.join(SRC, p["prev"]), "rb").read()
    nv, nt = struct.unpack("<II", b[4:12])
    V = np.frombuffer(b, "<f4", nv * 3, 12).reshape(-1, 3).astype(np.float64)
    T = np.frombuffer(b, "<u4", nt * 3, 12 + nv * 12).reshape(-1, 3).astype(np.int64)
    V2, T2 = B.simplify(V, T, 3000)
    blob = b"KBP1" + struct.pack("<II", len(V2), len(T2)) + np.asarray(V2, "<f4").tobytes() + np.asarray(T2, "<u4").tobytes()
    if len(cur) + len(blob) > PACK:
        flush()
    p["prev"] = f"pack{len(packs)}.txt#{len(cur)}:{len(blob)}"
    cur += blob
    n += 1
flush()
demo = dict(idx, parts=keep)
json.dump(demo, open(os.path.join(OUT, "builder", "index.json"), "w"), separators=(",", ":"))
src = lambda f: open(os.path.join(H, f), encoding="utf-8").read()
page = src("src/shell.html")
page = page[page.index("<title>"):page.index("</head>")] + page[page.index("<body>") + 6:page.index("</body>")]
page = page.replace('<script>/*APP*/</script>', '<script>window.SB_DEMO = true;</script>\n<script>/*APP*/</script>')
for mark, body in (("/*CSS*/", src("src/app.css")), ("/*THREE*/", src("vendor/package/build/three.min.js")),
                   ("/*ORBIT*/", src("vendor/package/examples/js/controls/OrbitControls.js")), ("/*APP*/", src("src/app.js"))):
    page = page.replace(mark, body.replace("</script", "<\\/script"), 1)
page = page.replace("<title>Squad Builder</title>", "<title>Squad Builder</title>\n<meta name=\"claude:viewport-fit-sides\" content=\"cover\">", 1)
open(os.path.join(OUT, "squad_builder.html"), "w", encoding="utf-8").write(page)
print(len(keep), "parts,", n, "previews in", len(packs), "packs:",
      [os.path.getsize(os.path.join(OUT, "builder", x)) // 1000000 for x in packs], "MB;",
      os.path.getsize(os.path.join(OUT, "builder", "index.json")) // 1000, "KB index")
