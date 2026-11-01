"""Blade wings on the TN Mk6 Universal jump pack (Josh, Oct 31, from Desktop\\Operation Marine\\base_jumpack.blend).

The pack carries Wing Mount L/R (Josh's BackPack_fin_l/r on the marine's pack). A wing (Malal3D Bladecrow, type Wings)
brings the Techmarine kit's 'Backpack Connector - Arm 2 Joint' (type Wing Mounts) onto that side's Wing Mount, and
hangs from the connector's own Wing L/R socket: Josh's wing_l / wing_r, set separately per side.
Josh: the connector comes with the wing; the TN Mk6 Universal only; library at scale 1.0 (his marine's pack is
enlarged). His wings are the unsupported OBJs enlarged x1.3 (registered exactly), so the wings carry scale 1.3.
Left wings: mirrors of the right files (Malal's own lefts are presupported only), as Josh's are.
Also copied onto the pack: Mechadendrite L/R and the topper spots (Back Top, Back Top L).

python3 build_wings.py EXTRACT_JSON SRC_DIR LIB_IN OUT_DIR   (LIB_IN: the library or the repo mirror, for the pack's
current sidecar; OUT_DIR gets the new STLs and sidecars at their library paths, plus sources.csv rows)"""
import json, os, struct, sys
import numpy as np
EX, SRC, LIB, OUT = sys.argv[1:5]
ex = json.load(open(EX))
MX = np.diag([-1.0, 1, 1, 1])
R6 = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
M4 = lambda a: np.array(a, float).reshape(4, 4)
WINGDIR = "Bits\\Bladecrow Jump Packs\\Wings\\"
MOUNT = "Bits\\Techmarine Conversion\\Wing Mounts\\Bits Techmarine - Wing Mount Arm 2 Joint.stl"
PACK = "Turtle Ninja - Heresy\\Mk6 Assault Addon 1\\Powerpacks\\Jump Packs\\TN Mk6 Assault - Jump Pack Universal.stl"
OBJDIR = "new cults\\_Iron Hands (3)\\Iron bits\\bladecrow-jump-packs-pre-supported-malal3d-320250324-1-xvwr09\\Malal3D\\bladecrow-jump-packs-pre-supported-malal3d-3\\Malal3D_BladecrowJumpPacks\\Malal3D_BladecrowJumpPacks\\UnsupportedOBJs\\"
CONN_SRC = "new cults\\Warhammer Techmarine Conversion Kit\\Warhammer Techmarine Conversion Kit @STL_Printer\\Backpack\\Backpacks and Side Connectors\\Backpack Connector - Arm 2 Joint.stl"
WINGS = [("Wing01_OpenR", "Wing 01 Open"), ("Wing02_ClosedR", "Wing 02 Closed"), ("Wing03_UpwardsR", "Wing 03 Upwards"),
         ("Wing04_WrappedR", "Wing 04 Wrapped"), ("Wing05_DownwardsR", "Wing 05 Downwards"), ("Wing06_ExtendedR", "Wing 06 Extended")]
SCALE = 1.3


def native(rel):
    return os.path.join(OUT, rel.replace("\\", os.sep))


def write(rel, d):
    p = os.path.splitext(native(rel))[0] + ".sockets.json"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1)


def obj_to_stl(src, dst):
    V, tris = [], []
    for l in open(src):
        if l.startswith("v "):
            V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith("f "):
            ix = [int(t.split("/")[0]) for t in l.split()[1:]]
            ix = [i - 1 if i > 0 else len(V) + i for i in ix]
            tris += [(ix[0], ix[k], ix[k + 1]) for k in range(1, len(ix) - 1)]
    V = np.array(V); T = np.array(tris)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(T), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = n; rec["v"] = np.hstack([a, b, c])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(b"Bladecrow wing (Malal3D), from the unsupported OBJ".ljust(80, b" ") + struct.pack("<I", len(T)) + rec.tobytes())
    return len(T)


def sock(t, name, m, how):
    return {"type": t, "name": name, "matrix": R6(m), "display_type": "ARROWS", "display_size": 3.0, "props": {"tiow_from": how}}


rows, report = [], []
# --- wings: Wing R fit from Josh's right wings, Wing L from his left ones (mirrored mesh: fit @ MX on the variant)
fits = {}
for w in ex["wing_fits"]:
    base = w["wing"].split(".")[0].replace("_AppliedMods", "")
    fits.setdefault((base, w["socket"]), M4(w["fit"]))
