"""Springles arm wrist cups: the far end of the forearm is a dish. Find it: farthest region from the shoulder joint,
fit the dish (sphere) and its rim circle."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
U = "/mnt/user-data/uploads/new cults/Springles/"
AF = json.load(open("arm_fits.json"))
def sphere_fit(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); s = np.linalg.lstsq(A, b, rcond=None)[0]
    c = s[:3]; r = np.sqrt(s[3] + c @ c); return c, r, np.abs(np.linalg.norm(P - c, axis=1) - r)
def analyse(rel, verbose=False):
    a = AF[rel]; k = a["scale"]; V, T = stlcache.load(U + rel); V = V * k
    Fm = np.array(a["fit"]); j = np.linalg.inv(Fm)[:3, 3]
    S = F.surf(V, T, 200000, 0); N = None
    d = np.linalg.norm(S - j, axis=1); far = S[np.argmax(d)]
    # forearm end axis: PCA of points within 6 mm of the far point
    P = S[np.linalg.norm(S - far, axis=1) < 6]; c0 = P.mean(0)
    w, v = np.linalg.eigh(np.cov((P - c0).T)); ax = v[:, 2]
    if (far - c0) @ ax < 0: ax = -ax       # pointing out of the arm
    # end plane: max projection along ax; take points within 1.2 mm of the end
    h = (S - far) @ ax
    return far, ax, j
if __name__ == "__main__":
    for rel in ["patternC arms/tactical arms/patternC ranged Rarm 1.stl", "patternC arms/melee arms/patternC melee Rarm 3.stl"]:
        a = AF[rel]; k = a["scale"]; V, T = stlcache.load(U + rel); V = V * k
        S = F.surf(V, T, 300000, 0)
        Fm = np.array(a["fit"]); j = np.linalg.inv(Fm)[:3, 3]
        d = np.linalg.norm(S - j, axis=1); far = S[np.argmax(d)]
        P = S[np.linalg.norm(S - far, axis=1) < 5]
        c0 = P.mean(0); w, v = np.linalg.eigh(np.cov((P - c0).T))
        print(rel, "far", far.round(2), "eig", w.round(2))
        # radial profile along each candidate axis: use the axis from joint->far as a guess, then refine by cylinder symmetry
        ax = (far - j) / np.linalg.norm(far - j)
        for it in range(3):
            h = (S - far) @ ax; Q = S[(h > -4)]
            # centre line: mean of slices
            cs = []
            for z in np.arange(-4, 0.01, 0.5):
                q = Q[np.abs(((Q - far) @ ax) - z) < 0.25]
                if len(q) > 30: cs.append(q.mean(0))
            cs = np.array(cs); u, s_, vt = np.linalg.svd(cs - cs.mean(0)); ax2 = vt[0] * np.sign(vt[0] @ ax); ax = ax2
        h = (S - far) @ ax
        top = h.max(); print(" axis", ax.round(3), "end h", round(top, 3))
        cen = cs.mean(0)
        for z in np.arange(top - 3.0, top + 0.01, 0.2):
            q = S[np.abs(h - z) < 0.06]
            if len(q) < 5: continue
            lat = q - cen; lat = lat - np.outer(lat @ ax, ax); r = np.linalg.norm(lat, axis=1)
            print("   h %6.2f n %4d r min %.2f med %.2f max %.2f" % (z - top, len(q), r.min(), np.median(r), r.max()))
