"""Redwarden Prime Techmarine torso (flat bottom): sockets by the flat torso rule (kits/cr/conv.py, as Turtle Ninja's
torsos): shoulder discs, back face and bottom face -> Mar Fil sockets via the AM torso's face->socket offsets, Neck by
rule D. File: Z up, front -Y (back face normal +Y), so `upright` turns it 180 deg to face +Y like Mar Fil's."""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/rw_spr"); from common import *
import flats, conv
from flatface import frame
REL = RW + "Torso/Prime Techmarine torso (Flat Bottom).stl"
def sockets():
    V, T = load(REL); Fl = flats.flats(V, T, min_area=1.0)
    up = np.array([0, 0, 1.0]); front = np.array([0, -1.0, 0])
    bot = max([f for f in Fl if f[1] @ -up > 0.98], key=lambda f: f[0])
    back = max([f for f in Fl if f[1] @ -front > 0.98 and f[2][2] > 10], key=lambda f: f[0])
    right = np.cross(front, up)
    shR = max([f for f in Fl if f[1] @ right > 0.95], key=lambda f: f[0]); shL = max([f for f in Fl if f[1] @ -right > 0.95], key=lambda f: f[0])
    face = {"Bottom": frame(bot[2], up, front), "Shoulder R": frame(shR[2], shR[1], up), "Shoulder L": frame(shL[2], shL[1], up),
            "Back": frame(back[2], back[1], up)}
    S = conv.torso_sockets(face)
    # Neck: rule D's turn (21.6 deg forward, as on the AM torso) at the floor of Redwarden's own neck cup: the cup is a
    # 4.1 mm-radius well (rim z 18.1) centred 1.4 mm in front of rule D's point; its floor (median z 14.67) is within
    # 0.2 mm of rule D's height.
    # Raised 1.2 mm along its Z: on the floor itself every helmet (Redwarden's 8, Springles mk5 / alt, all on Josh's AM
    # helmet seat) cut 1.05-1.49 mm into the cup's front; at +1.2 they cut 0.09-0.47 mm and still touch (0.00-0.04 mm).
    S["Neck"] = S["Neck"].copy(); S["Neck"][:3, 3] = np.array([0.006, -1.362, 14.67]) + 1.2 * S["Neck"][:3, 2]
    note = "flat torso rule (kits/cr/conv.py): bottom face z %.2f, shoulder discs x %.2f/%.2f, back face y %.2f; Neck rule D turned, 1.2 mm above the neck cup's floor" % (bot[2][2], shR[2][0], shL[2][0], back[2][1])
    return S, note
if __name__ == "__main__":
    S, note = sockets(); print(note)
    for k, M in S.items(): print("%-11s o %s  Z %s  Y %s" % (k, M[:3, 3].round(2), M[:3, 2].round(2), M[:3, 1].round(2)))
