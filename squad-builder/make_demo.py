"""The online demo of the Squad Builder: a sample of Josh's library index (lighter previews packed into a few
base64 text files, as artifacts serve no binary files or "_" folders) and the page set to read them (Send only reports)."""
import base64, json, os, re, struct, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index as B

H = os.path.dirname(os.path.abspath(__file__))
# python make_demo.py INDEX_JSON PREVIEWS_DIR HIDDEN_TXT OUT [--list FILE]   (Nov 3: from the PC's index; the sample
# below; parts hidden by Josh's _hidden.txt left out; --list writes the preview files needed and stops)
IDX, SRC, HID, OUT = sys.argv[1:5]
KITS = {("MarFil", "Assault"), ("MarFil", "Jump Chaplain"), ("MarFil", "Helmets"), ("TN", "Mk6 Assault"), ("Marta", "Gurls"), ("OldStyle", "MK8")}
TYPES = {"Bases", "Adapters", "Hip Plates", "Plate Accessories", "Buckles", "Tabards", "Trophies", "Chest Equipment", "Neck Guards"}
PACK = 9_000_000
TRIS = 3000

def hidden_rules(txt):
    paths, words, types = set(), [], []
    for l in txt.replace("\ufeff", "").splitlines():
        t = l.strip()
        if not t or t[0] == "#": continue
        m = re.match(r"^word:\s*(.+)$", t, re.I) or None
        if m: words.append(m.group(1).lower()); continue
        m = re.match(r"^type:\s*(.+)$", t, re.I)
        if m: types.append(m.group(1).lower()); continue
        paths.add(t.lower())
    return lambda p: p["path"].lower() in paths or any(w in (p["name"] + " " + (p.get("orig") or "")).lower() for w in words) or str(p["type"]).lower() in types

idx = json.load(open(IDX))
hid = hidden_rules(open(HID, encoding="utf-8-sig").read())
keep = [p for p in idx["parts"] if ((p["maker"], p["kit"]) in KITS or p["type"] in TYPES) and not hid(p)]
if "--list" in sys.argv:
    open(sys.argv[sys.argv.index("--list") + 1], "w").write("\n".join(p["prev"] for p in keep if p.get("prev")) + "\n")
    print(len(keep), "parts"); sys.exit()
def decimate(V, T, target):
    """Blender's collapse decimate (keeps the faces' facing; the numpy simplify left flipped triangles at 3,000)."""
    import bpy
    if len(T) <= target: return V, T
    me = bpy.data.meshes.new("p"); me.from_pydata(V.tolist(), [], T.tolist()); me.update()
    ob = bpy.data.objects.new("p", me); bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("d", "DECIMATE"); m.ratio = target / len(T); m.use_collapse_triangulate = True
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); em = ev.to_mesh(); em.calc_loop_triangles()
    V2 = np.empty(len(em.vertices) * 3); em.vertices.foreach_get("co", V2)
    T2 = np.empty(len(em.loop_triangles) * 3, np.int64); em.loop_triangles.foreach_get("vertices", T2)
    ev.to_mesh_clear(); bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)
    return V2.reshape(-1, 3), T2.reshape(-1, 3)


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
    V2, T2 = decimate(V, T, TRIS)
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
page = src("src/shell.html")          # the whole document (an artifact page must start with <!DOCTYPE html>)
page = page.replace('<script>/*APP*/</script>', '<script>window.SB_DEMO = true;</script>\n<script>/*APP*/</script>')
for mark, body in (("/*CSS*/", src("src/app.css")), ("/*THREE*/", src("vendor/three/build/three.min.js")),
                   ("/*ORBIT*/", src("vendor/three/examples/js/controls/OrbitControls.js")), ("/*APP*/", src("src/app.js"))):
    page = page.replace(mark, body.replace("</script", "<\\/script"), 1)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
print(len(keep), "parts,", n, "previews in", len(packs), "packs:",
      [os.path.getsize(os.path.join(OUT, "builder", x)) // 1000000 for x in packs], "MB;",
      os.path.getsize(os.path.join(OUT, "builder", "index.json")) // 1000, "KB index")
