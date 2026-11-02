"""Classify and rule every in-scope Marta file (resumable): python job.py inscope.json results.jsonl NC_ROOT [worker k of n]"""
import sys, os, json, re, time, traceback, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mgeo as M, tiow_geom as G
inv, out, NC = sys.argv[1:4]; k, nw = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)
done = set()
if os.path.exists(out):
    for l in open(out):
        try: done.add(json.loads(l)['rel'])
        except Exception: pass
todo = [e for e in json.load(open(inv)) if not e.get('dup_of') and not e.get('bad')]
todo = [e for i, e in enumerate(sorted(todo, key=lambda e: e['rel'])) if i % nw == k and e['rel'] not in done]
ARMW = re.compile(r'arm|amrs|fist|claw|gauntlet', re.I)
WEAPW = re.compile(r'sword|axe|hammer|mace|maul|spear|glaive|halberd|knife|dagger|blade|claymore|katana|kunai|flail|whip|staf|crozius|clave|trident|anchor|hook|truncheon|shield|' +
                   r'pistol|gun|bolt|rifle|plasma|melta|flamer|shotgun|combi|volkite|carbine|revolver|blaster|crossbow|palm|hand', re.I)
GUN = re.compile(r'pistol|gun|bolt|rifle|plasma|melta|flamer|las|shotgun|combi|volkite|grav|carbine|revolver|blaster|crossbow|bow\b', re.I)
r16 = lambda m: np.asarray(m).ravel().round(6).tolist()
for e in todo:
    t0 = time.time(); r = dict(rel=e['rel'])
    try:
        V, T = M.load(os.path.join(NC, e['rel'])); name = re.sub(r'^bionic-(arms-for-shield|amrs|power-fists)-', '', os.path.basename(e['rel']).lower())
        full = os.path.basename(e['rel']).lower()
        sf = M.shoulder_faces(V, T)
        pair = [(a, b) for i, a in enumerate(sf) for b in sf[i + 1:] if a[1] @ b[1] < -0.97 and 9 < abs(a[2][0] - b[2][0]) < 15]
        if pair: r.update(kind='two-armed')
        elif 'handle' in name and ('shield' in e['rel'].lower() or 'shield' in full):
            r.update(kind='handle')
        elif 'shield' in name and 'arm' not in name and M.shield_pad(V, T) is not None:
            a, n, c = M.shield_pad(V, T); r.update(kind='shield', pad=[round(a, 1)] + np.round(c, 3).tolist() + np.round(n, 3).tolist())
        elif sf and (ARMW.search(full) or not WEAPW.search(name)):
            side, F = M.arm_fit(sf[0]); r.update(kind='arm', side=side, fit=r16(F), face=[round(sf[0][0], 1)] + np.round(sf[0][2], 3).tolist())
            big = max([f[0] for f in M.merge_flats(M.flats(V, T))] + [0])
            N, tol = (None, None) if big > 50 else M.wrist_socket(V, T, side, sf[0][2], F)   # a shield or gun built on: no free wrist
            if N is not None: r.update(hand=r16(N), tol=tol)
            else: r.update(noHand=True)
        else:
            caps = G.hand_caps(V, T); best = {}
            for s in 'RL':
                Mh, md = G.hand_wrist_frame(V, T, s, None, caps)
                if Mh is not None and md is not None:
                    ci = int(np.argmin([np.linalg.norm(np.asarray(c[0]) - Mh[:3, 3]) for c in caps]))
                    best[s] = dict(fit=r16(Mh), med=round(float(md), 3), cap=ci)
            ok = {s: b for s, b in best.items() if b['med'] <= G.FIST_LIMIT}
            if ok:
                cat = 'Pistols' if GUN.search(name) else 'Shields' if 'shield' in name else 'Hands' if re.search(r'hand|palm', name) and not re.search(r'with|sword|axe|hammer|mace|knife|flail|katana|hook|anchor', name) else 'Pistols' if GUN.search(name) else 'Melee'
                r.update(kind='held', cat=cat, sides=best)
            else:
                r.update(kind='shield' if 'shield' in name else 'handle' if 'handle' in name else 'unknown', sides=best)
    except Exception as ex:
        r.update(kind='error', err=repr(ex)[:300])
    r['sec'] = round(time.time() - t0, 1)
    with open(out, 'a') as f: f.write(json.dumps(r) + '\n')
print('done', k, nw)
