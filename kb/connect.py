"""Connectors (notes 096-098): Josh's hand-cut mating surfaces, found on a part by shape.

A connector is an open surface cut in place from a reference part, so it is in that part's file coordinates. find()
looks for it anywhere on another part and returns the pose that carries the connector onto that part (connector coords
-> part coords); the part's joint is then the reference's joint moved by that pose.

How find() works (numpy, plus geo.kdtree for the final settle; no scipy needed):
  1. The part's surface is sampled densely; a voxel grid marks where its surface is (within ~0.2 mm).
  2. Candidate places: one point every ~0.35 mm over the part, each with a smoothed normal. The connector's anchor
     (its point nearest its middle, with its normal) is put on each, normal to normal, and spun about the normal in
     15 deg steps. Each pose is scored by how many of the connector's points land on the part's surface (the grid).
  3. The best few places are settled by ICP and scored by the distance to the surface (point to plane, so it does
     not depend on how densely a part is sampled). The best wins.
  4. Round connectors (neck, wrist, waist, pad spot) do not fix the turn about their own axis: among turns that fit
     as well, the one closest to the part's own file frame is kept (Mar Fil exports in its kit frame, notes 096).

Left parts are mirrored first (as the library does), keeping their faces outward.
"""
import numpy as np
from kb import geo

SPIN = 15.0          # deg between spins in the search
GRID = 0.15          # mm, voxel of the surface grid (dilated one voxel: hits within ~0.15-0.25 mm)
CAND = 0.35          # mm, spacing of candidate places on the part
KEEP = 12            # places settled by ICP



def soup(path, scale=1.0):
    """the triangles of a binary STL as they are, (n, 3, 3)"""
    dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return np.fromfile(path, dtype=dt, offset=84)["v"].astype(float) * scale


def _rot(ax, deg):
    ax = np.asarray(ax, float); ax = ax / np.linalg.norm(ax); th = np.radians(deg)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def _tangents(N):
    """two unit vectors across each normal"""
    a = np.where(np.abs(N[:, :1]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))
    U = np.cross(N, a); U /= np.linalg.norm(U, axis=1)[:, None]; return U, np.cross(N, U)


class Surface:
    """a surface as triangles: dense samples (S) with their normals (N), a nearest-point tree, a surface grid"""
    def __init__(self, tri, mirror=False, spacing=0.12, seed=0, most=400000):
        tri = np.asarray(tri, float)
        if mirror: tri = (tri * np.array([-1.0, 1, 1]))[:, [0, 2, 1]]          # mirrored, faces still outward
        fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); a = np.linalg.norm(fn, axis=1); ok = a > 1e-12
        tri, fn, a = tri[ok], fn[ok] / a[ok, None], a[ok] / 2
        self.tri = tri; self.area = float(a.sum())
        n = int(np.clip(self.area / spacing ** 2, 20000, most)); rng = np.random.default_rng(seed)
        i = rng.choice(len(tri), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n); m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]
        t = tri[i]; self.S = t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0]); self.N = fn[i]
        self._tree = None; self._grid = None

    @property
    def tree(self):
        if self._tree is None: self._tree = geo.kdtree(self.S)
        return self._tree

    def patches(self, h):
        """one point per h-sized voxel (the mean of the samples in it) with the mean normal; voxels where the normals
        cancel (a thin edge: both sides in one voxel) are left out. Kept per h (find_all asks once per connector)"""
        if not hasattr(self, "_patches"): self._patches = {}
        if h not in self._patches: self._patches[h] = self._make_patches(h)
        return self._patches[h]

    def _make_patches(self, h):
        k = np.floor((self.S - self.S.min(0)) / h).astype(np.int64)
        _, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True); inv = inv.reshape(-1)
        P = np.zeros((len(cnt), 3)); Nn = np.zeros((len(cnt), 3)); np.add.at(P, inv, self.S); np.add.at(Nn, inv, self.N)
        P /= cnt[:, None]; L = np.linalg.norm(Nn, axis=1); keep = (L > 0.6 * cnt) & (cnt >= 3)
        return P[keep], Nn[keep] / L[keep, None]

    def grid(self):
        """(origin, voxel, boolean grid) of where the surface is, dilated by one voxel"""
        if self._grid is None:
            h = GRID; o = self.S.min(0) - 3 * h; k = np.floor((self.S - o) / h).astype(np.int64); shape = k.max(0) + 4
            while np.prod(shape.astype(float)) > 6e7:                           # a very big part: coarser voxels
                h *= 1.25; o = self.S.min(0) - 3 * h; k = np.floor((self.S - o) / h).astype(np.int64); shape = k.max(0) + 4
            G = np.zeros(tuple(shape), bool); G[k[:, 0], k[:, 1], k[:, 2]] = True
            D = G.copy()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx or dy or dz: D |= np.roll(np.roll(np.roll(G, dx, 0), dy, 1), dz, 2)
            self._grid = (o, h, D)
        return self._grid

    def on(self, X):
        """for points X (..., 3): is each on the surface (in the grid)"""
        o, h, G = self.grid(); k = np.floor((X - o) / h).astype(np.int64)
        inside = np.all((k >= 0) & (k < np.array(G.shape)), axis=-1); k = np.where(inside[..., None], k, 0)
        return inside & G[k[..., 0], k[..., 1], k[..., 2]]

    def dist(self, X):
        """(point-to-plane distance, euclidean distance) of points X to the surface, via the nearest sample"""
        d, i = self.tree.query(X); return np.abs(np.einsum("ij,ij->i", X - self.S[i], self.N[i])), d


