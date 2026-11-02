"""Turn job.py's results into sidecars beside the Marta sources in D:\\new cults (the set-up parts plan_library.py reads).
Never overwrites an existing sidecar. python write_sidecars.py results.jsonl NC_ROOT [--dry]"""
import sys, os, json, numpy as np
res, NC = sys.argv[1:3]; DRY = '--dry' in sys.argv
LIMIT = 0.3                                   # TIOW's FIST_LIMIT
inv16 = lambda m: np.linalg.inv(np.array(m).reshape(4, 4)).ravel().round(6).tolist()
made, skipped = [], []
rows = json.load(open(res)) if res.endswith('.json') else [json.loads(l) for l in open(res)]
for r in rows:
    rel = r['rel']; stem = os.path.splitext(os.path.basename(rel))[0]
    d = {'schemaVersion': 1, 'part': stem}
    if r['kind'] == 'arm':
        s = r['side']; d.update(category='Arms', scale=0.9, fits={'Shoulder ' + s: r['fit']},
            notes={'Shoulder ' + s: 'Marta single arm: shoulder face (%.1f mm2) on the socket, face flat on the chest, her Y up kept; 90%% as her two-armed sets (Josh, 30 Oct)' % r['face'][0]})
        if r.get('hand'):
            d['sockets'] = [{'type': 'Hand ' + s, 'name': stem + '_socket_Hand ' + s, 'matrix': r['hand'], 'display_type': 'ARROWS', 'display_size': 3.0,
                             'props': {'tiow_from': 'Marta wrist: TIOW wrist face (round_tol %s), roll = torso up+forward (as Springles; TIOW armour roll scatters on Marta arms)' % r['tol']}}]
        else: d['noHand'] = True
    elif r['kind'] == 'held':
        ok = {s: b for s, b in r['sides'].items() if b['med'] <= LIMIT}
        best = min(ok, key=lambda s: ok[s]['med'])
        keep = {s: b for s, b in ok.items() if b['cap'] == ok[best]['cap']}      # the other hand only if the rule finds the same wrist
        d.update(category=r['cat'], fits={'Hand ' + s: inv16(b['fit']) for s, b in keep.items()}, ruled={'Hand ' + s: 'wrist-1' for s in keep},
                 notes={'Hand ' + s: 'TIOW hand rule (reference fist %.3f)' % b['med'] for s, b in keep.items()})
        if len(keep) < len(ok): d['notes']['side'] = 'only %s: the other hand\'s best wrist was a different stump' % best
    else:
        skipped.append((r['kind'], rel)); continue
    p = os.path.join(NC, os.path.splitext(rel)[0] + '.sockets.json')
    if os.path.exists(p): skipped.append(('exists', rel)); continue
    if not DRY: json.dump(d, open(p, 'w'), indent=1)
    made.append(rel)
print('sidecars', len(made), 'skipped', len(skipped))
import collections; print(collections.Counter(k for k, _ in skipped))
json.dump({'made': made, 'skipped': skipped}, open(os.path.join(os.path.dirname(res), 'written.json'), 'w'), indent=0)
