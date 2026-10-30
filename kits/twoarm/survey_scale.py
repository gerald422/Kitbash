"""How big are Marta's legs, pads, knee pads and loincloths next to Mar Fil's? Previews + fits from the index."""
import json, struct, sys, numpy as np, re
from collections import defaultdict
B = sys.argv[1]
d = json.load(open(B + "/index.json"))
def V(p):
    b = open(B + "/" + p["prev"], "rb").read(); nv = struct.unpack_from("<I", b, 4)[0]
    return np.frombuffer(b, np.float32, nv * 3, 12).reshape(-1, 3).astype(float)
M4 = lambda a: np.array(a, float).reshape(4, 4)
def inframe(v, F):            # the part's points in the socket frame its fit puts it on
    return v @ F[:3, :3].T + F[:3, 3]
out = defaultdict(list)
for p in d["parts"]:
    if not p.get("prev") or p["maker"] not in ("MarFil", "Marta", "TN", "CyberBrush", "BBoosty"):
        continue
    t = p["type"]
    try:
        if t in ("Shoulder Pads", "Knee Pads"):
            k = next((x for x in p["fits"] if x.startswith(("Pad", "Shin"))), None)
            if not k: continue
            w = inframe(V(p), M4(p["fits"][k])); e = np.sort(w.max(0) - w.min(0))[::-1]
            out[(t, p["maker"])].append((e[0], e[1], e[2], p["name"]))
        elif t == "Legs":
            if re.search(r"kneel|sit|crouch|bike|ride", p["name"], re.I): continue
            s = next((x for x in p["sockets"] if x["t"] == "Base"), None)
            if s is None: continue
            S = M4(s["m"]); w = (V(p) - S[:3, 3]) @ S[:3, :3]          # points in the Base frame (z up)
            z0 = w[:, 2].min(); sole = w[w[:, 2] < z0 + 0.6][:, :2]
            if len(sole) < 20: continue
            # two feet: split along the widest direction
            c = sole - sole.mean(0); u = np.linalg.svd(c, full_matrices=False)[2][0]
            proj = c @ u; gap = np.sort(proj); dg = np.diff(gap); i = np.argmax(dg)
            feet = [sole[proj <= gap[i]], sole[proj > gap[i]]] if dg[i] > 2.0 else [sole]
            L = []
            for f in feet:
                if len(f) < 10: continue
                cf = f - f.mean(0); a = np.linalg.svd(cf, full_matrices=False)[2]
                L.append(np.ptp(cf @ a[0]))
            out[("Legs sole length", p["maker"])].append((max(L), 0, 0, p["name"]))
            # standing height of the legs: base to the top of the mesh
            out[("Legs height", p["maker"])].append((w[:, 2].max() - z0, 0, 0, p["name"]))
        elif t == "Accessories" and "Belt Front" in p["fits"]:
            w = inframe(V(p), M4(p["fits"]["Belt Front"])); e = w.max(0) - w.min(0)
            out[("Loincloth (belt frame)", p["maker"])].append((e[0], e[1], e[2], p["name"]))
    except Exception as ex:
        print("skip", p["name"], ex)
for k in sorted(out):
    a = np.array([x[:3] for x in out[k]])
    print("%-24s %-10s n=%3d  median %s   p25 %s  p75 %s" % (k[0], k[1], len(a), np.median(a, 0).round(2), np.percentile(a, 25, 0).round(2), np.percentile(a, 75, 0).round(2)))