class Connector:
    """a connector surface in its reference part's file coordinates"""
    def __init__(self, tri, name=""):
        self.name = name; self.surf = Surface(tri, spacing=0.05, most=100000); S = self.surf.S
        rng = np.random.default_rng(1)
        self.fine = S[rng.choice(len(S), min(800, len(S)), replace=False)]           # settling (ICP) and the score
        self.coarse = S[rng.choice(len(S), min(48, len(S)), replace=False)]          # the search
        self.c = S.mean(0); w, v = np.linalg.eigh(np.cov((S - self.c).T)); self.axis = v[:, 0]   # its flattest direction
        P, Nn = self.surf.patches(0.4); j = int(np.argmin(np.linalg.norm(P - self.c, axis=1)))
        self.anchor, self.anchor_n = P[j], Nn[j]
        self.box = np.ptp(S, 0)
        # round = it matches itself turned 30 deg about its axis (decided once, from its own shape: on a part the
        # disc's little extra can look keyed and its turn left to the shape, 60-80 deg off on Intercessor arms, notes 100)
        X = (self.fine - self.c) @ _rot(self.axis, 30.0).T + self.c; self.turned30 = float(np.median(self.surf.dist(X)[0]))
        self.round = self.turned30 <= ROUND

    @classmethod
    def from_stl(cls, path, name=""):
        return cls(soup(path), name or path)


def _poses(con, P, Nn, spins):
    """all candidate poses (R, t) putting the connector's anchor on each place P (normal on normal), spun"""
    Ua, Va = _tangents(con.anchor_n[None]); Fa = np.stack([Ua[0], Va[0], con.anchor_n], 1)  # anchor frame (columns)
    Up, Vp = _tangents(Nn); th = np.radians(spins); c, s = np.cos(th), np.sin(th)
    U = c[None, :, None] * Up[:, None] + s[None, :, None] * Vp[:, None]; V = -s[None, :, None] * Up[:, None] + c[None, :, None] * Vp[:, None]
    Fp = np.stack([U, V, np.broadcast_to(Nn[:, None], U.shape)], -1)                # (places, spins, 3, 3) columns
    R = Fp @ Fa.T; t = P[:, None] - np.einsum("psij,j->psi", R, con.anchor)
    return R.reshape(-1, 3, 3), t.reshape(-1, 3)


