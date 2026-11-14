"""Shells (Josh, Nov 14, notes 094 / 095): the mating surface of a maker folder's parts of one type (maker + armour
type), lying where those parts sit on their joint, so a scene's centre is the socket and every maker's shell of a
type is in the same place. A part is then brought to the shell and mated there; the only fit set by hand is the
shell's own.

    PY  shells.py make  LIBRARY OUT [--types "Shoulder Pads,Heads,Backpacks,Arms,Hands"] [--pads WORK] [--k 15]
                        OUT/<maker folder> - <type> shell.stl and OUT/shells.json (what each was made from)
    BL  shells.py blend OUT FILE.blend LIBRARY [CHECKDIR]
                        one scene a part type: a collection a maker (one switched on), Mar Fil's body round the joint as
                        a wire guide. CHECKDIR: every shell alone, two views, on one numbered sheet (check.jpg)
  PY = a Python with numpy (Blender's own); BL = blender --background --factory-startup --python shells.py --

A shell is NOT faces cut out of a sculpt (tried first: rims, studs and fingers come along). It is what the joint sees
of the part, rebuilt as one clean surface:
  * every fitted part is moved into its socket's space by its own fit (a left part mirrored first);
  * heads, backpacks, arms, hands: looking out of the joint along the socket's Z, the nearest surface of the part in
    each 0.2 mm cell (a height map), within R of the joint;
    pads: from the middle of the dome, the nearest surface in each direction (the inside), over the dome's cap;
  * up to --k parts of the folder are laid over each other and the MIDDLE value of each cell kept, where most of
    them have a surface and agree to 0.35 mm: badges, one-off shapes and the odd wrong fit drop out, what the folder's
    parts share at the joint stays (only the biggest group of parts that lie alike is used: some makers' parts sit
    two ways);
  * the cells no deeper than DEPTH behind the nearest are kept, cliffs split the map, and the biggest piece is the
    shell.
1 unit = 1 mm, as the library's files are.
"""
import sys, os, json, glob, collections, random, warnings
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
TYPES = ["Shoulder Pads", "Knee Pads", "Heads", "Backpacks", "Arms", "Hands"]
SHELL = ("Shoulder Pads", "Knee Pads")      # these mate by their inside (a shell); the rest by their connector
CONN = {"Heads": (3.5, 2.5), "Backpacks": (3.0, 3.0), "Arms": (3.2, 1.5), "Hands": (2.0, 1.5)}       # R, D (mm): the connector
                                   # is the part within R of the joint and no more than D out of it (towards the part)
OWN = {("Mar Fil - Tacticus", "Heads"): "Mar Fil - Tacticus/AssaultMarines-V2/Helmet-Heads/Heads/MarFil Assault - Helmet 1",
       ("Mar Fil - Tacticus", "Arms"): "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R"}
ORTHO = {"Heads": (5.0, 2.5), "Backpacks": (9.0, 6.0), "Arms": (6.5, 3.0), "Hands": (3.5, 3.0)}       # R, DEPTH (mm): a shoulder is a cap
                                   # 2.5 mm deep, a pack's mount a plate with a boss 3 mm into the back; what parts do not share is already out
H, AGREE, JUMP = 0.2, 0.35, 0.6
U, DU = 1.3, 0.03                  # pads: the cap out to 105 deg from the dome's top, cells of about 3.4 deg there
SOCK = {"Shoulder Pads": "Pad R", "Knee Pads": "Shin R", "Heads": "Neck", "Backpacks": "Back", "Arms": "Shoulder R", "Hands": "Hand R"}
TORSO = "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1"
ARM = "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R"
LEGS = "Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A"


def write_stl(path, T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]); rec["n"], rec["v"] = n, T
    with open(path, "wb") as fo: fo.write(b"shell".ljust(80, b" ")); fo.write(np.uint32(len(T)).tobytes()); fo.write(rec.tobytes())
def move(T, M): return (np.c_[T.reshape(-1, 3), np.ones(len(T) * 3)] @ M.T)[:, :3].reshape(-1, 3, 3)
def unit(v): return v / np.linalg.norm(v)


