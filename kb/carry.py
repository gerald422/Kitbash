"""Fits and sockets for a new arm, legs or torso, carried from the already-fitted parts of the same type that sit
beside it in its library folder (notes 091). How the folder's fitted parts relate decides how a joint is carried:

  same    every fitted part has one and the same matrix (a kit frame)     -> the matrix is copied
  turn    they share the turn, only the place differs (one orientation)   -> the joint's region is moved onto the
                                                                             new part without turning it
  rigid   neither                                                         -> the region (and the whole shape) is
                                                                             matched with turning

and a gate decides whether it is kept (leave-one-out on the library, tests/kb/loo_carry.py: what the gates keep was
right every time; what they drop is filed without a fit and logged with its number):

  same    the joint has to lie on the new part as it does on its siblings (within GATES['on'] mm of their distance)
  turn    region match <= 0.12 mm
  rigid   legs / torsos: region match <= 0.10 mm; arms only when it is nearly the same arm (region <= 0.07 and whole
          shape <= 0.10 mm): with no convention in the folder a round shoulder says nothing about the arm's turn
  and, turn / rigid: every reference that matches within the gate has to place the joint within 0.5 mm and 3 deg of the
  best one's place (fitted parts of one folder don't always agree: a pose family can carry its own turn)

    from kb import carry
    refs = [carry.Ref(name, sidecar, stl_path), ...]            # fitted parts of the same type, same folder
    got = carry.like("Arms", carry.Shape(new_stl, scale), refs, stem="Maker - Arm 3 R")
    got["fits"], got["sockets"], got["how"] (mode / reference / match per joint), got["rejected"] (why not)

Arms get their Shoulder R or L fit (an arm with fitted siblings only on the other side is tried against their
mirror images). Legs get their Waist / Flat Waist fit and, with the same move, the reference's belt sockets (Hip,
Belt Front / Back, Buckle, Plate, Trophy: all within 16 mm of the waist); Base by the flat-legs rule (under the
lowest 0.6 mm of the part, the reference's up and front) when the reference's base came from that rule. Torsos get
Shoulder R / L, Neck, Back, Waist / Flat Waist sockets, each by its own region. numpy + kb.geo.kdtree (scipy, or
Blender's KD tree).
"""
import numpy as np
from . import geo

DT = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
TORSO = ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist", "Flat Waist")
RADIUS = {"Arms": 6.0, "Legs": 13.0, "Chests": 7.0}            # the region round a joint, mm
GATES = {"turn": 0.12, "rigid": 0.10, "arm_rigid": 0.07, "arm_whole": 0.10, "on": 0.5, "belt": 16.0, "agree_mm": 0.5, "agree_deg": 3.0}
MX = np.diag([-1.0, 1, 1, 1])
ROTS = geo.rots24()


def soup(path, scale=1.0):
    """the triangles of a binary STL as they are, (n, 3, 3): no welding, which a surface sample doesn't need"""
    return np.fromfile(path, dtype=DT, offset=84)["v"].astype(float) * scale
def sample(tri, n, seed=0):
    a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(seed); i = rng.choice(len(tri), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n)
    m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]; t = tri[i]
    return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
def M4(R, t): M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M
def flat(M): return [round(float(x), 6) for x in np.asarray(M).reshape(-1)]
def ang(A, B): return geo.ang(A[:3, :3].T @ B[:3, :3])
def point(kind, X):
    """where the joint is in the part's own coordinates: a fit maps the part into its socket, a socket sits on it"""
    return np.linalg.inv(X)[:3, 3] if kind == "fit" else X[:3, 3]
def swap(name): return name[:-1] + {"R": "L", "L": "R"}[name[-1]] if name[-2:] in (" R", " L") else name