def settle(con, surf, R, t, iters=40):
    """ICP from (R, t), point to plane (it slides along smooth surfaces quickly, where point to point crawls); the
    farthest 15% are left out each step (the connector's edge where the part differs). Returns (R, t, median
    point-to-plane mm, 90% mm, share of the connector on the surface)"""
    src = con.fine; R = np.array(R, float); t = np.array(t, float)
    for _ in range(iters):
        X = src @ R.T + t; d, i = surf.tree.query(X); m = d <= max(np.quantile(d, 0.85), 1e-9)
        x, s, n = X[m], surf.S[i[m]], surf.N[i[m]]
        A = np.c_[np.cross(x, n), n]; b = -np.einsum("ij,ij->i", x - s, n)
        try: w = np.linalg.solve(A.T @ A + 1e-9 * np.eye(6), A.T @ b)
        except np.linalg.LinAlgError: break
        ang = np.linalg.norm(w[:3]); dR = _rot(w[:3], np.degrees(ang)) if ang > 1e-12 else np.eye(3)
        R, t = dR @ R, dR @ t + w[3:]
        if ang < 1e-6 and np.linalg.norm(w[3:]) < 1e-6: break
    X = src @ R.T + t; dp, de = surf.dist(X)
    return R, t, float(np.median(dp)), float(np.quantile(dp, 0.9)), float(np.mean((dp < 0.1) & (de < 0.4)))


SURE = (0.005, 0.90)   # (median mm, share on the surface): the same connector, a copy of the reference's (notes 098)
LOOK = (0.03, 0.75)    # alike (a variant of the design): placed, but to be looked at
def level(m, cov):
    return "sure" if m <= SURE[0] and cov >= SURE[1] else "look" if m <= LOOK[0] and cov >= LOOK[1] else "none"


def _result(R, t, m, q, cov, **kw):
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; lv = level(m, cov)
    return dict(M=M, match=round(m, 4), q90=round(q, 4), cover=round(cov, 3), level=lv, same=lv != "none", **kw)


ROUND = 0.02         # mm: a connector still within this of its fit when turned 30 deg (not settled) is round
def prefer_file_turn(con, surf, best, tol=0.01, near=None):
    """a round connector fits at any turn about its own axis: keep the turn closest to the part's file frame (no turn),
    or to near (a 4x4 pose: where the part's own fit puts the connector, notes 100), if it fits as well (within tol mm). Returns the result kept, with 'turned' = deg moved and 'round' = fits turned.
    Round = within ROUND mm turned 30 deg: Josh's 2nd shoulder disc (a little more than the round face) is 0.012 off
    there, and with the old 0.01 it counted as keyed, so its turn was left to the shape, which does not hold it (6 deg
    median off vs 0.4; notes 099). Keyed cuts (pad spot, wrist B, shin spot) are 0.09-0.12 off at 30 deg."""
    R, t = best["M"][:3, :3], best["M"][:3, 3]; ax = R @ con.axis; c1 = R @ con.c + t
    Rr = _rot(ax, 30.0) @ R; spun = settle(con, surf, Rr, c1 - Rr @ con.c, 0)[2]      # 30 deg turned, not settled
    rnd = getattr(con, "round", False) or spun <= best["match"] + max(tol, ROUND)
    Rn = np.eye(3) if near is None else np.asarray(near)[:3, :3]
    angs = np.arange(-180, 180, 5.0); dev = [geo.ang(_rot(ax, a) @ R @ Rn.T) for a in angs]; a = float(angs[int(np.argmin(dev))])
    fine = np.arange(a - 5, a + 5.01, 0.25); a = float(fine[int(np.argmin([geo.ang(_rot(ax, x) @ R @ Rn.T) for x in fine]))])
    # a keyed connector keeps its shape's turn when it is a copy (sure); on a variant (look) the shape holds the turn
    # only loosely (the oval waist: 10-20 deg off by noise, notes 099), so the file frame's turn is taken if it is
    # within 30 deg and fits as well. Never a flip.
    if not rnd and (best["level"] == "sure" or abs(a) > 30): return dict(best, turned=0.0, round=False)
    if abs(a) < 0.25: return dict(best, turned=0.0, round=bool(rnd))
    # the file frame's turn exactly, about the connector's own axis, not settled again (a settle lets a nearly round
    # connector drift back a few degrees: notes 099)
    R2 = _rot(ax, a) @ R; r = settle(con, surf, R2, c1 - R2 @ con.c, 0)
    # the level stays the shape's (turning a round connector is free). With near (the part's own fit) a round
    # connector always takes its turn: the swing is the pose (Intercessor bolter arms: the disc's little extra fits
    # 82 deg round from the library's swing, which holds the gun; notes 100)
    if r[2] <= best["match"] + tol or (near is not None and getattr(con, "round", False)):
        M = np.eye(4); M[:3, :3] = r[0]; M[:3, 3] = r[1]; return dict(best, M=M, turned=a, round=bool(rnd), turned_match=round(r[2], 4))
    return dict(best, turned=0.0, round=bool(rnd))


