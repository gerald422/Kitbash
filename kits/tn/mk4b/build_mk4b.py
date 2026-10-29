import sys; sys.path.insert(0,'.')
from mk4body import *
import os
from render_cross import am, fit, ARM_R, ARM_L, HELM, C_T, C_MF
D = "/mnt/user-data/uploads/new cults/Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Bodies/"
OUT = "/home/claude/kits/out112/stage_oneoff/Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Bodies/"; os.makedirs(OUT, exist_ok=True)
NOTE = {'Shoulder R': 'flat torso rule: shoulder disc, matched to the Mar Fil torso shoulder face', 'Shoulder L': 'flat torso rule: shoulder disc, matched to the Mar Fil torso shoulder face',
        'Neck': 'head where it sits on the Mar Fil torso relative to the shoulder joints (Josh, version D)', 'Back': 'flat torso rule: backpack mount face, matched to the Mar Fil torso back'}
models = []; L = lambda x: x.ravel().tolist()
for i, n in enumerate([f"Mk4_Body_{a}_{b}" for a in "ABCDE" for b in (1, 2)]):
    V, T = stlcache.load(D + n + ".stl"); S, FW, base, f = body_sockets(V, T)
    socks = [sock(n, j, S[j], NOTE[j]) for j in ('Shoulder R', 'Shoulder L', 'Neck', 'Back')]
    socks.append(sock(n, 'Base', base, 'under the feet, Z up, Y front'))
    socks += [sock(n, t, M, 'belt rule: 1 mm under the waist line (from the shoulders, as on the Mar Fil torso), Z out, Y up', 1.5) for t, M in belt_anchors(V, T, FW).items()]
    json.dump(dict(schemaVersion=1, part=n, category='Chests', fits={}, upright=flat(conv.KB @ inv(FW)), sockets=socks,
                   notes={'body': 'torso and legs in one piece: stands on its own Base, takes arms, head and pack like any torso'}), open(OUT + n + '.sockets.json', 'w'), indent=1)
    print(n, 'shoulders %.1f/%.1f back %.1f' % (f['shR'][0], f['shL'][0], f['back'][0]), 'socks', [s['type'] for s in socks])
    U = conv.KB @ inv(FW)
    items = [[stlcache.npz(D + n + ".stl"), L(U), C_T]] + [[am(rel), L(U @ S[j] @ fit(rel, j)), C_MF] for rel, j in ((ARM_R, 'Shoulder R'), (ARM_L, 'Shoulder L'), (HELM, 'Neck'))]
    models.append(dict(name=n, items=items))
json.dump({"out": "/home/claude/kits/tn/mk4b/r2", "res": 220, "pad": 1.05, "models": models, "views": {"front": [0, 1, 0.1], "side": [1, 0, 0.1]}}, open('j2.json', 'w'))
