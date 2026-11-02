"""Marta strapped shields: shield + its set's handle joined into one part (Josh left the choice to us, 1 Nov: no TIOW or
page change). Marta exports the handle turned as the shield (plate face +Z, onto the shield's back pad facing -Z), so
joining is a move: plate centre onto pad centre. The arm's wrist face glues onto the handle's side face, so the Hand
fit is that face: origin its centre, Y out of it (towards the arm), Z the shield's up (+Y) - as TIOW's hand rule reads
Marta's own shield-with-hand (Lion Knights Shield 1: same handle face, Z up the shield).
    python merge_shields.py pairs.json NC_ROOT OUT_ROOT     pairs: [[shield rel, handle rel], ...]"""
import sys, os, json, struct, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mgeo as M
def raw(f):
    d = open(f, 'rb').read(); n = struct.unpack('<I', d[80:84])[0]; return np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])).copy()
def plate(V, T):
    info = M.tri_info(V, T)
    for a, n, c in M.merge_flats(M.flats(V, T)):
        if n[2] > 0.95 and 55 < a < 85 and M.compact(V, T, n, c, info) >= 0.6: return a, n, c
def wrist_face(V, T, pc):
    """the handle's glue face for the wrist: flat 4-25 mm2, normal across the shield (|nz| < 0.6), below the plate"""
    c = [(a, n, c) for a, n, c in M.merge_flats(M.flats(V, T, 1.0)) if 4 < a < 25 and abs(n[2]) < 0.6 and c[2] < pc[2] - 0.5]
    return max(c, key=lambda f: f[0]) if c else None
def main(pairs, NC, OUT):
    done = []
    for srel, hrel in pairs:
        Vs, Ts = M.load(os.path.join(NC, srel)); Vh, Th = M.load(os.path.join(NC, hrel))
        pad = M.shield_pad(Vs, Ts); pl = plate(Vh, Th)
        if pad is None or pl is None or pad[1][2] > -0.95: print('skip (no pad/plate)', srel); continue
        t = pad[2] - pl[2]; t[2] = pad[2][2] - pl[2][2]
        wf = wrist_face(Vh, Th, pl[2])
        if wf is None: print('skip (no wrist face)', hrel); continue
        a, n, c = wf; c = c + t
        Y = n / np.linalg.norm(n); Z = np.array([0, 1.0, 0]) - Y[1] * Y; Z /= np.linalg.norm(Z)
        F = np.eye(4); F[:3, 0], F[:3, 1], F[:3, 2], F[:3, 3] = np.cross(Y, Z), Y, Z, c
        rs, rh = raw(os.path.join(NC, srel)), raw(os.path.join(NC, hrel)); rh['v'] += t.astype(np.float32)
        allt = np.concatenate([rs, rh]); rel = os.path.splitext(srel)[0] + ' with handle.stl'
        dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f: f.write(b'Marta shield + handle (Kitbash)'.ljust(80, b' ')); f.write(struct.pack('<I', len(allt))); f.write(allt.tobytes())
        fit = np.linalg.inv(F).ravel().round(6).tolist(); stem = os.path.splitext(os.path.basename(rel))[0]
        side = {'schemaVersion': 1, 'part': stem, 'category': 'Shields', 'fits': {'Hand L': fit, 'Hand R': fit},
                'notes': {'Hand L': 'the handle\'s wrist face (%.1f mm2) on the wrist, the shield\'s up along Z (as TIOW reads Marta\'s Lion Knights Shield 1)' % a,
                          'joined': 'shield %s + handle %s, handle moved %s onto the shield\'s back pad' % (srel, hrel, np.round(t, 3).tolist())}}
        json.dump(side, open(os.path.splitext(dst)[0] + '.sockets.json', 'w'), indent=1); done.append([srel, hrel, rel])
        print('joined', rel, 'move', np.round(t, 2), 'wrist face %.1f' % a)
    json.dump(done, open(os.path.join(OUT, 'joined.json'), 'w'), indent=0)
if __name__ == '__main__': main(json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3])
