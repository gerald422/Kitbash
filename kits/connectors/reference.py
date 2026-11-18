"""Read Josh's reference file (docs/PLAN.md, "The reference file"): his cuts and his placements. Needs bpy. Read only.

read(blend, lib) -> {"parts", "joints", "notes"}:
  parts   object name -> {"rel": library path, "Wm": maker coordinates -> the reference's world}
  spots   the other cuts (legs buckle, arm wrist armour, legs back plate) by fixed name: [{"cut", "part", "tri", "Wm"}]
  joints  one per joint (shoulder, neck, waist, back, wrist, pad, shin): the socket / fit names it stands for and
          "hosts" / "children": [{"cut", "part" (library path), "tri" (the cut in its part's maker coordinates),
          "J" (the joint's frame in that part's maker coordinates)}]
A part elsewhere gets:  socket = M x J (host side),  fit = inverse(M x J) (child side),  M = where the cut is found on it
(kb.connect.find, cut coordinates -> the part's maker coordinates). On the reference parts themselves M is identity, so
they sit exactly as Josh placed them: the anchor is his placement, never a library fit. The joint's frame is only a
convention (it cancels between the two sides): the reference host's own socket where it has one, so the hosts' socket
axes stay as the add-on expects them; else the host cut's middle with the world's axes.

Which library file an object is: its name (the library's, or the maker's original file name from _sources.csv). How
its mesh lies (the file as it is, the maker's export, or moved by an applied transform) is read from the file itself:
one triangle of the object found in the file by its edge lengths, checked on the object's other corners."""
import os, re, json, csv
import numpy as np
from kb import origin as OG, connect as C

FIXED = ["torso shoulder", "torso neck", "torso waist", "torso back", "arm shoulder disc", "arm pad spot", "arm wrist armour", "arm wrist",
         "legs waist", "legs shin spot", "legs buckle", "legs ankle ball", "legs back plate", "legs backplate", "head neck", "jump pack mount",
         "backpack mount", "weapon wrist", "shin pad inside", "pad inside"]
# joint: (host cut, child cuts, socket on the host, fit on the child, host types, child types)
JOINTS = {"shoulder": ("torso shoulder", ["arm shoulder disc"], "Shoulder R", "Shoulder R", ["Chests"], ["Arms"]),
          "neck": ("torso neck", ["head neck"], "Neck", "Neck", ["Chests"], ["Heads"]),
          "waist": ("torso waist", ["legs waist"], "Waist", "Waist", ["Chests"], ["Legs"]),
          "back": ("torso back", ["jump pack mount", "backpack mount"], "Back", "Back", ["Chests"], ["Jump Packs", "Backpacks"]),
          "wrist": ("arm wrist", ["weapon wrist"], "Hand R", "Hand R", ["Arms"], ["Melee", "Pistols", "Hands", "Shields"]),
          "pad": ("arm pad spot", ["pad inside"], "Pad R", "Pad R", ["Arms"], ["Shoulder Pads"]),
          "shin": ("legs shin spot", ["shin pad inside"], "Shin R", "Shin R", ["Legs"], ["Knee Pads"])}
MX = np.diag([-1.0, 1, 1, 1])
EXCLUDE = ("VeteranBladeSquad/Arms/",)   # parts left out of the reference for now (Josh, Nov 17: Bladeguard arms are a bad example of a normal fit)
TINY = 50            # triangles: a smaller object in a parts collection is a stray bit, not a part
GAP = 0.3            # mm: a placed pad's inside = its triangles within this of the spot cut
M4 = lambda a: np.array(a, float).reshape(4, 4)


ALIAS = {"belt buckle": "buckle"}   # Josh's wording -> the fixed name's ("Intercessor Legs belt buckle")


