import sys, json, time, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/real')
import fitlib as F, handrule
D = "/mnt/user-data/uploads/Desktop/tubes, pipes, chains/Toothed Glaives and Swords (1)/Final STLs/"
for rel in sys.argv[1:]:
    V, T = F.stl(D + rel); t0 = time.time()
    out = []
    for sd in ('R', 'L') if '2_Hands' in rel else ('R',):
        M, info = handrule.hand_frame(V, T, sd)
        if M is None: out.append(sd + ' NO CAP'); continue
        out.append('%s fist med %.3f caps %d r %.2f at %s Y %s Z %s' % (sd, info['med'], info['ncaps'], info['r'], M[:3, 3].round(2), M[:3, 1].round(2), M[:3, 2].round(2)))
    print(rel, '(%.0fs)' % (time.time() - t0)); [print('   ', o) for o in out]
