import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, glob, os
from neckfit import neck_fit
out = {}
for d in ('HelmetsUpdate/HelmetsUpdates/HelmetsUpdates', 'HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1'):
    for f in sorted(glob.glob(geo.U + d + '/*.stl'), key=lambda x: int(os.path.basename(x)[:-4])):
        rel = f[len(geo.U):]; F, md = neck_fit(rel); out[rel] = {'F': F.tolist(), 'md': md}
        print('%-30s match %.3f  fit t %s' % (d.split('/')[-1] + '/' + os.path.basename(f), md, np.round(F[:3, 3], 2)), flush=True)
json.dump(out, open('/home/claude/kits/hu/necks.json', 'w'), indent=1)
