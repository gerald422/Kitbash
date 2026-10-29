"""Device: flat legs results -> <part>.sockets.json in a staging tree mirroring the library. usage: mk_legs_sidecars.py results.json stage_dir lib_root"""
import sys, os, json
res, stage, root = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
def flat(M): return [round(float(x), 6) for row in M for x in row]
n = 0
for p, v in res.items():
    if 'err' in v: continue
    rel = os.path.relpath(p, root); stem = os.path.splitext(os.path.basename(p))[0]
    socks = [{'type': 'Base', 'name': f'{stem}_socket_Base', 'matrix': flat(v['base']), 'display_type': 'ARROWS', 'display_size': 3.0,
              'props': {'tiow_from': 'flat-legs rule: under the feet, Z up, Y front'}}]
    for t, M in v['belt'].items():
        socks.append({'type': t, 'name': f'{stem}_socket_{t}', 'matrix': flat(M), 'display_type': 'ARROWS', 'display_size': 1.5,
                      'props': {'tiow_from': 'belt rule (flat legs): on the belt 1 mm under the top, Z out, Y up (as a clicked anchor)'}})
    sc = {'schemaVersion': 1, 'part': stem, 'category': 'Legs', 'sockets': socks, 'fits': {'Flat Waist': flat(v['fit'])},
          'notes': {'Flat Waist': 'top face: origin at its centre, Z out of it, Y the front of the legs (TIOW Inbox 1.12)'}}
    dst = os.path.join(stage, os.path.splitext(rel)[0] + '.sockets.json')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    json.dump(sc, open(dst, 'w'), indent=1); n += 1
print('staged', n)