def guides(lib):
    """{type: [(library part, its move into that type's socket space)]}: Mar Fil's body round each joint"""
    def sidecar(rel): return json.load(open(lib + "/" + rel + ".sockets.json", encoding="utf-8-sig"))
    def sock(sc, t): return np.array(next(s["matrix"] for s in sc["sockets"] if s["type"] == t)).reshape(4, 4)
    tor, arm, legs = sidecar(TORSO), sidecar(ARM), sidecar(LEGS); inv = np.linalg.inv
    Warm = sock(tor, "Shoulder R") @ np.array(arm["fits"]["Shoulder R"]).reshape(4, 4)            # the arm in the torso's space
    return {"Heads": [(TORSO, inv(sock(tor, "Neck")))], "Backpacks": [(TORSO, inv(sock(tor, "Back")))], "Arms": [(TORSO, inv(sock(tor, "Shoulder R")))],
            "Shoulder Pads": [(ARM, inv(sock(arm, "Pad R"))), (TORSO, inv(Warm @ sock(arm, "Pad R")))],
            "Hands": [(ARM, inv(sock(arm, "Hand R")))] if any(s["type"] == "Hand R" for s in arm["sockets"]) else [],
            "Knee Pads": [(LEGS, inv(sock(legs, "Shin R")))] if any(s["type"] == "Shin R" for s in legs.get("sockets") or []) else []}
def view_frame(lib, typ, G):
    """rows e1, e2, n: n looks from what the part hangs from to the part, in the socket's space. A socket's Z is not
    always that way (a neck's is; an arm hangs off the side of the shoulder's, a pack off the back's), so it is taken
    from where Mar Fil's body is: away from the middle of its surface within 10 mm of the joint."""
    from kb import carry
    rel, M = G[typ][0]; V = move(carry.soup(lib + "/" + rel + ".stl"), M).reshape(-1, 3); near = V[np.linalg.norm(V, axis=1) < 10]
    n = -unit(near.mean(0)); e1 = unit(np.cross(n, [0.0, 0, 1] if abs(n[2]) < 0.9 else [1.0, 0, 0])); return np.array([e1, np.cross(n, e1), n])


def height_map(T, R):
    """the part (triangles in the joint's view frame: z from the host to the part) seen from the joint: the nearest
    surface in each cell, nan where none"""
    from kb import carry
    c = T.mean(1); near = (np.hypot(c[:, 0], c[:, 1]) < R + 2) & (c[:, 2] > -4) & (c[:, 2] < 12)
    n = int(np.ceil(2 * R / H)); Z = np.full((n, n), np.inf)
    if near.sum() < 4: return Z * np.nan
    P = carry.sample(T[near], 250000, 0); i = np.floor((P[:, 0] + R) / H).astype(int); j = np.floor((P[:, 1] + R) / H).astype(int)
    ok = (i >= 0) & (i < n) & (j >= 0) & (j < n); np.minimum.at(Z, (i[ok], j[ok]), P[ok, 2]); Z[np.isinf(Z)] = np.nan
    return Z
def cap_map(T, C, B):
    """a pad (triangles in its socket's space) seen from the middle C of its dome: the nearest surface in each
    direction of the cap round the dome's top B[2] (the directions laid flat from the opening's side), nan where none"""
    from kb import carry
    n = int(np.ceil(2 * U / DU)); Rm = np.full((n, n), np.inf); c = T.mean(1); near = np.linalg.norm(c - C, axis=1) < 14
    if near.sum() < 4: return Rm * np.nan
    P = carry.sample(T[near], 600000, 0) - C; r = np.linalg.norm(P, axis=1); d = P / np.maximum(r, 1e-9)[:, None]
    x, y, w = d @ B[0], d @ B[1], d @ B[2]; ok = w > -0.3
    i = np.floor((x[ok] / (1 + w[ok]) + U) / DU).astype(int); j = np.floor((y[ok] / (1 + w[ok]) + U) / DU).astype(int); r = r[ok]
    ok = (i >= 0) & (i < n) & (j >= 0) & (j < n); np.minimum.at(Rm, (i[ok], j[ok]), r[ok]); Rm[np.isinf(Rm)] = np.nan
    return Rm


def pieces(T):
    """the triangles' joined pieces (sharing a corner), as lists of indices"""
    _, ix = np.unique(np.round(T.reshape(-1, 3), 4), axis=0, return_inverse=True); ix = ix.reshape(-1, 3); up = list(range(len(T)))
    def root(a):
        while up[a] != a: up[a] = up[up[a]]; a = up[a]
        return a
    first = {}
    for t, row in enumerate(ix.tolist()):
        for v in row:
            if v in first: up[root(t)] = root(first[v])
            else: first[v] = t
    out = collections.defaultdict(list)
    for t in range(len(T)): out[root(t)].append(t)
    return list(out.values())
