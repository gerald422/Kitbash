"""Sidecars: Turtle Ninja flat torsos (54) and the six body adaptors."""
import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, os
import conv, flatface as FF
from tn_sockets import sockets_for
OUT = '/home/claude/kits/out112/stage/'
def ortho(M):
    M = np.array(M, float); U_, _, Vt = np.linalg.svd(M[:3, :3]); M[:3, :3] = U_ @ Vt; return M
def flat(M): return [round(float(x), 6) for x in ortho(M).reshape(-1)]
def sock(stem, t, M, note, size=3.0):
    return {'type': t, 'name': f'{stem}_socket_{t}', 'matrix': flat(M), 'display_type': 'ARROWS', 'display_size': size, 'props': {'tiow_from': note}}
def write(rel, sc):
    p = OUT + os.path.splitext(rel)[0] + '.sockets.json'; os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(sc, open(p, 'w'), indent=1)
NOTES = {'Shoulder R': 'flat torso rule: shoulder disc, matched to the Mar Fil torso shoulder face',
         'Shoulder L': 'flat torso rule: shoulder disc, matched to the Mar Fil torso shoulder face',
         'Neck': 'head where it sits on the Mar Fil torso relative to the shoulder joints (Josh, version D)',
         'Back': 'flat torso rule: backpack mount face, matched to the Mar Fil torso back',
         'Waist': 'on Mar Fil legs: flat bottom on top of the belt (front belt line, 24.8)',
         'Flat Waist': 'flat bottom: origin at its centre, Z up into the torso, Y front'}
n = 0
for rel in json.load(open('/home/claude/kits/tn/flat_torsos.json')):
    S, f = sockets_for(rel); stem = os.path.splitext(os.path.basename(rel))[0]
    up = conv.KB @ np.linalg.inv(S['Flat Waist'])          # file -> Mar Fil kit frame (as if on Mar Fil legs)
    write('Turtle Ninja/' + rel, {'schemaVersion': 1, 'part': stem, 'category': 'Chests', 'fits': {}, 'upright': flat(up),
                                  'sockets': [sock(stem, t, S[t], NOTES[t]) for t in ('Shoulder R', 'Shoulder L', 'Neck', 'Back', 'Waist', 'Flat Waist')],
                                  'notes': {'pose': 'the flat pose of this torso design (Josh: one pose per torso, the flat one)'}})
    n += 1
AD = json.load(open('/home/claude/kits/cr/ad_frames.json')); M_AD = np.array(AD['M_ad'])
S_AD_FLAT = FF.frame([3.587, AD['ring_y'], 4.135], [0, -1, 0], [0, 0, -1])
F_W = np.linalg.inv(conv.S_AM['Waist']) @ M_AD
for i in range(1, 7):
    stem = f'lower_body_(torso)_{i}'
    write(f'body adaptor/{stem}.stl', {'schemaVersion': 1, 'part': stem, 'category': 'Adapters', 'fits': {'Waist': flat(F_W)},
                                       'sockets': [sock(stem, 'Flat Waist', S_AD_FLAT, 'flat ring under the stomach plating: Z up, Y front; flat-topped legs stand here')],
                                       'notes': {'Waist': 'the top is a copy of the Mar Fil legs waist (plug + plating, 0.1 mm): seated like Josh’s 29-Legs-2'}})
    n += 1
print('sidecars', n)