class Shape:
    """a part's surface: 60,000 points (S), 3,000 of them (full), its corners (V) and sorted box (ext)"""
    def __init__(self, path, scale=1.0, seed=0, mirror=False):
        tri = soup(path, scale)
        if mirror: tri = tri * np.array([-1.0, 1, 1])
        self.V = tri.reshape(-1, 3); self.ext = np.sort(np.ptp(self.V, 0))
        self.S = sample(tri, 60000, seed); self.full = self.S[np.random.default_rng(2).choice(60000, 3000, replace=False)]
        self._tree = None
    @property
    def tree(self):
        if self._tree is None: self._tree = geo.kdtree(self.S)
        return self._tree


class Ref:
    """a fitted part of the folder: its name, sidecar and (read when first needed) its shape"""
    def __init__(self, name, sc, path, mirror=False):
        self.name, self.sc, self.path, self.mirror, self._shape, self._ext = name, sc, path, mirror, None, None
    @property
    def ext(self):
        """the part's sorted box, read without sampling it: cheap enough to rank every part of a folder"""
        if self._ext is None:
            try: self._ext = np.sort(np.ptp(soup(self.path, self.sc.get("scale", 1.0)).reshape(-1, 3), 0))
            except (OSError, ValueError): self._ext = np.full(3, 9e9)
        return self._ext
    @property
    def shape(self):
        if self._shape is None: self._shape = Shape(self.path, self.sc.get("scale", 1.0), 1, self.mirror)
        return self._shape
    def mirrored(self):
        """the other side's part: the shape mirrored in X, every fit conjugated and its side swapped"""
        sc = dict(self.sc, sockets=[], fits={swap(k): flat(MX @ np.array(F).reshape(4, 4) @ MX) for k, F in self.sc.get("fits", {}).items()})
        return Ref(self.name + " (mirrored)", sc, self.path, not self.mirror)


def joints(cat, sc):
    """name -> ('fit' | 'sock', 4x4): what a part of this type is carried by"""
    if cat in ("Arms", "Legs"):
        return {k: ("fit", np.array(F).reshape(4, 4)) for k, F in (sc.get("fits") or {}).items()}
    return {s["type"]: ("sock", np.array(s["matrix"]).reshape(4, 4)) for s in sc.get("sockets") or [] if s["type"] in TORSO}


def regime(kind, Xs):
    if len(Xs) < 2: return "rigid"
    tu = max(ang(Xs[0], X) for X in Xs); P = np.array([point(kind, X) for X in Xs])
    sp = float(np.linalg.norm(P - np.median(P, 0), axis=1).max())
    return "same" if tu < 0.5 and sp < 0.05 else "turn" if tu < 0.5 else "rigid"


def shift_icp(src, tree, t, iters=30, keep=0.85):
    """move src onto the tree's points without turning it"""
    for _ in range(iters):
        d, i = tree.query(src + t); m = d <= np.quantile(d, keep)
        t = t + (tree.data[i[m]] - (src[m] + t)).mean(0)
    return t


def carry_joint(cat, mode, part, ref, kind, X):
    """the reference's joint X carried onto the part: (matrix, the move reference -> part, region median, whole
    median), or None when the reference has no surface round the joint"""
    S, full, tree = ref.S, ref.full, part.tree
    reg = S[np.linalg.norm(S - point(kind, X), axis=1) < RADIUS[cat]]
    if len(reg) < 150: return None
    if len(reg) > 1500: reg = reg[np.random.default_rng(3).choice(len(reg), 1500, replace=False)]
    I, Q = np.eye(3), part.S
    if mode == "same":
        cands = [(I, np.zeros(3))]
    elif mode == "turn":
        cands = [(I, shift_icp(reg, tree, shift_icp(full, tree, t0, 20), 30)) for t0 in (np.zeros(3), Q.mean(0) - full.mean(0))]
    else:
        sub = full[:400]; coarse = []
        for R0 in ROTS:
            R, t, d = geo.icp(sub, tree, R0, Q.mean(0) - R0 @ full.mean(0), 20); coarse.append((float(np.median(d)), R, t))
        cands = []
        for R, t in [(R, t) for _, R, t in sorted(coarse, key=lambda c: c[0])[:3]] + [(I, np.zeros(3))]:
            R, t, d = geo.icp(full, tree, R, t, 30); R, t, d = geo.icp(reg, tree, R, t, 30); cands.append((R, t))
    best = None
    for R, t in cands:
        m = float(np.median(tree.query(reg @ R.T + t)[0])); mw = float(np.median(tree.query(full @ R.T + t)[0]))
        if best is None or m + 0.15 * mw < best[0]: best = (m + 0.15 * mw, m, mw, R, t)
    _, m, mw, R, t = best; M = M4(R, t)
    return (X @ np.linalg.inv(M)) if kind == "fit" else (M @ X), M, m, mw


