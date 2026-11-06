"""Marta two-armed sets at 90%: the facing pair of shoulder faces (as job.py flags them); the right arm's face (normal +X)
on Shoulder R by the one-handed arm rule (mgeo.arm_fit, Q from Mar Fil Torso 1's shoulder faces); the left arm follows."""
import sys, json, re, numpy as np
sys.path.insert(0, '/home/claude/work/m2h'); import mgeo as M
NC = '/mnt/user-data/uploads/d/new cults/'
L = [l.strip() for l in open('/mnt/user-data/uploads/d/Kitbash Library/_backups/marta-2h-2026-11-06/files.txt') if l.strip()]
GUN = re.compile(r'pistol|gun|bolt|rifle|plasma|melta|flamer|las|shotgun|combi|volkite|grav|carbine|launcher|cannon|bfg|weapon', re.I)
MEL = re.compile(r'sword|axe|hammer|mace|maul|spear|glaive|halberd|naginata|katana|staff|staf|chain|fist|claw|banner|handle|blade', re.I)
out = {}
for rel in L:
    V, T = M.load(NC + rel); sf = M.shoulder_faces(V, T); n = rel.rsplit('/', 1)[-1][:-4]
    pair = [(a, b) for i, a in enumerate(sf) for b in sf[i + 1:] if a[1] @ b[1] < -0.97 and 9 < abs(a[2][0] - b[2][0]) < 15]
    if not pair: out[rel] = {'ok': False, 'faces': len(sf)}; print('NO PAIR (%d faces) %s' % (len(sf), rel[6:100])); continue
    a, b = max(pair, key=lambda p: p[0][0] + p[1][0]); R_, L_ = (a, b) if a[1][0] > 0 else (b, a)
    side, F = M.arm_fit(R_); d = np.linalg.norm(np.array(R_[2]) - np.array(L_[2]))
    cat = 'Two-Handed Melee' if MEL.search(n) and not GUN.search(n) else 'Two-Handed Guns'
    out[rel] = {'ok': True, 'side': side, 'fit': np.asarray(F).tolist(), 'cat': cat, 'faces': [round(float(R_[0]), 1), round(float(L_[0]), 1)], 'apart': round(float(d) * 0.9, 2)}
    print('%-16s %s faces %5.1f / %5.1f mm2, %5.2f mm apart at 90%% | %s' % (cat, side, R_[0], L_[0], d * 0.9, rel[6:100]))
json.dump(out, open('results.json', 'w'), indent=0)
