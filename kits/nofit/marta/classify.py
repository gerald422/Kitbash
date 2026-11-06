"""File every Marta weapon/arm the rules couldn't fit under its category, with no fit and a note (Josh, Nov 6: parts
without a fit are kept and logged). Writes plan.json (rel -> category, scale, note); --write writes the sidecars beside
the sources in D:\\new cults (never over an existing one)."""
import json, os, csv, re, glob, sys, collections
H = os.path.expanduser('~/mnt/d/'); NC = H + 'new cults/'; B = H + 'Kitbash Library/_backups/marta-1h-2026-11-01/'
OUT = H + 'Kitbash Library/_backups/marta-nofit-2026-11-06/'
src = set(r[1].replace('\\', '/').lower() for r in list(csv.reader(open(H + 'Kitbash Library/_sources.csv', encoding='utf-8-sig')))[1:])
R = [json.loads(l) for l in open(B + 'results.jsonl', encoding='utf-8') if l.strip()]
cands = [(r['rel'], r['kind']) for r in R if r['rel'].lower() not in src and r['kind'] != 'two-armed']
X = ['Marta/10 Oct 2025-20251031T164458Z-1-001 (1)/10 Oct 2025/heavy ARMS-WEAPONS-effects/heavy_arm_[123].stl',
     'Marta/d2420251125-1-bd6hiy/marta_PunkGirl/d24/D24_1/EXECUTIONS 4/blood effect/R_arm_blood_effect.stl',
     'Marta/Marta_Captain with Relic Shield/Captain with Relic Shield/set_arms_[13].[12].stl', 'Marta/Marta_Captain with Relic Shield/Captain with Relic Shield/2h_handle_[123].stl',
     'Marta/Marta GURLS/04.23 DA Lion Knights/weapons without hands/*.stl', 'Marta/Marta GURLS/04.23 DA Lion Knights/shoulder shields/lion_shield.stl',
     'Marta/Marta GURLS/Hooded models/weapons/weapons with no arms/DA_swordd.stl', 'Marta/Marta GURLS/Hooded models/arms/*2h*.stl',
     'Marta/Marta GURLS/06.23 Greek Themed Gurls/2h-*.stl', 'Marta/Marta_Techmarine V2/02 Feb 2025-20250228T123625Z-001 (1)/02 Feb 2025/character 2/2h_handle.stl',
     'Marta/07 July 2025-20250731T104415Z-1-001/07 July 2025/character 3/2h_handle.stl', 'Marta/Marta_Techmarine/Techmarine/servo arm.stl',
     'Marta/Marta_Techmarine V2/Techmarine V2/Iron_father_servo_*.stl', 'Marta/52 June 2026-20260618T122425Z-3-001/52 June 2026/bike/set_arms_1_*for_bike.stl',
     'Marta/52 June 2026-20260618T122425Z-3-001/52 June 2026/bike/palm_withs_chain.stl']
for g in X: cands += [(os.path.relpath(f, NC).replace('\\', '/'), 'extra') for f in sorted(glob.glob(NC + g))]
seen = set(); plan = {}; skip = collections.Counter(); skipped = []
ARM = re.compile(r'(^|[^a-z])(arm|arms|amrs)([^a-z]|$)|fist|clow|claws_l', re.I)
for rel, kind in cands:
    if rel.lower() in seen or rel.lower() in src: continue
    seen.add(rel.lower()); n = rel.rsplit('/', 1)[-1][:-4]; low = n.lower(); d = os.path.dirname(rel)
    def S(why): skip[why] += 1; skipped.append((why, rel))
    if os.path.exists(NC + rel[:-4] + '.sockets.json'): S('already has a sidecar'); continue
    if re.search(r'pres_|presup|zsup', low): S('presupported copy'); continue
    if re.search(r'armor_part|armor plates|armour', low): S('armour plate (not a weapon or arm)'); continue
    if kind in ('shield', 'handle') and 'shield' in low and 'handle' not in low and os.path.exists(NC + rel[:-4] + ' with handle.stl'):
        S('shield already in as "with handle"'); continue
    if kind == 'handle' and 'shield' in low:
        sh = [f for f in glob.glob(NC + d + '/*with handle.stl')]
        if sh: S('shield handle, its shield already in as "with handle"'); continue
        cat, sc, why = 'Shields', 1.0, 'shield handle; its shield is filed loose (handle not matched to it) - join or place by eye'
    elif 'back_pack' in low: cat, sc, why = 'Backpacks', 1.0, 'pack with a bolter built in; no Back fit yet'
    elif 'servo' in low: cat, sc, why = 'Servo Arms', 1.0, 'servo arm; no anchor rule yet'
    elif low.startswith('1h_handle'): cat, sc, why = 'Hands', 1.0, 'hand gripping a hilt (the blades slot on); the hand rule could not seat it'
    elif 'with_palm' in low: cat, sc, why = 'Melee', 1.0, 'weapon with its hand; the wrist fit could not be found'
    elif low == 'anchor': cat, sc, why = 'Hand-less Weapons', 1.0, 'anchor from the maker\'s accessories folder (could be a belt bit instead); Grip fit to do'
    elif low == 'handle': cat, sc, why = 'Hand-less Weapons', 1.0, 'bare haft, no hand and no head; Grip fit to do'
    elif low.startswith('lion_shield'): cat, sc, why = 'Shoulder Pads', 1.0, 'Lion Knights shoulder shield; no pad fit yet'
    elif re.search(r'2h', low) and not ARM.search(low): cat, sc, why = 'Two-Handed Held', 1.0, 'held in both hands, no arms; offHand/pivot fit to do'
    elif 'shield' in low: cat, sc, why = 'Shields', 1.0, 'shield whose handle did not match on Nov 2 (or none found) - place by eye'
    elif re.search(r'palm|hand_with|hook', low) or low == 'hand': cat, sc, why = 'Hands', 1.0, 'hand piece the hand rule could not seat'
    elif ARM.search(low) or kind == 'extra' and 'arm' in low:
        what = 'forearm and hand piece (no shoulder)' if re.search(r'heavy_arm_\d|blood_effect', low) else 'bike pose' if 'bike' in low else 'arm with no shoulder face the rules could find'
        cat, sc, why = 'Arms', 0.9, what + ' - place by eye'
    else: cat, sc, why = 'Hand-less Weapons', 1.0, 'weapon without a hand (or the hand rule found no grip); Grip fit to do'
    plan[rel] = {'category': cat, 'scale': sc, 'note': why}
print(len(plan), 'to file:', dict(collections.Counter(v['category'] for v in plan.values()))); print('skipped:', dict(skip))
json.dump(plan, open(OUT + 'plan.json', 'w'), indent=1)
open(OUT + 'skipped.txt', 'w').write('# Marta weapons/arms left out of the library on purpose (Nov 6)\n' + ''.join('%s\t%s\n' % x for x in sorted(skipped)))
for rel, v in sorted(plan.items(), key=lambda x: (x[1]['category'], x[0])): print('  %-18s %s' % (v['category'], '/'.join(rel.split('/')[1:])[-80:]))
if '--write' in sys.argv:
    for rel, v in plan.items():
        d = {'schemaVersion': 1, 'part': rel.rsplit('/', 1)[-1][:-4], 'category': v['category'], 'sockets': [], 'fits': {},
             'notes': {'category': 'filed without a fit so it is not missed (Nov 6, Josh): ' + v['note']}}
        if v['scale'] != 1.0: d['scale'] = v['scale']
        f = NC + rel[:-4] + '.sockets.json'
        if not os.path.exists(f): json.dump(d, open(f, 'w'), indent=1)
    print('sidecars written')