def _sock(stem, typ, X, why, points=None):
    s = {"type": typ, "name": "%s_socket_%s" % (stem, typ), "matrix": flat(X), "display_type": "ARROWS", "display_size": 3.0,
         "props": {"tiow_from": why}}
    if points is not None: s["points"] = [[round(float(x), 6) for x in p] for p in points]
    return s


def _pass(cat, part, refs, G, k):
    """one go over the references: {name: (kind, matrix, move, ref, how)} kept, {name: why} dropped, {name: how}"""
    kept, dropped, hows = {}, {}, {}
    for name in sorted({n for r in refs for n in joints(cat, r.sc)}):
        rs = [r for r in refs if name in joints(cat, r.sc)]
        kind = joints(cat, rs[0].sc)[name][0]; mode = regime(kind, [joints(cat, r.sc)[name][1] for r in rs])
        close = lambda r: float(np.abs(r.ext - part.ext).sum())
        use = sorted(rs, key=close)[:1 if mode == "same" else k]       # the fitted parts nearest in size
        all_ = []
        for r in use:
            try: got = carry_joint(cat, mode, part, r.shape, kind, joints(cat, r.sc)[name][1])
            except OSError: continue
            if got: all_.append(got + (r,))
        if not all_: dropped[name] = "no fitted part beside it has a surface round this joint"; continue
        best = min(all_, key=lambda g: g[2] + 0.15 * g[3])
        X, M, m, mw, r = best; why = None
        how = {"mode": mode, "from": r.name, "match": round(m, 3), "whole": round(mw, 3)}
        if mode == "same":
            near = lambda sh, p: float(np.linalg.norm(sh.S - p, axis=1).min())
            mine = near(part, point(kind, X)); theirs = max(near(q.shape, point(kind, joints(cat, q.sc)[name][1])) for q in sorted(rs, key=close)[:3])
            how["off"] = round(mine, 2)
            if mine > theirs + G["on"]: why = "the joint is %.1f mm off this part (%.1f on its siblings): it isn't in their frame" % (mine, theirs)
        elif mode == "turn":
            if m > G["turn"]: why = "its joint region is %.2f mm off the nearest fitted sibling's (limit %.2f): place it by eye" % (m, G["turn"])
        elif cat == "Arms":
            if m > G["arm_rigid"] or mw > G["arm_whole"]:
                why = "the arms beside it share no turn and it is no near-copy of one (region %.2f, whole %.2f mm): place it by eye" % (m, mw)
        elif m > G["rigid"]: why = "its joint region is %.2f mm off the nearest fitted sibling's (limit %.2f): place it by eye" % (m, G["rigid"])
        if why is None and mode != "same":                         # the fitted parts that match it as well have to agree
            lim = G["arm_rigid"] if (mode == "rigid" and cat == "Arms") else G[mode]
            for X2, M2, m2, mw2, r2 in all_:
                if r2 is r or m2 > lim: continue
                mm, dg = float(np.linalg.norm(point(kind, X2) - point(kind, X))), ang(X2, X)
                if mm > G["agree_mm"] or dg > G["agree_deg"]:
                    why = "%s and %s both match it but would place it %.1f mm / %.0f deg apart: place it by eye" % (r.name, r2.name, mm, dg); break
        hows[name] = how
        if why: dropped[name] = why
        else: kept[name] = (kind, X, M, r, how)
    return kept, dropped, hows