def connector(T, B, R, D):
    """the connector of a part (triangles in its socket's space): within R of the joint and at most D out of it towards
    the part, the joined piece nearest the joint (and any other piece as near)"""
    c = T.mean(1); keep = np.nonzero((np.linalg.norm(c, axis=1) < R) & (c @ B[2] < D))[0]
    if len(keep) < 12: return np.zeros((0, 3, 3))
    P = pieces(T[keep]); d = [float(np.linalg.norm(c[keep[p]], axis=1).min()) for p in P]; best = min(d)
    return T[keep[[i for p, dd in zip(P, d) if dd <= best + 0.3 and len(p) >= 8 for i in p]]]


def agree(maps):
    """the middle of the maps, where most have a surface and they agree; how well (the median spread); which maps.
    Only the biggest group of maps that lie alike is used (each within 0.35 mm of the one most of the others match
    over the cells they share): a maker whose parts sit two ways, or a wrong fit, would tear the surface."""
    A = np.stack(maps); k = len(maps); pick = list(range(k))
    if k > 2:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            D = np.array([[np.nanmedian(np.abs(A[i] - A[j])) if (~np.isnan(A[i]) & ~np.isnan(A[j])).sum() >= 0.3 * max(1, (~np.isnan(A[i])).sum()) else 9.0 for j in range(k)] for i in range(k)])
        D = np.where(np.isnan(D), 9.0, D); c = int((D <= AGREE).sum(1).argmax()); pick = [j for j in range(k) if D[c, j] <= AGREE]
        if len(pick) < 2: pick = [c]
    A = A[pick]; k = len(pick)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore"); med = np.nanmedian(A, 0); mad = np.nanmedian(np.abs(A - med), 0)
    cnt = (~np.isnan(A)).sum(0); keep = (cnt >= max(1, int(np.ceil(0.6 * k)))) & (mad <= AGREE)
    med[~keep] = np.nan
    return med, (float(np.nanmedian(mad[keep])) if keep.any() else 9.0), pick
def trim(mask, n=2):
    """thin tails and frills off: what is left after shrinking the mask n cells and growing it back"""
    def nb(m, f):
        P = np.zeros((m.shape[0] + 2, m.shape[1] + 2), bool); P[1:-1, 1:-1] = m
        return f(np.stack([P[a:a + m.shape[0], b:b + m.shape[1]] for a in range(3) for b in range(3)]), 0)
    m = mask
    for _ in range(n): m = nb(m, np.all)
    for _ in range(n): m = nb(m, np.any)
    return m & mask
def smooth(Z):
    n, m = Z.shape; P = np.full((n + 2, m + 2), np.nan); P[1:-1, 1:-1] = Z
    with warnings.catch_warnings():
        warnings.simplefilter("ignore"); S = np.nanmedian(np.stack([P[a:a + n, b:b + m] for a in range(3) for b in range(3)]), 0)
    S[np.isnan(Z)] = np.nan; return S
def surface(V, val, mask, facing, seed=None):
    """the grid's cells as one mesh: quads whose four corners are in and no cliff between them, the biggest joined
    piece (or the one at `seed`), faces looking along `facing`(point) -> triangles (n, 3, 3)"""
    q = mask[:-1, :-1] & mask[1:, :-1] & mask[:-1, 1:] & mask[1:, 1:]
    c = np.stack([val[:-1, :-1], val[1:, :-1], val[:-1, 1:], val[1:, 1:]]); c = np.where(np.isnan(c), 0, c); q &= (c.max(0) - c.min(0)) < JUMP
    lab = np.zeros(q.shape, int); k = 0; sizes = {}
    for s in zip(*np.nonzero(q)):
        if lab[s]: continue
        k += 1; lab[s] = k; todo = [s]; cnt = 0
        while todo:
            a, b = todo.pop(); cnt += 1
            for a2, b2 in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= a2 < q.shape[0] and 0 <= b2 < q.shape[1] and q[a2, b2] and not lab[a2, b2]: lab[a2, b2] = k; todo.append((a2, b2))
        sizes[k] = cnt
    if not sizes: return np.zeros((0, 3, 3))
    best = lab[seed] if seed is not None and lab[seed] and sizes[lab[seed]] >= 0.3 * max(sizes.values()) else max(sizes, key=sizes.get)
    a, b = np.nonzero(lab == best); v00, v10, v01, v11 = V[a, b], V[a + 1, b], V[a, b + 1], V[a + 1, b + 1]
    T = np.concatenate([np.stack([v00, v10, v11], 1), np.stack([v00, v11, v01], 1)])
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); want = facing(T.mean(1))
    if float((n * want).sum()) < 0: T = T[:, ::-1]
    return T


