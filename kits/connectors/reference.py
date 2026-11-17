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
         "legs waist", "legs shin spot", "legs buckle", "legs back plate", "legs backplate", "head neck", "jump pack mount",
         "backpack mount", "weapon wrist", "shin pad inside", "pad inside"]
# joint: (host cut, child cuts, socket on the host, fit on the child, host types, child types)
JOINTS = {"shoulder": ("torso shoulder", ["arm shoulder disc"], "Shoulder R", "Shoulder R", ["Chests"], ["Arms"]),
          "neck": ("torso neck", ["head neck"], "Neck", "Neck", ["Chests"], ["Heads"]),
          "waist": ("torso waist", ["legs waist"], "Waist", "Waist", ["Chests"], ["Legs"]),
          "back": ("torso back", ["jump pack mount", "backpack mount"], "Back", "Back", ["Chests"], ["Jump Packs", "Backpacks"]),
          "wrist": ("arm wrist", ["weapon wrist"], "Hand R", "Hand R", ["Arms"], ["Melee", "Pistols", "Hands", "Shields"]),
          "pad": ("arm pad spot", ["pad inside"], "Pad R", "Pad R", ["Arms"], ["Shoulder Pads"]),
          "shin": ("legs shin spot", ["shin pad inside"], "Shin R", "Shin R", ["Legs"], ["Knee Pads"])}
GAP = 0.3            # mm: a placed pad's inside = its triangles within this of the spot cut
M4 = lambda a: np.array(a, float).reshape(4, 4)


def fixed(name):
    n = re.sub(r"\.\d{3}$", "", name).lower().strip()
    return next((f for f in FIXED if n.startswith(f)), None)


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


def read(blend, lib):
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
        return [h[:-4].replace("\\", "/") for h in sorted(set(hits))]

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
            f = fixed(o.name)
            if not f: notes.append("cut %r: not one of the fixed names, left out" % o.name); continue
            cuts[o.name] = {"fixed": f.replace("legs backplate", "legs back plate"), "world": tf(T, W), "coll": cn[0]}; continue
        cands = resolve(o.name)
        if not cands: notes.append("part %r: no library file by that name, left out" % o.name); continue
        for rel in cands:
            sc = json.load(open(lib + "/" + rel + ".sockets.json", encoding="utf-8-sig")); G = OG.from_file(sc)
            now = C.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)); mk = tf(now, np.linalg.inv(M4(G))) if G else now
            O2M = frame_of(T, mk)
            if O2M is not None: break
        if O2M is None: notes.append("part %r (%s): its mesh could not be lined up with the library file, left out" % (o.name, " or ".join(cands))); continue
        parts[o.name] = {"rel": rel, "cat": cat.get(rel), "Wm": W @ np.linalg.inv(O2M), "world": tf(T, W), "sc": OG.maker_view(sc), "maker_tri": mk}
    keys = {n: _keys(p["world"]) for n, p in parts.items()}
    for n, c in cuts.items():                                    # the part a cut was taken from: the corner points they share
        k = _keys(c["world"]); sh = sorted(((len(k & pk), pn) for pn, pk in keys.items()), reverse=True)
        if not sh or sh[0][0] < 3: notes.append("cut %r: shares no points with a part, left out" % n); c["part"] = None; continue
        c["part"] = sh[0][1]
    cuts = {n: c for n, c in cuts.items() if c["part"]}
    side = lambda n, c: {"cut": n, "part": parts[c["part"]]["rel"], "obj": c["part"], "tri": tf(c["world"], np.linalg.inv(parts[c["part"]]["Wm"]))}
    joints = {}
    for jn, (hc, ccs, sock, fit, htypes, ctypes) in JOINTS.items():
        hosts = [side(n, c) for n, c in sorted(cuts.items()) if c["fixed"] == hc]
        if not hosts: notes.append("joint %s: no %r cut" % (jn, hc)); continue
        kids = [side(n, c) for n, c in sorted(cuts.items()) if c["fixed"] in ccs]
        if jn in ("pad", "shin") and not kids:               # the pad's inside: what of the placed pad rests on the spot
            spot = C.Surface(np.concatenate([cuts[h["cut"]]["world"] for h in hosts]), spacing=0.03)
            for pn, p in parts.items():
                if p["cat"] not in ctypes: continue
                keep = p["world"][spot.dist(p["world"].mean(1))[1] < GAP]
                if len(keep) >= 20: kids.append({"cut": ccs[0] + " (from the placed %s)" % pn, "part": p["rel"], "obj": pn, "tri": tf(keep, np.linalg.inv(p["Wm"]))})
        if not kids: notes.append("joint %s: no child cut (%s) or placed part" % (jn, " / ".join(ccs))); continue
        # the joint's frame in the reference's world (a convention): the first host's own socket, else the host cuts' middle
        h0 = parts[hosts[0]["obj"]]; S = next((M4(s["matrix"]) for s in h0["sc"].get("sockets") or [] if s.get("type") == sock), None)
        if jn == "shin":                                      # the shin he cut: the side whose library socket is nearest it
            mid = tf(hosts[0]["tri"], np.eye(4)).reshape(-1, 3).mean(0); best = None
            for s in h0["sc"].get("sockets") or []:
                if s.get("type") in ("Shin R", "Shin L"):
                    d = float(np.linalg.norm(M4(s["matrix"])[:3, 3] - mid))
                    if best is None or d < best[0]: best = (d, s["type"], M4(s["matrix"]))
            if best: sock, S = best[1], best[2]; fit = sock
        if S is not None: Jw = h0["Wm"] @ S; conv = "the reference host's %s socket" % sock
        else:
            Jw = np.eye(4); Jw[:3, 3] = np.concatenate([cuts[h["cut"]]["world"] for h in hosts]).reshape(-1, 3).mean(0); conv = "the host cut's middle"
        for x in hosts + kids: x["J"] = np.linalg.inv(parts[x["obj"]]["Wm"]) @ Jw
        joints[jn] = {"socket": sock, "fit": fit, "host_types": htypes, "child_types": ctypes, "hosts": hosts, "children": kids, "frame": conv, "Jw": Jw}
    # the other cuts (buckle, wrist armour, back plate): their surface, part and world pose, for the callers that use them
    spots = {}
    for n, c in sorted(cuts.items()):
        if c["fixed"] not in {x for j in JOINTS.values() for x in [j[0]] + j[1]}:
            e = side(n, c); e["Wm"] = parts[c["part"]]["Wm"]; spots.setdefault(c["fixed"], []).append(e)
    return {"parts": {n: {"rel": p["rel"], "Wm": p["Wm"]} for n, p in parts.items()}, "joints": joints, "spots": spots, "notes": notes}
