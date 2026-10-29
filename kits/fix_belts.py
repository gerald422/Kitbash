"""Post-step for every kit's sidecars: the legs' belt anchors (Hip R, Hip L, Belt Front, Belt Back) by the belt rule,
replacing the hip sockets carried over from Josh's AM legs (Z up/down inside the waist - not the frame belt bits are
fitted to and settle along). Anchors saved where a maker put a part (tiow_holds) stay; the rule fills the rest."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits')
import belt
BELT = ('Hip R', 'Hip L', 'Belt Front', 'Belt Back')
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
S_WAIST = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in P['AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl']['sockets']}['Waist']
def flat(M): return [float(x) for x in np.asarray(M).reshape(-1)]
def fix(partial, prefix=''):
    data = json.load(open(partial)); side = data['side']; n = 0
    for rel, v in side.items():
        if 'Waist' not in v.get('fits', {}): continue
        held = [s for s in v['sockets'] if s['type'] in BELT and (s.get('props') or {}).get('tiow_holds')]
        v['sockets'] = [s for s in v['sockets'] if s['type'] not in BELT] + held
        M = S_WAIST @ np.array(v['fits']['Waist']).reshape(4, 4)
        have = {s['type'] for s in held}
        for t, A in belt.belt_anchors(prefix + rel, M).items():
            if t in have: continue
            v['sockets'].append({'type': t, 'name': f"{v['part']}_socket_{t}", 'matrix': flat(A), 'display_type': 'ARROWS', 'display_size': 1.5,
                                 'props': {'tiow_from': 'belt rule: on the belt, Z out, Y up (as a clicked anchor)'}})
        n += 1
    json.dump(data, open(partial, 'w'))
    print(partial, n, 'legs')
if __name__ == '__main__':
    for pf, pre in (('/home/claude/kits/amv2_partial.json', ''), ('/home/claude/kits/vet/vet_partial.json', ''),
                    ('/home/claude/kits/iv2/iv2_partial.json', '../'), ('/home/claude/kits/cj/cj_partial.json', '')):
        fix(pf, pre)