def like(cat, part, refs, stem="part", gates=None, k=4, mirror=True):
    """Carry what the folder's fitted parts have onto `part` (a Shape). -> {"fits", "sockets", "how", "rejected"}"""
    G = dict(GATES, **(gates or {})); out = {"fits": {}, "sockets": [], "how": {}, "rejected": {}}
    refs = [r for r in refs if joints(cat, r.sc)]
    if not refs:
        out["rejected"]["*"] = "no fitted part of this type beside it to carry from"; return out
    kept, dropped, hows = _pass(cat, part, refs, G, k)
    if cat == "Arms" and not kept and mirror:                     # only fitted arms of the other side beside it?
        k2, d2, h2 = _pass(cat, part, [r.mirrored() for r in refs], G, k)
        if k2: kept, dropped, hows = k2, {}, h2
    if cat in ("Arms", "Legs") and len(kept) > 1:                 # one shoulder, one waist: the better match
        best = min(kept, key=lambda n: kept[n][4]["match"] + 0.15 * kept[n][4]["whole"])
        for n in [n for n in kept if n != best]: dropped[n] = "the %s match is better" % best; del kept[n]
    out["how"], out["rejected"] = hows, {n: w for n, w in dropped.items() if n not in kept}
    for name, (kind, X, M, r, how) in kept.items():
        tag = "carried from %s (%s, match %.2f mm)" % (r.name, how["mode"], how["match"])
        if kind == "fit": out["fits"][name] = flat(X)
        else: out["sockets"].append(_sock(stem, name, X, tag))
    if cat == "Legs" and kept:
        name, (kind, X, M, r, how) = next(iter(kept.items())); w = point("fit", joints(cat, r.sc)[name][1])
        for s in r.sc.get("sockets") or []:
            S = np.array(s["matrix"]).reshape(4, 4); t = s["type"]; src = (s.get("props") or {}).get("tiow_from", "")
            if t.startswith("Shin"): continue                     # TIOW Inbox finds shins itself
            if t == "Base":
                if how["mode"] == "same": out["sockets"].append(_sock(stem, t, S, "as %s (the same frame)" % r.name))
                elif src.startswith("flat-legs rule"):
                    Rb = M[:3, :3] @ S[:3, :3]; up = Rb[:, 2]; h = part.V @ up; foot = part.V[h < h.min() + 0.6].mean(0)
                    out["sockets"].append(_sock(stem, t, M4(Rb, foot - (foot @ up - h.min()) * up), "flat-legs rule: under the feet, Z up, Y front (up and front from %s)" % r.name))
                else: out["rejected"]["Base"] = "%s's base is not from the flat-legs rule (%s): not carried" % (r.name, src[:40] or "no source")
            elif float(np.linalg.norm(S[:3, 3] - w)) <= G["belt"]:
                pts = None if s.get("points") is None else (np.c_[np.array(s["points"], float), np.ones(len(s["points"]))] @ M.T)[:, :3]
                out["sockets"].append(_sock(stem, t, M @ S, "carried from %s with its waist (%s, match %.2f mm)" % (r.name, how["mode"], how["match"]), pts))
    if cat == "Chests" and kept and all(v[4]["mode"] == "same" for v in kept.values()):
        r = next(iter(kept.values()))[3]                          # a kit frame: what every fitted torso agrees on comes too
        for s in r.sc.get("sockets") or []:
            if s["type"] in TORSO: continue
            S = np.array(s["matrix"]).reshape(4, 4); others = [np.array(o["matrix"]).reshape(4, 4) for q in refs for o in q.sc.get("sockets") or [] if o["type"] == s["type"]]
            if len(others) >= len(refs) and all(ang(S, O) < 0.5 and np.linalg.norm(S[:3, 3] - O[:3, 3]) < 0.05 for O in others):
                out["sockets"].append(_sock(stem, s["type"], S, "as %s (the same frame)" % r.name))
    return out
