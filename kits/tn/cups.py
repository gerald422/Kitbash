import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache
from belt import surf_n
from flatface import frame
from tn_torso import torso_faces, TN
from tn_sockets import sockets_for
def sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); x = np.linalg.lstsq(A, b, rcond=None)[0]; c = x[:3]; r = np.sqrt(x[3] + c @ c)
    return c, r, float(np.sqrt(np.mean((np.linalg.norm(P - c, axis=1) - r) ** 2)))
def cup_frame(rel):
    V, T = stlcache.load(TN + rel); f = torso_faces(V, T); up = f['up']; c = f['neck'][2]
    S, N = surf_n(V, T, 400000); d = S - c; h = d @ up; r = np.linalg.norm(d - h[:, None] * up, axis=1)
    k = (r < 2.5) & (h < -0.05) & (h > -3)
    cs, rs, rms = sphere(S[k])
    return frame(cs, up, f['front']), rs, rms
if __name__ == '__main__':
    REF = {"Mk2": "TurtleNinja's Mk2-6 Builder/Mk2/Torsos/Upper A 1.stl", "Mk3": "TurtleNinja's Mk2-6 Builder/Mk3/Torsos/Upper A 9.stl", "Mk4": "TurtleNinja's Mk2-6 Builder/Mk4/Torsos/Upper A 1.stl",
           "Mk6": "TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl", "Mk6A": "TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl", "Mk7": "TurtleNinja's Mk7-8 Builder/Mk7-8/Torsos/Upper A 1.stl",
           "Mk8": "TurtleNinja's Mk7-8 Builder/Mk7-8/Torsos/Mk8 Torso A 1.stl", "Mk10": "TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Torso/Mk10_Assault_Torso_Skull_Aquilla_1.stl",
           "Mk7J": "TurtleNinja's Mk7-8 Assault Intercessors Addon 1/Torsos/Mk7_Torso_Jumppack_A_9.stl"}
    out = {}
    for k, rel in REF.items():
        K, rs, rms = cup_frame(rel); S, f = sockets_for(rel)
        out[k] = (np.linalg.inv(S['Neck']) @ K).round(6).tolist()
        print(k, 'cup r %.2f rms %.3f' % (rs, rms), 'cup in neck socket frame t', np.round(out[k][0][3], 2), np.round(out[k][1][3], 2), np.round(out[k][2][3], 2))
    json.dump(out, open('/home/claude/kits/tn/cup_in_neck.json', 'w'))