def cut_name(name):
    """(fixed name, armour type) of a cut: '<type> <fixed name> <anything>', the type optional (Josh, Nov 18: 'intercessor
    arm pad spot', 'Intercessor Legs belt buckle'; one cut per armour type). (None, None) if no fixed name"""
    n = re.sub(r"\s+", " ", re.sub(r"\.\d{3}$", "", name).lower()).strip()
    for a, b in ALIAS.items(): n = n.replace(a, b)
    w = n.split(" ")
    for i in range(len(w)):
        rest = " ".join(w[i:]); f = next((f for f in FIXED if rest.startswith(f)), None)
        if f: return f, " ".join(w[:i]) or None
    return None, None


def fixed(name): return cut_name(name)[0]


def tf(T, M): M = np.asarray(M); return T @ M[:3, :3].T + M[:3, 3]


def _keys(V): return set(map(tuple, np.round(np.asarray(V).reshape(-1, 3) * 500).astype(np.int64).tolist()))


def _kabsch(P, Q):
    cp, cq = P.mean(0), Q.mean(0); U, _, Vt = np.linalg.svd((P - cp).T @ (Q - cq))
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]); R = Vt.T @ D @ U.T; M = np.eye(4); M[:3, :3] = R; M[:3, 3] = cq - R @ cp; return M


def _edges(T):
    """each triangle's corners ordered by the length of the edge opposite, and those lengths"""
    L = np.stack([np.linalg.norm(T[:, 2] - T[:, 1], axis=1), np.linalg.norm(T[:, 0] - T[:, 2], axis=1), np.linalg.norm(T[:, 1] - T[:, 0], axis=1)], 1)
    o = np.argsort(L, 1); return np.take_along_axis(T, o[:, :, None], 1), np.take_along_axis(L, o, 1)


