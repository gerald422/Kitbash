"""CyberBrush Space Bug Hunter forearms -> Forearm R fits, from Josh's Forearm 3 on 77-Arm-1-R-B.
Forearms 1 and 2 are exported like 3 (model axes, only moved): matched to 3 by their inner faces, translation only."""
import json, numpy as np
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
J = json.load(open('/home/claude/kits/nc/josh_forearm.json'))
rel = np.array(J['rel_arm'])                       # Forearm 3 file -> arm 77 file coords (Josh)
arm = json.load(open('/home/claude/test/kitlib/All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/77-Arm-1-R-B.sockets.json'))
F77 = np.array([s for s in arm['sockets'] if s['type'] == 'Forearm R'][0]['matrix']).reshape(4, 4)
T = lambda t: np.block([[np.eye(3), np.array(t, float)[:, None]], [np.zeros((1, 3)), np.ones((1, 1))]])
shift = {1: [-0.013, -0.244, 2.229], 2: [-0.05, -0.156, 2.578], 3: [0, 0, 0]}
out = {}
for k, t in shift.items():
    rel_k = f'CyberBrush/Space Bugs Hunters/Space Bug Hunters Forearms/Forearm {k}.stl'
    fit = np.linalg.inv(F77) @ rel @ T(t)
    out[rel_k] = dict(schemaVersion=1, part=f'Forearm {k}', category='Forearm Armour', sockets=[], fits={'Forearm R': R(fit)},
                      notes={'Forearm R': "Josh's Forearm 3 on 77-Arm-1-R-B (Oct 21)" + ('' if k == 3 else f"; Forearm {k} matched to 3 by its inner face (moved only)") +
                             "; lefts are mirrored onto Forearm L"})
json.dump(out, open('/home/claude/kits/nc/cb_side_forearms.json', 'w'), indent=1)
print(len(out), 'forearms')
