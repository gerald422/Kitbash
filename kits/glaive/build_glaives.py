"""Toothed chainswords and chainglaives (Josh's default chain weapons): the hand versions only.
Hand R fit by the hand rule (Mar Fil's fist matched onto each hand, wrist cap frame). One-handed ones get a
mirrored left-hand copy as a variant; the two-handed glaives are Two-Handed Held: the upper hand (blade side)
in Hand R, the lower hand's wrist as offHand, turning about the right wrist (pivot) to meet the left arm."""
import sys, os, json, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/real')
import fitlib as F, handrule, wristrule
D = "/mnt/user-data/uploads/Desktop/tubes, pipes, chains/Toothed Glaives and Swords (1)/Final STLs/Merged/"
LIBDIR = "Bits\\Toothed Chain Weapons\\"
MX = np.diag([-1.0, 1, 1, 1])
R6 = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
orig_caps = wristrule.stub_caps
def frame_on(V, T, cap, side):
    handrule.W.stub_caps = lambda V_, T_: [cap]
    try: return handrule.hand_frame(V, T, side)
    finally: handrule.W.stub_caps = orig_caps
out, report = {}, []
for kind, folder, pat, n in (("sword", "Chainsword", "Right_Hand_%03d", 12), ("glaive", "Chainglaives", "1_Hand_%03d", 12), ("glaive2", "Chainglaives", "2_Hands_%03d", 12)):
    for i in range(1, n + 1):
        src = folder + "/" + (pat % i) + ".stl"; V, T = F.stl(D + src)
        if kind != "glaive2":
            M, info = handrule.hand_frame(V, T, 'R')
            name = ("Bits Toothed - Chainsword %02d" if kind == "sword" else "Bits Toothed - Chainglaive %02d") % i
            sub = "Chainswords" if kind == "sword" else "Chainglaives"
            fit = np.linalg.inv(M)
            sc = {"schemaVersion": 1, "part": pat % i, "category": "Melee", "sockets": [], "fits": {"Hand R": R6(fit)},
                  "notes": {"Hand R": "hand rule: Mar Fil's fist matched onto the hand (median %.3f mm), wrist cap frame" % info["med"]},
                  "variants": [{"side": "L", "mirror": True, "align": R6(MX), "name": name + " L", "title": name + " (left hand)",
                                "from": "mirror of the right-hand file", "sidecar": {"category": "Melee", "sockets": [], "fits": {"Hand L": R6(MX @ fit @ MX)}}}],
                  "original": {"name": pat % i, "folder": folder, "path": "Desktop\\tubes, pipes, chains\\Toothed Glaives and Swords (1)\\Final STLs\\Merged\\" + folder + "\\" + (pat % i) + ".stl"}}
            report.append("%-40s fist %.3f mm" % (name, info["med"]))
        else:
            caps = wristrule.stub_caps(V, T); fr = []
            for c in caps:
                for sd in ("R", "L"):
                    M, info = frame_on(V, T, c, sd)
                    if M is not None: fr.append((info["med"], sd, M, c[1]))
            # two hands: the blade end is where the mesh is (PCA long axis signed toward the vertex mean, away from the
            # hands, as the BBoosty two-handers); the upper hand (nearer the blade) is the right hand, as in the
            # one-handed glaives, the lower one the left
            good = {}
            for f in fr:
                k = tuple(np.round(f[3], 3)); good.setdefault(k, []).append(f)
            cs = sorted(good, key=lambda k: min(x[0] for x in good[k]))[:2]
            w_, U_ = np.linalg.eigh(np.cov((V - V.mean(0)).T)); L = U_[:, -1]
            mid = (np.array(cs[0]) + np.array(cs[1])) / 2
            if (V.mean(0) - mid) @ L < 0: L = -L
            upc, loc = sorted(cs, key=lambda k: -(np.array(k) @ L))
            a = next(x for x in good[upc] if x[1] == "R"); b = next(x for x in good[loc] if x[1] == "L")
            assert a[2][:3, 2] @ L > 0, "right fist upside down"
            name = "Bits Toothed - Chainglaive Two Hands %02d" % i; sub = "Chainglaives Two Hands"
            MR, ML = a[2], b[2]
            sc = {"schemaVersion": 1, "part": pat % i, "category": "Two-Handed Held", "sockets": [], "fits": {"Hand R": R6(np.linalg.inv(MR))},
                  "offHand": R6(ML), "pivot": [round(float(x), 6) for x in MR[:3, 3]],
                  "notes": {"Hand R": "the upper hand (blade side) by the hand rule (fist %.3f mm)" % a[0],
                            "offHand": "the lower hand's wrist (left fist %.3f mm, %.1f mm down the shaft): the glaive turns about the right wrist to bring it to the left wrist" % (b[0], np.linalg.norm(a[3] - b[3]))},
                  "original": {"name": pat % i, "folder": folder, "path": "Desktop\\tubes, pipes, chains\\Toothed Glaives and Swords (1)\\Final STLs\\Merged\\" + folder + "\\" + (pat % i) + ".stl"}}
            report.append("%-40s right %.3f  left %.3f  hands %.1f mm apart (%d caps)" % (name, a[0], b[0], np.linalg.norm(a[3] - b[3]), len(caps)))
        out[src] = {"rel": LIBDIR + sub + "\\" + name + ".stl", "sidecar": sc}
json.dump(out, open("glaives.json", "w"), indent=1)
print("\n".join(report))
