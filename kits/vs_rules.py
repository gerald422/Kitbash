import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, os, json, glob, time, wristrule as W, handrule
B = '/home/claude/raw/VeteranSquad/VeteranSquad/'
out = {'arms': {}, 'hands': {}}
for f in sorted(glob.glob(B + 'Arms/*/*.stl')):
    rel = f.replace('/home/claude/raw/', ''); sd = 'L' if 'Mirrored' in rel else 'R'
    V, T = geo.load(rel); joint = np.array([5.48 * (1 if sd == 'R' else -1), 0.2, 31.95])
    t = time.time(); M = W.wrist_frame2(V, T, joint, sd)
    out['arms'][rel] = dict(M=M.tolist(), side=sd)
    print('%-40s %s origin %s Y %s Z %s (%.1fs)' % (os.path.basename(rel), sd, M[:3, 3].round(2), M[:3, 1].round(2), M[:3, 2].round(2), time.time() - t))
for f in sorted(glob.glob(B + 'Melee/*/*.stl')):
    rel = f.replace('/home/claude/raw/', ''); sd = 'L' if 'Mirrored' in rel else 'R'
    if 'PowerFist' in rel: continue
    V, T = geo.load(rel); t = time.time()
    M, info = handrule.hand_frame(V, T, sd)
    if M is None: print(os.path.basename(rel), 'NO CAP'); continue
    out['hands'][rel] = dict(M=M.tolist(), side=sd, **info)
    print('%-40s %s fist med %.3f caps %d r %.2f origin %s Y %s (%.1fs)' % (os.path.basename(rel), sd, info['med'], info['ncaps'], info['r'], M[:3, 3].round(2), M[:3, 1].round(2), time.time() - t))
json.dump(out, open('/home/claude/kits/vs_rules.json', 'w'))
