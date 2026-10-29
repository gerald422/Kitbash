#!/usr/bin/env python3
"""Copy the planned parts (~/catalogue/plan.json) into the library:
STL as is, sidecar with its folder fits folded in (and the type when it came
from the file name). Resumable: a part already there at the same size is
skipped, so run it again until it says COPY DONE. Stops itself after
--time seconds. Then 'verify' checks every STL (size + sampled hash) and
every sidecar.
    build_library.py <library root> [verify] [--time 160] [--workers 6] [--work ~/catalogue]"""
import os, sys, json, time, hashlib, csv, shutil
from concurrent.futures import ThreadPoolExecutor

SRC = os.path.expanduser('~/mnt/new cults')
args = sys.argv[1:]
def opt(name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return type(default)(v)
    return default
BUDGET = opt('--time', 160.0); WORKERS = opt('--workers', 6)
WORK = os.path.expanduser(opt('--work', '~/catalogue'))   # where plan.json is (plan_library.py --work)
DST = args[0]
VERIFY = len(args) > 1 and args[1] == 'verify'
plan = json.load(open(os.path.join(WORK, 'plan.json')))
log = open(os.path.join(WORK, 'verify.log' if VERIFY else 'copy.log'), 'a', buffering=1)

def shash(p, size):
    h = hashlib.md5(str(size).encode())
    with open(p, 'rb') as fh:
        for off in (0, max(0, size // 2 - 131072), max(0, size - 262144)):
            fh.seek(off); h.update(fh.read(262144))
    return h.hexdigest()

def sidecar(r):
    side = dict(r['side'] or {})
    if r['folderFits']:
        fits = dict(side.get('fits') or {})
        for k, v in sorted(r['folderFits'].items()):
            m = v.get('m') if isinstance(v, dict) else v
            if isinstance(m, list) and len(m) == 16:
                fits.setdefault(k, m)
        side['fits'] = fits
    if r['catFrom'] != 'sidecar' or not side.get('category'):
        side['category'] = r['category']
    return side

def paths(r):
    return (os.path.join(SRC, r['rel']), os.path.join(DST, r['dst']), os.path.join(DST, r['scDst']))

def check(r):
    src, dst, scd = paths(r)
    try:
        ok = os.path.isfile(dst) and os.path.getsize(dst) == r['bytes'] and \
            shash(dst, r['bytes']) == shash(src, r['bytes']) and \
            json.load(open(scd, encoding='utf-8')) == sidecar(r)
    except Exception:
        ok = False
    return r['dst'], ok

def copy(r):
    src, dst, scd = paths(r)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    n = 0
    if not (os.path.isfile(dst) and os.path.getsize(dst) == r['bytes']):
        shutil.copyfile(src, dst + '.part')
        os.replace(dst + '.part', dst)
        n = r['bytes']
    want = sidecar(r)
    try:
        same = json.load(open(scd, encoding='utf-8')) == want
    except Exception:
        same = False
    if not same:
        with open(scd + '.part', 'w', encoding='utf-8') as fh:
            json.dump(want, fh, indent=1)
        os.replace(scd + '.part', scd)
    return n

t0 = time.time()
todo = plan
if not VERIFY:
    # cheap pass first: what is already there
    todo = [r for r in plan if not (os.path.isfile(paths(r)[1]) and os.path.getsize(paths(r)[1]) == r['bytes']
                                    and os.path.isfile(paths(r)[2]))]
    log.write('start: %d of %d to copy (%.2f GB)\n' % (len(todo), len(plan), sum(r['bytes'] for r in todo) / 1e9))
    # sidecars of parts already copied are rewritten only if they differ
    rest = [r for r in plan if r not in todo] if len(todo) < len(plan) else []
results, bad, copied, i = [], [], 0, 0
with ThreadPoolExecutor(WORKERS) as ex:
    futs = []
    for r in todo:
        if time.time() - t0 > BUDGET:
            break
        futs.append(ex.submit(check if VERIFY else copy, r))
        if len(futs) >= WORKERS * 2:
            f = futs.pop(0); v = f.result(); i += 1
            if VERIFY:
                if not v[1]: bad.append(v[0])
            else:
                copied += v
    for f in futs:
        v = f.result(); i += 1
        if VERIFY:
            if not v[1]: bad.append(v[0])
        else:
            copied += v
el = time.time() - t0
if VERIFY:
    for b in bad: log.write('BAD %s\n' % b)
    log.write('VERIFY %s %d/%d checked, %d bad, %.0fs\n' % ('DONE' if i == len(plan) else 'PARTIAL', i, len(plan), len(bad), el))
    print('verified', i, 'of', len(plan), 'bad', len(bad))
else:
    left = len(todo) - i
    log.write('%d copied this run, %.2f GB, %.0fs, %.1f MB/s, %d left\n' % (i, copied / 1e9, el, copied / 1e6 / max(el, 1), left))
    print('copied', i, '%.2f GB' % (copied / 1e9), '%.1f MB/s' % (copied / 1e6 / max(el, 1)), 'left', left)
    if left == 0:
        if rest and time.time() - t0 < BUDGET:
            for r in rest:
                copy(r)       # refresh sidecars only (STL already there)
        # rows already in _sources.csv for other parts are kept (a plan for just the creators being added)
        rows = {}
        try:
            with open(os.path.join(DST, '_sources.csv'), newline='', encoding='utf-8') as fh:
                for row in list(csv.reader(fh))[1:]:
                    if row: rows[row[0].lower()] = row
        except OSError:
            pass
        for r in plan:
            row = [r['dst'].replace('/', '\\'), r['rel'].replace('/', '\\'), r['category'], ' '.join(sorted(r['folderFits']))]
            rows[row[0].lower()] = row
        with open(os.path.join(DST, '_sources.csv'), 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['library path', 'copied from (D:\\new cults)', 'type', 'folder fits folded in'])
            for k in sorted(rows):
                w.writerow(rows[k])
        log.write('COPY DONE\n'); print('COPY DONE')
