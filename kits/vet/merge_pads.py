"""Add the Vet pad fits (vs_pads.json) to vet_partial.json."""
import json, os
p = '/home/claude/kits/vet/vet_partial.json'; side = json.load(open(p))['side']
for rel, v in json.load(open('/home/claude/kits/vet/vs_pads.json')).items():
    d = side.setdefault(rel, {'schemaVersion': 1, 'part': os.path.splitext(os.path.basename(rel))[0], 'sockets': [], 'fits': {}})
    d['fits'][v['type']] = [float(x) for row in v['fit'] for x in row]
    d['category'] = 'Knee Pads' if v['type'].startswith('Shin') else 'Shoulder Pads'
json.dump({'side': side}, open(p, 'w')); print(len(side), 'sidecars')