class Claim:
    """the parts of a surface other connectors already sit on (their placed points, within ~0.5 mm)"""
    H = 0.5
    def __init__(self): self.keys = np.zeros(0, np.int64)
    @staticmethod
    def _code(k): return (k[..., 0] + 4096) * 8192 * 8192 + (k[..., 1] + 4096) * 8192 + (k[..., 2] + 4096)
    def add(self, X):
        k = np.floor(np.asarray(X) / self.H).astype(np.int64); d = np.array([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)])
        self.keys = np.unique(np.r_[self.keys, self._code(k[:, None] + d[None]).reshape(-1)])
    def has(self, X):
        if not len(self.keys): return np.zeros(len(X), bool)
        return np.isin(self._code(np.floor(np.asarray(X) / self.H).astype(np.int64)), self.keys)


def placed(con, r): return con.fine @ r["M"][:3, :3].T + r["M"][:3, 3]


def find(con, surf, keep=KEEP, file_turn=True, claim=None, near=None):
    """the connector's best pose on this part: dict(M = 4x4 connector -> part, match = median mm point to plane,
    q90, cover = share of the connector on the surface, level = sure / look / none (same = not none), ambiguous =
    another place fits as well, others). claim: places other connectors already sit on are not used (a pose with
    over 30% of it there is dropped). When the first search isn't sure, a wider one (more places, finer spins) runs.
    near: a 4x4 pose (connector -> part) to prefer among equals instead of the file frame (the part's own fit)."""
    r = _find(con, surf, keep, SPIN, file_turn, claim, near=near)
    if r["level"] != "sure" or r.get("ambiguous"):
        r2 = _find(con, surf, 3 * keep, SPIN * 2 / 3, file_turn, claim, more=r.get("_out", []), near=near)
        r2["wider"] = True; r = r2
    r.pop("_out", None); return r


