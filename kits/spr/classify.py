"""Pick the Springles hands by their known poses: every two-hand gun has the same two hands in the same places
(grip wrist along -X, the other 10.9 / 3.9 / 0.9 mm from it along +X/+Y/+Z); pistols the grip hand; axes their own."""
import json, numpy as np
GRIP = np.array([-1.0, 0, 0.08]); FORE = np.array([-0.2, 0.91, 0.37]); AXE = np.array([-0.08, -1.0, 0.04])
OFF = np.array([10.9, 3.9, 0.9])
PIST = ("pistol", "revolver", "hand flamer", "serpenta")
def u(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def kind(rel):
    b = rel.split("/")[-1].lower()
    if rel.startswith("heavy weapons/") or rel.startswith("assault cannon/"): return "heavy"
    if any(p in b for p in PIST): return "pistol"
    if "axe" in b or "tabar v" in b: return "axe"
    if "tabar pose" in b: return "tabar2"
    return "gun"
def pick(rel, ds):
    k = kind(rel)
    ds = [dict(d, apex=np.array(d["apex"], float), a=u(d["a"])) for d in ds]
    if k == "pistol":
        g = [d for d in ds if d["a"] @ u(GRIP) > 0.97]; return (max(g, key=lambda d: d["n"]), None) if g else (None, None)
    if k == "axe":            # posed variants tilt the wrist up to ~20 deg
        g = [d for d in ds if d["a"][1] < -0.85]; return (max(g, key=lambda d: d["n"]), None) if g else (None, None)
    if k == "gun":
        gs = [d for d in ds if d["a"] @ u(GRIP) > 0.97]; fs = [d for d in ds if d["a"] @ u(FORE) > 0.95]
        best = None
        for g in gs:
            for f in fs:
                e = np.linalg.norm(f["apex"] - g["apex"] - OFF)
                if e < 1.0 and (best is None or e < best[0]): best = (e, g, f)
        return (best[1], best[2]) if best else (None, None)
    if k == "tabar2":          # both hands on the haft: the lower one is the right (rear) hand
        ds2 = [d for d in ds if d["n"] >= 200]
        if len(ds2) < 2: return None, None
        s = sorted(ds2, key=lambda d: d["apex"][2]); return s[0], s[1]
    if k == "heavy":
        SH = u([0.25, -0.83, -0.49])                  # shoulder-carried (las cannon, plasma cannon, rocket launcher)
        sh = [d for d in ds if d["a"] @ SH > 0.97]
        if sh:
            o = sh[0]; g = [d for d in ds if d["a"][0] < -0.8 and 7 < np.linalg.norm(d["apex"] - o["apex"]) < 13]
            return (max(g, key=lambda d: d["n"]), o) if g else (None, None)
        HIP = u([-0.49, -0.72, 0.49])                 # hip-held: the angled hand is the trigger hand
        gs = [d for d in ds if d["a"] @ HIP > 0.97]; os_ = [d for d in ds if d["a"][0] < -0.95]
        best = None
        for g in gs:
            for o in os_:
                e = abs(np.linalg.norm(o["apex"] - g["apex"]) - 12.6)
                if e < 1.0 and (best is None or e < best[0]): best = (e, g, o)
        return (best[1], best[2]) if best else (None, None)
    return None, None
if __name__ == "__main__":
    H = json.load(open("w/hands_all.json"))
    bad = []
    for rel, h in sorted(H.items()):
        g, f = pick(rel, h["domes"]); k = kind(rel)
        if g is None or (k == "gun" and f is None): bad.append(rel)
    bad = [b for b in bad if "bolt cannon" not in b and "bolter slung" not in b]
    print(len(bad), bad); json.dump(bad, open("w/redo.json", "w"))