for src, title in WINGS:
    FR = fits[(src, "wing_r")]; FL = fits[(src, "wing_l")]
    fl = FL @ MX
    name = "Bits Bladecrow - " + title + " R"
    rel = WINGDIR + name + ".stl"
    nt = obj_to_stl(os.path.join(SRC, src + ".obj"), native(rel))
    d = {"schemaVersion": 1, "part": src, "category": "Wings", "scale": SCALE, "sockets": [],
         "fits": {"Wing R": R6(FR)},
         "notes": {"Wing R": "Josh's placement on the connector's wing socket (base_jumpack.blend, Oct 31)",
                   "scale": "Josh's wings are Malal3D's OBJs enlarged x1.3 (registered exactly)",
                   "adaptor": "comes with its connector: the Techmarine Arm 2 Joint goes on the pack's Wing Mount, the wing on the connector"},
         "adaptor": MOUNT,
         "variants": [{"side": "L", "mirror": True, "align": R6(MX), "name": name[:-2] + " L", "title": name[:-2] + " L",
                       "folder": "Wings", "from": "mirror of the right wing, as Josh's left wings are",
                       "sidecar": {"category": "Wings", "scale": SCALE, "sockets": [], "fits": {"Wing L": R6(fl)}}}],
         "original": {"name": src, "folder": "UnsupportedOBJs", "path": OBJDIR + src + ".obj"}}
    write(rel, d)
    rows.append((rel, OBJDIR + src + ".obj", "Wings"))
    # is Josh's left wing the mirror image of his right one, in their sockets' frames?
    report.append("%-38s %6d tris" % (name, nt))

# --- the connector: as the file on the left, mirrored on the right (as Josh has them)
cL, cR = ex["connector"]["L"], ex["connector"]["R"]
assert cL["det"] > 0 and cR["det"] < 0
d = {"schemaVersion": 1, "part": "Backpack Connector - Arm 2 Joint", "category": "Wing Mounts",
     "sockets": [sock("Wing L", "Wing Mount_socket_Wing L", M4(cL["wing_socket"]), "Josh's wing_l on the connector (base_jumpack.blend)")],
     "fits": {"Wing Mount L": R6(M4(cL["fit"]))},
     "notes": {"Wing Mount L": "Josh's placement on the pack's left fin socket (base_jumpack.blend, Oct 31)",
               "type": "brought by a wing (TIOW Inbox 1.17.5), not picked on its own"},
     "variants": [{"side": "R", "mirror": True, "align": R6(MX), "name": "Bits Techmarine - Wing Mount Arm 2 Joint R",
                   "title": "Bits Techmarine - Wing Mount Arm 2 Joint R", "folder": "Wing Mounts", "from": "mirror, as Josh's right connector",
                   "sidecar": {"category": "Wing Mounts", "fits": {"Wing Mount R": R6(M4(cR["fit"]) @ MX)},
                               "sockets": [sock("Wing R", "Wing Mount R_socket_Wing R", MX @ M4(cR["wing_socket"]), "Josh's wing_r on the connector")]}}],
     "original": {"name": "Backpack Connector - Arm 2 Joint", "folder": "Backpacks and Side Connectors", "path": CONN_SRC}}
for v in (d["sockets"][0]["matrix"], d["variants"][0]["sidecar"]["sockets"][0]["matrix"], d["fits"]["Wing Mount L"], d["variants"][0]["sidecar"]["fits"]["Wing Mount R"]):
    assert np.linalg.det(M4(v)[:3, :3]) > 0.999
write(MOUNT, d)
src_stl = os.path.join(SRC, "connector.stl")
os.makedirs(os.path.dirname(native(MOUNT)), exist_ok=True)
open(native(MOUNT), "wb").write(open(src_stl, "rb").read())
rows.append((MOUNT, CONN_SRC, "Wing Mounts"))

# --- the pack: Josh's sockets merged into its sidecar (fits, exact and the rest kept)
pp = os.path.join(LIB, os.path.splitext(PACK)[0].replace("\\", os.sep) + ".sockets.json")
pk = json.load(open(pp, encoding="utf-8"))
NAMES = {"Pack Fin L": "Wing Mount L", "Pack Fin R": "Wing Mount R"}
have = {s["type"] for s in pk.get("sockets") or []}
for t, v in ex["pack_sockets"].items():
    t2 = NAMES.get(t, t)
    if t2 in have:
        continue
    pk.setdefault("sockets", []).append(sock(t2, "Mk6_Jumppack_Universal_socket_" + t2, M4(v["matrix"]),
                                             "Josh's %s (base_jumpack.blend, the marine's pack, scale taken out)" % v["from"].split("_socket_")[-1]))
pk.setdefault("notes", {})["Wing Mount L"] = "where a wing's connector goes (Josh's fin sockets on this pack; only this pack has them)"
write(PACK, pk)
with open(os.path.join(OUT, "sources_rows.csv"), "w", encoding="utf-8", newline="") as f:
    for rel, src, typ in rows:
        f.write("%s,%s,%s,\r\n" % (rel, src.replace("new cults\\", "", 1), typ))
print("\n".join(report))
print("pack sockets:", [s["type"] for s in pk["sockets"]])