def make(lib, out, A):
    from kb import carry
    import carry_library as CL, masters as MS
    types = CL.opt(A, "--types", ",".join(TYPES)).split(","); pads = CL.opt(A, "--pads"); K = int(CL.opt(A, "--k", "15")); os.makedirs(out, exist_ok=True)
    old = {s["shell"]: s for s in (json.load(open(out + "/shells.json", encoding="utf-8")) if os.path.exists(out + "/shells.json") else [])}
    P = CL.scan(lib, types); G = guides(lib); frames = {t: view_frame(lib, t, G) for t in types if t in CONN}
    for t, B in frames.items(): print("%-10s seen along %s of its socket" % (t, B[2].round(2)))
    def in_socket(rel, sc):
        F, left = MS.right_fit(sc); return move(carry.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)) * (np.array([-1.0, 1, 1]) if left else 1.0), F)
    for typ in types:
        by = collections.defaultdict(list)
        for rel, sc in P[typ]:
            if MS.right_fit(sc)[0] is not None: by[CL.maker(rel)].append((rel, sc))
        for mk in sorted(by):
            name = "%s - %s shell" % (mk, typ); D = dict(by[mk]); use = random.Random(7).sample(sorted(D), min(K, len(D))); maps, used = [], []
            if typ not in SHELL or (mk, typ) in OWN:                # ONE reference part: Josh's, or the folder's most ordinary
                ref = OWN.get((mk, typ))
                if ref not in D:
                    right = [r for r in D if not MS.right_fit(D[r])[1]] or list(D); E = {}
                    for r in right:
                        try: E[r] = np.sort(np.ptp(carry.soup(lib + "/" + r + ".stl", D[r].get("scale", 1.0)).reshape(-1, 3), 0))
                        except (OSError, ValueError): pass
                    if not E: continue
                    med = np.median(np.array(list(E.values())), 0); ref = min(E, key=lambda r: float(np.abs(E[r] - med).sum()))
                Tr = in_socket(ref, D[ref])
                if typ in CONN:
                    T = connector(Tr, frames[typ], *CONN[typ]); view = (-frames[typ][2]).tolist(); how = "connector"
                else:                                               # Mar Fil's pads: the inside of Josh's pad 62
                    I = carry.inner(carry.sample(Tr, 60000, 0)); C = carry._centre(I); c = Tr.mean(1); far = np.linalg.norm(I - C, axis=1).max() + 0.15
                    a = unit(((I - C) / np.linalg.norm(I - C, axis=1)[:, None]).mean(0)); T = Tr[(np.linalg.norm(c - C, axis=1) <= far) & ((c - C) @ a > -0.3 * far)]
                    T = T[[i for p in pieces(T) if len(p) > 0.05 * len(T) for i in p]] if len(T) else T; view = (-a).tolist(); how = "inside"
                if len(T) < 12: print("%-34s %-14s NO SHELL from %s" % (mk, typ, os.path.basename(ref))); old.pop(name, None); continue
                write_stl("%s/%s.stl" % (out, name), T); pts = T.reshape(-1, 3)
                old[name] = {"shell": name, "maker": mk, "type": typ, "socket": SOCK[typ], "from": [ref], "how": how, "tried": 1, "fitted": len(D), "spread": 0.0, "faces": int(len(T)), "view": view,
                             "box": [[round(float(x), 2) for x in pts.min(0)], [round(float(x), 2) for x in pts.max(0)]]}
                print("%-34s %-14s %5d faces, the %s of %s" % (mk, typ, len(T), how, os.path.basename(ref)), flush=True); continue
            if typ in SHELL:
                first = None
                if pads and os.path.exists("%s/one-%s.json" % (pads, mk)): first = json.load(open("%s/one-%s.json" % (pads, mk), encoding="utf-8"))["master"]
                if first not in D: first = use[0]
                I = carry.inner(carry.sample(in_socket(first, D[first]), 60000, 0)); C = carry._centre(I); a = unit(((I - C) / np.linalg.norm(I - C, axis=1)[:, None]).mean(0))
                e1 = unit(np.cross(a, [0.0, 0, 1] if abs(a[2]) < 0.9 else [1.0, 0, 0])); B = np.array([e1, np.cross(a, e1), a])
            else: B = frames[typ]
            for rel in use:
                try: T = in_socket(rel, D[rel])
                except (OSError, ValueError): continue
                maps.append(cap_map(T, C, B) if typ in SHELL else height_map(T @ B.T, ORTHO[typ][0])); used.append(rel)
            if not maps: continue
            M, spread, pick = agree(maps); M = smooth(M); n = M.shape[0]; tried = len(used); used = [used[i] for i in pick]
            if typ in SHELL:
                g = (np.arange(n) + 0.5) * DU - U; u, v = np.meshgrid(g, g, indexing="ij"); rho2 = u * u + v * v
                d = (2 * u[..., None] * B[0] + 2 * v[..., None] * B[1] + (1 - rho2)[..., None] * B[2]) / (1 + rho2)[..., None]
                mask = ~np.isnan(M) & (rho2 <= U * U)
                if mask.any(): mask &= np.where(mask, M, 0) <= 1.6 * np.nanmedian(M[mask])
                mask = trim(mask)
                V = C + np.where(mask, M, 0)[..., None] * d; T = surface(V, M, mask, lambda c: C - c, seed=(n // 2, n // 2)); view = (-B[2]).tolist()
            else:
                R, depth = ORTHO[typ]; g = (np.arange(n) + 0.5) * H - R; x, y = np.meshgrid(g, g, indexing="ij"); mask = ~np.isnan(M) & (x * x + y * y <= R * R)
                if mask.any(): mask &= np.where(mask, M, 9e9) <= np.percentile(M[mask], 5) + depth
                mask = trim(mask)
                V = np.dstack([x, y, np.where(mask, M, 0)]) @ B; T = surface(V, M, mask, lambda c: -B[2]); view = (-B[2]).tolist()
            if len(T) < 40: print("%-34s %-14s NO SHELL: its %d parts share no surface at the joint" % (mk, typ, len(used))); old.pop(name, None); continue
            write_stl("%s/%s.stl" % (out, name), T); pts = T.reshape(-1, 3)
            old[name] = {"shell": name, "maker": mk, "type": typ, "socket": SOCK[typ], "from": used, "tried": tried, "fitted": len(D), "spread": round(spread, 3), "faces": int(len(T)), "view": view,
                         "box": [[round(float(x), 2) for x in pts.min(0)], [round(float(x), 2) for x in pts.max(0)]]}
            print("%-34s %-14s %5d faces from %2d parts that lie alike (of %2d tried, %3d fitted); they agree to %.2f mm" % (mk, typ, len(T), len(used), tried, len(D), spread), flush=True)
    done = sorted(old.values(), key=lambda s: (TYPES.index(s["type"]), s["maker"]))
    json.dump(done, open(out + "/shells.json", "w", encoding="utf-8"), indent=1)
    print("%d shells -> %s" % (len(done), out))


FONT = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111", "4": "101101111001001",
        "5": "111100111001111", "6": "111100111101111", "7": "111001001001001", "8": "111101111101111", "9": "111101111001111"}
def blend(out, blendfile, lib, check=None):
    import bpy
    from mathutils import Matrix, Vector
    from kb import carry
    guide = guides(lib)
    cols = [(0.45, 0.65, 0.88, 1), (0.9, 0.58, 0.35, 1), (0.55, 0.8, 0.5, 1), (0.75, 0.55, 0.85, 1), (0.9, 0.35, 0.35, 1), (0.9, 0.85, 0.3, 1), (0.4, 0.8, 0.8, 1), (0.85, 0.5, 0.7, 1)]
    def obj(coll, name, T, wire=False):
        me = bpy.data.meshes.new(name); n = len(T); me.from_pydata(T.reshape(-1, 3).tolist(), [], np.arange(n * 3).reshape(-1, 3).tolist()); me.update()
        o = bpy.data.objects.new(name, me); coll.objects.link(o)
        if wire: o.display_type = "WIRE"; o.hide_select = True
        return o
    bpy.ops.wm.read_factory_settings(use_empty=True); first = bpy.context.scene; S = json.load(open(out + "/shells.json", encoding="utf-8")); made = {}; objs = []
    for typ in dict.fromkeys(s["type"] for s in S):
        sc = bpy.data.scenes.new(typ); made[typ] = 0
        sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = "MILLIMETERS"
        mine = [s for s in S if s["type"] == typ]; on = next((s["maker"] for s in mine if s["maker"].startswith("Mar Fil")), mine[0]["maker"])
        for k, s in enumerate(mine):
            co = bpy.data.collections.new("%s (%s)" % (s["maker"], typ)); sc.collection.children.link(co)
            o = obj(co, s["shell"], carry.soup("%s/%s.stl" % (out, s["shell"]))); o["socket"] = s["socket"]; o["made from"] = "%d parts that lie alike, of %d tried (%d fitted)" % (len(s["from"]), s.get("tried", len(s["from"])), s["fitted"]); o.color = cols[k % len(cols)]
            sc.view_layers[0].layer_collection.children[co.name].exclude = s["maker"] != on; made[typ] += 1; objs.append((sc, o, s))
        gc = bpy.data.collections.new("guide: Mar Fil body (%s)" % typ); sc.collection.children.link(gc)
        for rel, M in guide.get(typ, []): obj(gc, "guide " + os.path.basename(rel), move(carry.soup(lib + "/" + rel + ".stl"), M), wire=True)
    bpy.data.scenes.remove(first)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blendfile))
    print("scenes:", ", ".join("%s (%d shells)" % kv for kv in made.items()), "->", blendfile)
    if not check: return
    sys.path.insert(0, REPO + "/tests"); import rend                     # after the save: the file keeps no camera
    os.makedirs(check, exist_ok=True); t = 220; tiles = []
    for sc in bpy.data.scenes:
        for lc in sc.view_layers[0].layer_collection.children: lc.exclude = False
        rend.setup(sc, t)
    for k, (sc, o, s) in enumerate(objs):
        cam = sc.camera
        for q in sc.objects:
            if q.type == "MESH": q.hide_render = q is not o
        pts = [Vector(c) for c in o.bound_box]; lo = Vector([min(q[i] for q in pts) for i in range(3)]); hi = Vector([max(q[i] for q in pts) for i in range(3)]); c = (lo + hi) / 2; size = (hi - lo).length
        v = Vector(s["view"]).normalized(); side = v.orthogonal().normalized(); row = []
        for vn, d in (("a", v), ("b", (v * 0.55 + side * 0.85).normalized())):
            u = Vector((0, 1, 0)) if abs(d.dot(Vector((0, 1, 0)))) < 0.95 else Vector((1, 0, 0)); y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
            cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 50), Matrix((x, y, d)).transposed().to_quaternion(), None); cam.data.ortho_scale = size * 1.15
            f = "%s/%02d_%s.png" % (check, k + 1, vn); sc.render.filepath = f; bpy.ops.render.render(write_still=True, scene=sc.name)
            im = bpy.data.images.load(f); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); row.append(a.reshape(h, w, 4)[::-1, :, :3].copy()); bpy.data.images.remove(im); os.remove(f)
        cell = np.hstack(row)
        for j, ch in enumerate(str(k + 1)):
            g = np.array([int(x) for x in FONT[ch]], bool).reshape(5, 3).repeat(5, 0).repeat(5, 1); cell[6:31, 6 + j * 20:21 + j * 20][g] = (1.0, 0.85, 0.1)
        cell[:, -1] = 0.5; cell[-1, :] = 0.5; tiles.append(cell)
    ncol = 4; rows = -(-len(tiles) // ncol); C = np.zeros((rows * t, ncol * 2 * t, 3), np.float32)
    for k, cell in enumerate(tiles): r, c = divmod(k, ncol); C[r * t:(r + 1) * t, c * 2 * t:(c + 1) * 2 * t] = cell
    Hh, Ww = C.shape[:2]; im = bpy.data.images.new("check", Ww, Hh); im.pixels.foreach_set(np.dstack([C[::-1], np.ones((Hh, Ww, 1), np.float32)]).ravel())
    im.filepath_raw = check + "/check.jpg"; im.file_format = "JPEG"; im.save()
    for k, (sc, o, s) in enumerate(objs): print(k + 1, "|", s["maker"], "|", s["type"], "|", len(s["from"]), "alike of", s.get("tried"), "tried,", s["fitted"], "fitted | agree", s["spread"])
    print("sheet ->", check + "/check.jpg")


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if not A: sys.exit(__doc__)
    if A[0] == "make": make(A[1], A[2], A)
    elif A[0] == "blend": blend(A[1], A[2], A[3], A[4] if len(A) > 4 else None)
    else: sys.exit(__doc__)