def frame_of(obj_tri, file_tri):
    """object mesh coordinates -> the file's coordinates (4x4), or None: identity if the object is the file; else from one
    triangle of the object found in the file by its three edge lengths, accepted when the object's corners land on the file's"""
    K = _keys(file_tri); V = obj_tri.reshape(-1, 3); V = V[::max(1, len(V) // 3000)]
    ok = lambda M: len(_keys(tf(V, M)) & K) >= 0.8 * len(_keys(tf(V, M)))
    if ok(np.eye(4)): return np.eye(4)
    Fo, Fl = _edges(file_tri); key = lambda L: tuple(np.round(L * 1000).astype(np.int64).tolist())
    table = {}
    for i, l in enumerate(Fl):
        if l[1] - l[0] > 0.01 and l[2] - l[1] > 0.01: table.setdefault(key(l), []).append(i)
    Oo, Ol = _edges(obj_tri); area = np.linalg.norm(np.cross(obj_tri[:, 1] - obj_tri[:, 0], obj_tri[:, 2] - obj_tri[:, 0]), axis=1)
    for i in np.argsort(-area)[:400]:
        l = Ol[i]
        if l[1] - l[0] <= 0.01 or l[2] - l[1] <= 0.01: continue
        for d in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            for j in table.get(tuple(a + b for a, b in zip(key(l), d)), [])[:4]:
                M = _kabsch(Oo[i], Fo[j])
                if np.abs(tf(Oo[i], M) - Fo[j]).max() < 0.005 and ok(M): return M
    return None


def read(blend, lib, pool=()):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False)
    idx = json.load(open(lib + "/_builder/index.json", encoding="utf-8"))
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    byname = {norm(e["name"]): e for e in idx["parts"]}; bystem = {}
    for r in list(csv.reader(open(lib + "/_sources.csv", encoding="utf-8-sig")))[1:]:
        if len(r) > 1: bystem.setdefault(norm(os.path.splitext(os.path.basename(r[1].replace("\\", "/")))[0]), []).append(r[0])
    cat = {e["path"][:-4].replace("\\", "/"): e["type"] for e in idx["parts"]}

    def resolve(name):
        """the library files the object's name can be (the library's name, else the maker's file name, e.g. both the
        L and R copies of '176-ChainSword-2'); the one whose mesh lines up with the object is kept below"""
        n = norm(re.sub(r"\.\d{3}$", "", name))
        if n in byname: return [byname[n]["path"][:-4].replace("\\", "/")]
        hits = bystem.get(n) or [p for s, ps in bystem.items() if s.startswith(n + "-") for p in ps]
        if not hits:                  # a copy lettered by hand: 'Forearm 2 a', 'Forearm 2.b' (CyberBrush forearm armour)
            m = re.sub(r"[ .][a-z]$", "", n); hits = bystem.get(m, []) if m != n else []
        return [h[:-4].replace("\\", "/") for h in sorted(set(hits))]

    toks = lambda s: set(re.findall(r"[a-z0-9]+", re.sub(r"#\d+|\.\d{3}$", "", s.lower()))) - {"marfil"}
    def like(name):
        """library files whose name holds every word of the object's (a shortened name: 'Bladeguard Axe 1A')"""
        t = toks(name)
        return [e["path"][:-4].replace("\\", "/") for e in idx["parts"] if t and t <= toks(e["name"])][:12]

    mks = {}
    def maker_mesh(rel):
        if rel not in mks:
            sc = json.load(open(lib + "/" + rel + ".sockets.json", encoding="utf-8-sig")); G = OG.from_file(sc)
            now = C.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)); mks[rel] = (sc, tf(now, np.linalg.inv(M4(G))) if G else now)
        return mks[rel]

    def tris(o):
        me = o.data; me.calc_loop_triangles(); n = len(me.loop_triangles)
        i = np.empty(n * 3, np.int64); me.loop_triangles.foreach_get("vertices", i)
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); return co.reshape(-1, 3)[i.reshape(-1, 3)]

    notes, parts, cuts = [], {}, {}
    for o in bpy.data.objects:
        cn = [c.name for c in o.users_collection]
        if o.type != "MESH" or not cn or any(c.startswith("ND.") for c in cn): continue
        T = tris(o); W = np.array(o.matrix_world)
        if any(c.lower().endswith(" cuts") for c in cn):
            f, kind = cut_name(o.name)
            if not f: notes.append("cut %r: not one of the fixed names, left out" % o.name); continue
            cuts[o.name] = {"fixed": f.replace("legs backplate", "legs back plate"), "kind": kind, "world": tf(T, W), "coll": cn[0]}; continue
        if len(T) < TINY: notes.append("object %r: %d triangles, a stray bit, left out" % (o.name, len(T))); continue
        # which file: its name (the library's, the maker's file name, or a shortened one), else, when the name says
        # otherwise (a renamed copy), the mesh against the files the reference is built from (pool)
        named = resolve(o.name) or like(re.sub(r"\.\d{3}$", "", o.name)); O2M = None
        for rel in named + [r for r in pool if r not in named]:
            sc, mk = maker_mesh(rel); O2M = frame_of(T, mk)
            if O2M is not None: break
        if O2M is None: notes.append("part %r: its mesh is none of %s, left out" % (o.name, " / ".join(os.path.basename(r) for r in named) or "the reference's files")); continue
        if rel not in named: notes.append("part %r is %s (by its mesh; the name says otherwise)" % (o.name, os.path.basename(rel)))
        if any(x in rel for x in EXCLUDE): notes.append("part %r (%s): left out for now" % (o.name, os.path.basename(rel))); continue
        parts[o.name] = {"rel": rel, "cat": cat.get(rel), "Wm": W @ np.linalg.inv(O2M), "world": tf(T, W), "sc": OG.maker_view(sc), "maker_tri": mk}
    keys = {n: _keys(p["world"]) for n, p in parts.items()}
    for n, c in cuts.items():                                    # the part a cut was taken from: the corner points they share
        k = _keys(c["world"]); sh = sorted(((len(k & pk), pn) for pn, pk in keys.items()), reverse=True)
        if not sh or sh[0][0] < 3: notes.append("cut %r: shares no points with a part, left out" % n); c["part"] = None; continue
        c["part"] = sh[0][1]
    cuts = {n: c for n, c in cuts.items() if c["part"]}
    side = lambda n, c: {"cut": n, "kind": c.get("kind"), "part": parts[c["part"]]["rel"], "obj": c["part"], "tri": tf(c["world"], np.linalg.inv(parts[c["part"]]["Wm"]))}
    joints = {}
    inst = {}                                                    # library file -> its objects (copies too)
    for pn, p in parts.items(): inst.setdefault(p["rel"], []).append(pn)
    surfs = {}
    def surf(pn):
        if pn not in surfs: surfs[pn] = C.Surface(parts[pn]["world"], spacing=0.1, most=100000)
        return surfs[pn]
    world = lambda x: tf(x["tri"], parts[x["obj"]]["Wm"])
    mirrored = lambda pn: np.linalg.det(parts[pn]["Wm"][:3, :3]) < 0
    for jn, (hc, ccs, sock, fit, htypes, ctypes) in JOINTS.items():
        hosts = [side(n, c) for n, c in sorted(cuts.items()) if c["fixed"] == hc]
        if not hosts: notes.append("joint %s: no %r cut" % (jn, hc)); continue
        if jn == "shin" and "waist" in joints:                # each shin spot's side, in the waist's frame (+X = the right)
            for h in hosts: h["side"] = "R" if tf(world(h).reshape(-1, 3).mean(0)[None], np.linalg.inv(joints["waist"]["Jw"]))[0, 0] > 0 else "L"
        right = [h for h in hosts if h.get("side", "R") == "R"] or hosts
        kids = [side(n, c) for n, c in sorted(cuts.items()) if c["fixed"] in ccs]
        if jn in ("pad", "shin", "wrist"):   # a placed pad / weapon with no cut of its own: its inside = what of it rests on a (right) spot cut, on any copy of that part
            have = {k["part"] for k in kids}; spots_w = []
            for h in right:
                for pn in inst[h["part"]]: spots_w.append(tf(h["tri"], parts[pn]["Wm"]))
            spot = C.Surface(np.concatenate(spots_w), spacing=0.03)
            best = {}                     # one per file: the copy with the most of it resting on a spot (another copy may only graze one)
            cut_rels = {h["part"] for h in right}; host_objs = [pn for pn, p in parts.items() if p["cat"] in htypes]
            def rests_on(pn):             # None if it sits on a part that carries the cut (as well as on any, within 80%: Arm 2A and 2B are one shape at the shoulder); else the part it does sit on
                X = parts[pn]["world"].mean(1); X = X[::max(1, len(X) // 3000)]
                t = {h: float(np.mean(surf(h).dist(X)[1] < GAP)) for h in host_objs}
                if not t: return None
                top = max(t, key=t.get); on_cut = max((v for h, v in t.items() if parts[h]["rel"] in cut_rels), default=0.0)
                return None if on_cut >= 0.8 * t[top] else top
            for pn, p in parts.items():
                if p["cat"] not in ctypes or p["rel"] in have or mirrored(pn): continue
                keep = p["world"][spot.dist(p["world"].mean(1))[1] < GAP]
                other = rests_on(pn) if len(keep) >= 20 else None
                if other: notes.append("%s: sits on %s, which has no %s cut: not used" % (pn, other, hc)); continue
                flush = int(np.sum(spot.dist(keep.mean(1))[1] < 0.05))   # the copy the cut was taken under sits flush on it; another only crosses it
                if len(keep) >= 20 and flush > best.get(p["rel"], (-1,))[0]: best[p["rel"]] = (flush, pn, keep)
            for rel, (_, pn, keep) in sorted(best.items()):
                kids.append({"cut": ccs[0] + " (from the placed %s)" % pn, "part": rel, "obj": pn, "tri": tf(keep, np.linalg.inv(parts[pn]["Wm"]))})
        if not kids: notes.append("joint %s: no child cut (%s) or placed part" % (jn, " / ".join(ccs))); continue
        # the joint's frame in the reference's world (a convention): the first (right) host's own socket, else its cut's middle
        x0 = right[0]; h0 = parts[x0["obj"]]; S = next((M4(s["matrix"]) for s in h0["sc"].get("sockets") or [] if s.get("type") == sock), None)
        if jn == "shin":                                      # the shin he cut: the side whose library socket is nearest it
            mid = x0["tri"].reshape(-1, 3).mean(0); best = None
            for s_ in h0["sc"].get("sockets") or []:
                if s_.get("type") in ("Shin R", "Shin L"):
                    d = float(np.linalg.norm(M4(s_["matrix"])[:3, 3] - mid))
                    if best is None or d < best[0]: best = (d, s_["type"], M4(s_["matrix"]))
            if best: sock, S = best[1], best[2]; fit = sock
        if S is not None: Jw0 = h0["Wm"] @ S; conv = "the reference host's %s socket" % sock
        else:
            Jw0 = np.eye(4); Jw0[:3, 3] = world(x0).reshape(-1, 3).mean(0); conv = "the host cut's middle"
        # every other cut takes the joint from the known part sat on it (docs/PLAN.md: each part sits against a Mar Fil
        # part): a host cut from the child placed on it, a child cut from the host it sits on. A file's joint is the same
        # on every copy of it. A mirrored copy (a left shin pad) gives the left joint: right = left mirrored.
        kh, kk = {}, {}                                       # (library file, side) -> the joint in its maker coordinates
        def setJ(role, x, Jw):
            x["J"] = np.linalg.inv(parts[x["obj"]]["Wm"]) @ Jw; (kh if role == "host" else kk)[(x["part"], x.get("side", "R"))] = x["J"]
        setJ("host", x0, Jw0)
        todo = [("host", h) for h in hosts if h is not x0] + [("kid", k) for k in kids]
        while todo:
            done = []
            for role, x in todo:
                mine, other = (kh, kk) if role == "host" else (kk, kh)
                key = (x["part"], x.get("side", "R"))
                if key in mine: x["J"] = mine[key]; done.append((role, x)); continue
                X = world(x).reshape(-1, 3); X = X[::max(1, len(X) // 300)]; best = None
                for (rel, sd), J in other.items():
                    if sd != "R": continue
                    for pn in inst[rel]:
                        if pn == x["obj"]: continue
                        d = float(np.median(surf(pn).dist(X)[1]))
                        if best is None or d < best[0]: best = (d, pn, J)
                if best and best[0] <= 1.5:
                    Jw = parts[best[1]]["Wm"] @ best[2] @ (MX if mirrored(best[1]) else np.eye(4))
                    x["joint_from"] = best[1]; setJ(role, x, Jw); done.append((role, x))
            if not done:
                for role, x in todo:
                    notes.append("joint %s: %r has no Mar Fil part sat on it to take the joint from: the main reference's assumed" % (jn, x["cut"]))
                    setJ(role, x, Jw0)
                break
            todo = [t for t in todo if not any(t[1] is d_[1] for d_ in done)]
        joints[jn] = {"socket": sock, "fit": fit, "host_types": htypes, "child_types": ctypes, "hosts": hosts, "children": kids, "frame": conv, "Jw": Jw0,
                      "host_J": {"%s|%s" % k: v for k, v in kh.items()}}
    # the other cuts (buckle, wrist armour, back plate): their surface, part and world pose, for the callers that use them
    spots = {}
    for n, c in sorted(cuts.items()):
        if c["fixed"] not in {x for j in JOINTS.values() for x in [j[0]] + j[1]}:
            e = side(n, c); e["Wm"] = parts[c["part"]]["Wm"]; spots.setdefault(c["fixed"], []).append(e)
    return {"parts": {n: {"rel": p["rel"], "Wm": p["Wm"], "mid": p["world"].reshape(-1, 3).mean(0)} for n, p in parts.items()}, "joints": joints, "spots": spots, "notes": notes}
