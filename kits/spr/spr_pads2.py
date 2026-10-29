"""Pad anchors for Springles arms: reference = Josh's 62-on-76 anchor (torso pose) on the hanging 'slung arm', pushed out
to clear its shoulder armour; every other arm = that anchor turned by the arm's shoulder swing (capmatch), pushed out again."""
import sys, json, numpy as np
import capmatch as CM, spr_pads as SP
from spr_arms import S_R, S_L, S_H
REF = "patternC arms/unique/patternC slung arm.stl"
MX = np.diag([-1.0, 1, 1, 1])
_ref = None
def ref():
    global _ref
    if _ref is None:
        side, W, P = CM.torso_pts(REF, 250000)
        Pp, Pn = normals_for(REF)
        M = SP.PAD76.copy(); d = dirv(M)
        t = SP.push_out(Pp, Pn, M, d); M[:3, 3] += t * d
        _ref = (CM.shoulder(P), M, t)
    return _ref
def dirv(M):
    cen = M[:3, :3] @ (SP.F62[:3, :3] @ SP._pad_center()) + M[:3, :3] @ SP.F62[:3, 3] + M[:3, 3]
    v = cen - S_H[:3, 3]; return v / np.linalg.norm(v)
def normals_for(rel):
    s = json.load(open(SP.ST + rel[:-4] + ".sockets.json")); side = list(s["fits"])[0][-1]
    W = (S_R if side == "R" else S_L) @ np.array(s["fits"]["Shoulder " + side]).reshape(4, 4)
    V, T = SP.stlcache.load(SP.U + rel); P, Pn = SP.arm_points_normals(np.asarray(V, float) * s["scale"], T, W)
    if side == "L": P = P * [-1, 1, 1]; Pn = Pn * [-1, 1, 1]
    return P, Pn
def anchor(rel):
    SR, Mref, tref = ref()
    side, W, P = CM.torso_pts(rel)
    th, med = CM.match(SR, CM.shoulder(P))
    R3, med3 = CM.match3(SR, CM.shoulder(P), th)
    if med3 > 0.15:                                    # raised sideways etc: search every rotation
        Ra, ma = CM.match_any(SR, CM.shoulder(P))
        if ma < med3: R3, med3 = Ra, ma
    R = np.eye(4); R[:3, :3] = R3; R[:3, 3] = CM.D0 - R3 @ CM.D0
    tilt = float(np.degrees(np.arccos(np.clip(R3[:, 0] @ CM.rot(np.radians(th))[:, 0], -1, 1))))
    M = R @ Mref
    Pp, Pn = normals_for(rel); d = dirv(M)
    t = SP.push_out(Pp, Pn, M, d); M[:3, 3] += t * d
    if side == "L": M = MX @ M @ MX
    return side, np.linalg.inv(W) @ M, M, dict(swing=th, match=med, match3=med3, tilt=tilt, push=t)
if __name__ == "__main__":
    print("ref push", ref()[2])
    for rel in sys.argv[1:]:
        side, Mp, Mt, info = anchor(rel); print(rel.split("/")[-1], side, {k: round(v, 2) for k, v in info.items()})
