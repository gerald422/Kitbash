"""CyberBrush torso (light armour) + heads + backpacks.
Torso: comes in its own axes (front -Y); 'upright' turns it to face +Y with the shoulder faces on the Mar Fil heresy
shoulder line. Sockets copy the Mar Fil 23-Torso-2 ones, each moved by the difference between the matching features:
shoulder faces -> Shoulder R/L, neck cup -> Neck, back plate -> Back; the flat waist like Turtle Ninja's (Flat Waist on
the bottom face, Waist 4.5 above it)."""
import numpy as np, json, os, glob, sys
sys.path.insert(0, '/home/claude/blend/forclaude')
from stl_io import read_stl
from geo import *; from bbrules import *
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
NPZ = '/home/claude/kits/nc/npz/'
TORSO = 'CyberBrush__Cyberbrush_3D_Pulses_2024_11_Light_armor_Marine_torso_&_Tactical__Light armor Marine torso & Tactical Equipments__Unsupported__Torso'
V, F = load(NPZ + TORSO + '.npz'); N = vnormals(V, F)
from bbarm import all_flats
fl = all_flats(V, F, min_area=10)
dR = [d for d in fl if d['n'][0] < -0.95][0]          # file -X face = the model's right (front -Y)
dL = [d for d in fl if d['n'][0] > 0.95][0]
bottom = [d for d in fl if d['n'][2] < -0.95][0]
backp = [d for d in fl if d['n'][1] > 0.9][0]
cups = []
for votes, r, c, sup in spheres(V, F, np.arange(2.5, 4.2, 0.1), top=3, convex=False)[:4]:
    c2, r2, n2 = refine_sphere(V, c, r); cups.append((votes, c2, r2))
neck = max(cups, key=lambda x: x[0])
mid_sh = (dR['cc'] + dL['cc']) / 2
t = np.array([0, 0.2019, 31.2218]) - (RZ180[:3, :3] @ mid_sh)
U = T(t) @ RZ180                                       # file -> standing, facing +Y
w = lambda p: (U @ np.r_[p, 1])[:3]
o_R = w(dR['cc']); o_L = w(dL['cc'])
SR_cb = T(o_R - S_H[:3, 3]) @ S_R
SL_cb = T(o_L - (MX @ S_H)[:3, 3]) @ S_L
NECK_CUP_MF = np.array([0.0, 1.14, 35.22])
SN_cb = T(w(neck[1]) - NECK_CUP_MF) @ S_NECK
BACKPLATE_MF = np.array([0.0, -5.35, 33.46])
SB_cb = T(w(backp['cc']) - BACKPLATE_MF) @ S_BACK
FW_cb = T(w(bottom['cc']))                             # flat waist: the bottom face centre, Mar Fil axes
W_cb = T(w(bottom['cc']) + [0, 0, 4.508])
iU = np.linalg.inv(U)
def sock(typ, M, note):
    return dict(type=typ, name=f"Torso_socket_{typ}", matrix=R(iU @ M), display_type="ARROWS", display_size=3.0, props={"tiow_from": note})
socks = [sock("Shoulder R", SR_cb, "Mar Fil Shoulder R moved by the difference of the round shoulder faces (heresy arms' faces meet)"),
         sock("Shoulder L", SL_cb, "Mar Fil Shoulder L moved by the difference of the round shoulder faces"),
         sock("Neck", SN_cb, "Mar Fil Neck moved by the difference of the neck cups (r %.2f here, 2.67 Mar Fil)" % neck[2]),
         sock("Back", SB_cb, "Mar Fil Back moved by the difference of the back plates"),
         sock("Flat Waist", FW_cb, "the flat bottom face (r %.2f), as Turtle Ninja's flat waist" % bottom['r']),
         sock("Waist", W_cb, "4.5 above the flat waist, as Turtle Ninja's")]
side = {}
side['CyberBrush/Cyberbrush_3D_Pulses_2024_11_Light_armor_Marine_torso_&_Tactical/Light armor Marine torso & Tactical Equipments/Unsupported/Torso.stl'] = dict(
    schemaVersion=1, part="Torso", category="Chests", upright=R(U), sockets=socks, fits={},
    notes={"pose": "CyberBrush light armour torso in its own axes (front -Y); upright turns it to face +Y, shoulder faces on the Mar Fil heresy shoulder line"})
print('shoulder faces', np.round(o_R, 2), np.round(o_L, 2), 'neck cup', np.round(w(neck[1]), 2), 'r', round(neck[2], 2), 'back', np.round(w(backp['cc']), 2), 'bottom', np.round(w(bottom['cc']), 2))
# heads: neck ball in the neck cup, model axes
for f in sorted(glob.glob(NPZ + 'CyberBrush__Space Bugs Hunters__*Heads__*.npz') + glob.glob(NPZ + 'CyberBrush__Space Bugs Hunters__Broken Helmets__*.npz')):
    Vh, Fh = load(f)
    b = [o for o in balls(Vh, Fh, 1.8, 2.8, minc=0.25, k=4) if o['free'][2] < -0.8]
    if not b: print('no neck ball', f); continue
    b = min(b, key=lambda o: o['c'][2])
    Wh = T(NECK_CUP_MF) @ RZ180 @ T(-b['c'])
    rel = os.path.basename(f)[:-4].replace('__', '/') + '.stl'
    side[rel] = dict(schemaVersion=1, part=os.path.basename(rel)[:-4], category="Heads", sockets=[], fits={"Neck": R(np.linalg.inv(S_NECK) @ Wh)},
                     notes={"Neck": "CyberBrush neck ball (r %.2f) centred in the Mar Fil neck cup, the model's own axes turned 180 deg (front -Y)" % b['r']})
    print('head', os.path.basename(f)[:-4][-40:], 'ball r %.2f' % b['r'])
json.dump(side, open('/home/claude/kits/nc/cb_side_body.json', 'w'))