def _find(con, surf, keep, spin, file_turn, claim, more=(), near=None):
    P, Nn = surf.patches(CAND); spins = np.arange(0, 360, spin); X = con.coarse
    if claim is not None and len(claim.keys):
        free = ~claim.has(P); P, Nn = P[free], Nn[free]
        if not len(P): return dict(_result(np.eye(3), np.zeros(3), 9.0, 9.0, 0.0), ambiguous=False, tied=0, others=[], claimed=True)
    scores = np.empty(len(P) * len(spins), np.int32); step = max(1, 200000 // (len(spins) * len(X)))
    for a in range(0, len(P), step):
        R, t = _poses(con, P[a:a + step], Nn[a:a + step], spins)
        scores[a * len(spins):a * len(spins) + len(R)] = surf.on(np.einsum("nij,kj->nki", R, X) + t[:, None]).sum(1)
    S = scores.reshape(len(P), len(spins)); top = S.max(1); order = np.argsort(-top, kind="stable"); where = []; out = []
    for pi in order[:4000]:                                    # the best places, 0.8 mm apart
        p = P[pi]
        if any(np.linalg.norm(p - q) <= 0.8 for q in where): continue
        where.append(p); took = []
        for si in np.argsort(-S[pi], kind="stable"):            # at each place, up to 3 turns 45+ deg apart
            if S[pi, si] < 0.6 * top[pi] or len(took) == 3: break
            if any(min(abs(spins[si] - x), 360 - abs(spins[si] - x)) < 45 for x in took): continue
            took.append(spins[si]); R, t = _poses(con, p[None], Nn[pi][None], spins[[si]])
            r = _result(*settle(con, surf, R[0], t[0]), hits=int(S[pi, si]))
            if claim is None or claim.has(placed(con, r)).mean() <= 0.3: out.append(r)
        if len(where) == keep: break
    out += list(more)
    if not out: return dict(_result(np.eye(3), np.zeros(3), 9.0, 9.0, 0.0), ambiguous=False, tied=0, others=[], claimed=True)
    r = choose(con, surf, out, file_turn, near); r["_out"] = out; return r


def find_all(cons, surf, file_turn=True, near=None):
    """every connector of a part type on one part, each place used by one connector only: the connector that fits
    best (it is 'same', then the most of it on the surface, then the closest) takes its place first; the others are
    searched again away from the places taken. near: {connector name: 4x4 pose to prefer}. Returns {name: result}"""
    near = near or {}
    res = {c.name: find(c, surf, file_turn=file_turn, near=near.get(c.name)) for c in cons}; by = {c.name: c for c in cons}
    claim = Claim(); done = {}; again = set()
    def at_near(n):                       # it sits where the part's own fit / socket puts it (within 1 mm)
        N, r, c = near.get(n), res[n], by[n].c
        return N is not None and np.linalg.norm(r["M"][:3, :3] @ c + r["M"][:3, 3] - (N[:3, :3] @ c + N[:3, 3])) <= 1.0
    while len(done) < len(cons):
        # first come: a match, at its own joint (wrist A also fits the disc: on Power Fist / Intercessor arms it took
        # the disc's place and the disc landed 55-80 deg off, notes 100), most of it on the part, the closest
        def rank(n): r = res[n]; return (not r["same"], not at_near(n), -r["cover"], r["match"])
        n = min((n for n in res if n not in done), key=rank); r = res[n]
        # it sits where another one already does: searched again away from it. Not when it is at its own joint: the
        # pad spot touches the disc, and its claim (0.5 mm boxes and their neighbours) pushed the disc 59 deg round
        if n not in again and not at_near(n) and claim.has(placed(by[n], r)).mean() > 0.3:
            res[n] = find(by[n], surf, file_turn=file_turn, claim=claim, near=near.get(n)); again.add(n); continue
        done[n] = r
        if r["same"]: claim.add(placed(by[n], r))
    return done


TIE = 0.01           # mm: places / turns that fit within this of the best fit as well (at most)
TIE_MIN, TIE_REL = 0.002, 0.25   # ...and within a quarter of the best fit's own gap (at least 0.002): a 0.000 fit never
                                 # ties with a 0.009 one (left shin pads, Outrider pads: a 180 deg flip won the tie)
def tie_window(m): return min(TIE, max(TIE_MIN, TIE_REL * m))


def file_dist(con, r, near=None):
    """how far a pose is from where the connector sits on its reference part, or from near (mm, 20 deg counted as 1 mm)"""
    N = np.eye(4) if near is None else np.asarray(near); R, t = r["M"][:3, :3], r["M"][:3, 3]
    return float(np.linalg.norm(R @ con.c + t - (N[:3, :3] @ con.c + N[:3, 3]))) + geo.ang(R @ N[:3, :3].T) / 20.0


def choose(con, surf, out, file_turn=True, near=None):
    """of the settled poses, those that fit as well as the best are tied; of those, the one nearest the reference's
    own place (the maker's kit frame) is kept. 'ambiguous': another tied pose is elsewhere on the part (> 1 mm), so
    the shape alone does not say where the joint is"""
    good = [r for r in out if r["cover"] >= 0.7] or out; m = min(r["match"] for r in good)
    tied = [r for r in good if r["match"] <= m + tie_window(m)]
    best = min(tied, key=lambda r: file_dist(con, r, near)) if file_turn else min(tied, key=lambda r: r["match"])
    at = lambda r: r["M"][:3, :3] @ con.c + r["M"][:3, 3]
    amb = [r for r in tied if np.linalg.norm(at(r) - at(best)) > 1.0]
    if file_turn: best = prefer_file_turn(con, surf, best, near=near)
    best["ambiguous"] = bool(amb); best["tied"] = len(tied)
    best["others"] = [dict(match=r["match"], cover=r["cover"], at=np.round(at(r), 2).tolist()) for r in sorted(amb, key=lambda r: r["match"])[:3]]
    return best
