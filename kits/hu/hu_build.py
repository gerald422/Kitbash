"""Helmet updates (two sets, three copies each) and the BackPackUpdate-1 copies without sidecars (Outriders, library root)."""
import sys; sys.path.insert(0, '/home/claude/kits')
import json, numpy as np, os
N = json.load(open('/home/claude/kits/hu/necks.json'))
F = N['HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/1.stl']['F']        # all 21 within 0.05 deg / 0.001 mm of this
def flat(M): return [float(x) for x in np.asarray(M).reshape(-1)]
side = {}
SETS = {'HelmetsUpdates': (range(1, 11), ['All Mar All the time/HelmetsUpdate/HelmetsUpdates/HelmetsUpdates', 'All Mar All the time/Outriders (1)/Outriders/Helmets-1/HelmetsUpdates/Helmets-RawSTL', 'HelmetsUpdate/HelmetsUpdates/Helmets-RawSTL']),
        'HelmetsUpdates-1': (range(1, 12), ['All Mar All the time/HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1', 'All Mar All the time/Outriders (1)/Outriders/Helmets-2/HelmetsUpdates-1/RawSTL', 'HelmetsUpdates-1/HelmetsUpdates-1/RawSTL'])}
for s, (nums, dirs) in SETS.items():
    for d in dirs:
        for n in nums:
            side[f'{d}/{n}.stl'] = {'schemaVersion': 1, 'part': str(n), 'category': 'Heads', 'sockets': [], 'fits': {'Neck': flat(F)}}
V = json.load(open('/home/claude/kits/vet/vet_partial.json'))['side']
for k, v in V.items():
    if 'VeteranSquad/VeteranSquad/Backpacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/' in k:
        n = k.split('/')[-1]
        for d in ('All Mar All the time/Outriders (1)/Outriders/BackPacks/BackPackUpdate-1/RawSTL', 'BackPackUpdate-1/BackPackUpdate-1/RawSTL'):
            side[f'{d}/{n}'] = json.loads(json.dumps(v))
json.dump({'side': side}, open('/home/claude/kits/hu/hu_partial.json', 'w'))
print(len(side), 'sidecars (paths relative to D:\\new cults)')
