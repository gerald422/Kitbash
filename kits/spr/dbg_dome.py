import sys, json, numpy as np
import hands as H, domes as D
src = open("domes.py").read().replace('    return [o for o in out if o["cover"] >= 0.85 and o["front"] < 200 and o["n"] >= 120]', '    return out').replace('if __name__ == "__main__":', 'if False:')
ns = {}; exec(compile(src, "d", "exec"), ns)
sel = json.load(open("w/sel_raw.json"))
for rel in sys.argv[1:]:
    V1, T1 = D.stlcache.load(D.U + rel); S1 = D.F.surf(V1, T1, 300000, 0)
    V0, T0 = D.stlcache.load(D.U + sel[rel]); m, Vh, Th = H.hand_mesh(V1, T1, V0, T0)
    print(rel)
    for o in ns["domes"](Vh, Th, S1):
        print("   apex", o["apex"].round(1), "a", o["a"].round(2), "cover %.2f front %d n %d" % (o["cover"], o["front"], o["n"]))
