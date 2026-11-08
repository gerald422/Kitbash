"""Pad fix, Nov 8: (1) every arm's Pad socket in Josh's 62 convention, (2) BBoosty / CyberBrush pad fits moved off the old
'dome' sockets onto that convention.  Arm records cover main files and their variants (mirror copies)."""
import sys, os, json, math, collections, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads")
from fixseats import metrics, passes, rmin, about_J, updir3, cur_seat
from padfam import K
from respin import respin
from kb import *
LIB = "/home/claude/work/pads/before"
TOR = BY["MarFil Assault - Torso 1"]
def sidecar_path(e): return os.path.join(LIB, e["path"].replace("\\", "/")[:-4] + ".sockets.json")
def load_sc(e):
    b = open(sidecar_path(e), "rb").read(); return json.loads(b.decode("utf-8-sig"))
def records():
    out = []
    for e in P:
        if e["type"] != "Arms": continue
        V0 = T0 = None
        hs = [(None, e, np.eye(4))] + [(v["i"], v, M(v["align"])) for v in e.get("variants") or []]
        for vi, d, A in hs:
            pads = [s for s in d.get("sockets", []) if s["t"] in ("Pad R", "Pad L")]
            if not pads: continue
            side = pads[0]["t"][-1]
            if fit(d, "Shoulder " + side) is None: continue
            if V0 is None: V0, T0 = prev(e)
            S_real = sock(TOR, "Shoulder " + side) @ fit(d, "Shoulder " + side)
            V = xf(S_real @ A, V0); T = T0 if np.linalg.det(A[:3, :3]) > 0 else T0[:, ::-1]
            S = S_real
            if side == "L": V = V * [-1, 1, 1]; T = T[:, ::-1]; S = conj(S_real)
            seat = S @ (sock(d, "Pad R") if side == "R" else conj(sock(d, "Pad L")))
            u = updir3(V)
            out.append(dict(e=e, vi=vi, d=d, side=side, S_real=S_real, V=V, T=T, u=u, seat=seat, m=metrics(seat, u),
                            fam=e["maker"] + "/" + e["kit"], name=d.get("name", e["name"])))
    return out
R = records()
# corrected by Josh (Save Correction): keep
for r in R:
    sc = load_sc(r["e"]); h = sc if r["vi"] is None else sc["variants"][r["vi"]]["sidecar"]
    r["corrected"] = any((s.get("props") or {}).get("tiow_corrected") for s in h.get("sockets", []) if s["type"] == "Pad " + r["side"])
DOME = ("BBoosty", "CyberBrush")
GOOD = [r for r in R if passes(r["m"]) and r["e"]["maker"] not in DOME + ("Marta",)]
SPR = [r for r in GOOD if r["e"]["maker"] == "Springles"]
def predict(r, wide=False):
    pool = SPR if r["e"]["maker"] in DOME and not wide else GOOD
    pool = [g for g in pool if g is not r]
    best = max(pool, key=lambda g: g["u"] @ r["u"] + (0.03 if g["fam"] == r["fam"] else 0.0))
    Rm = np.eye(4); Rm[:3, :3] = rmin(best["u"], r["u"]); return about_J(Rm) @ best["seat"], best
CHANGE = []
for r in R:
    if r["corrected"]: r["why"] = "kept (Josh's correction)"; continue
    mk = r["e"]["maker"]
    if mk in DOME or mk == "Marta" or not passes(r["m"]):
        W, b = predict(r)
        if not passes(metrics(W, r["u"])):
            W2, b2 = predict(r, wide=True)
            if passes(metrics(W2, r["u"])): W, b = W2, b2
        if not passes(metrics(W, r["u"])) and abs(metrics(W, r["u"])["spin"]) > 45:
            W = respin(W, 0.0); b = dict(b, name=b["name"] + " (turned to spin 0)")
        r["new"] = W; r["ref"] = b["name"]; r["pose"] = math.degrees(math.acos(np.clip(b["u"] @ r["u"], -1, 1)))
        r["why"] = ("dome -> " if mk in DOME else "Marta -> " if mk == "Marta" else "flagged -> ") + b["name"]
        r["m_new"] = metrics(W, r["u"]); CHANGE.append(r)
def local_socket(r, W):
    Wr = W if r["side"] == "R" else conj(W)
    return np.linalg.inv(r["S_real"]) @ Wr
if __name__ == "__main__":
    c = collections.Counter(r["fam"] for r in CHANGE); n = collections.Counter(r["fam"] for r in R)
    print(len(R), "arm records;", len(CHANGE), "re-seated;", sum(r["corrected"] for r in R), "corrected kept")
    print(", ".join("%s %d/%d" % (k, c[k], n[k]) for k in sorted(n)))
    bad = [r for r in CHANGE if not passes(r["m_new"])]
    print("re-seated that still fail the check:", len(bad))
    for r in bad: print("   %-50s pose diff %5.1f  from %s  %s" % (r["name"][:50], r["pose"], r["ref"], {k: round(v) for k, v in r["m_new"].items()}))
    ang_ch = [ang(rot(r["new"]) @ rot(r["seat"]).T) for r in CHANGE]
    print("turn applied: med %.0f, p90 %.0f" % (np.median(ang_ch), np.percentile(ang_ch, 90)))
