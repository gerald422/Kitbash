"""Put Caliper's repaired STLs in place of their originals, after checking each one.

    "Caliper Swap.bat" <folder>            (Blender's Python; drop a folder on the .bat)
    blender --background --python caliper_swap.py -- <folder> [--dry] [--scan] [--no-move]
    python3 caliper_swap.py <folder> [...]  (plain Python with numpy + scipy also works)

Caliper's batch writes the files it repaired into an output folder ('Caliper-repaired-<id>' beside the originals by
default, or a name chosen in Caliper), as '[<batch no>-]<original name>_repaired.stl'. <folder> can be the folder of
originals (or any folder above it) or the output folder itself. For every '*_repaired.stl' found:

  1. find its original ('<folder>\\<original name>.stl');
  2. check it: a binary STL, no open / non-manifold edges, no flipped (doubled directed) edges, no degenerate
     triangles; the same place - bounding box within 0.05 mm, 95% of its vertices within 0.01 mm of the original
     surface and none further than 0.25 mm (every sidecar fit and socket is in the STL's own coordinates, so a file that
     moved would break them); triangle count within 5%;
  3. if it passes: back up the original, then the repaired file takes the original's name and place.

Backups: in the Kitbash Library (a folder above holding _sources.csv) to '_backups\\caliper-<date>\\<same path>', and
the part is listed in '_repaired.csv' at the library root so build_library.py never copies the maker's file back
over it; elsewhere (D:\\new cults ...) to '_caliper_backups\\<date>\\<same path>' at the top of <folder>.
A Caliper folder whose files were all swapped is moved into the backup folder (--no-move keeps it), so it is never
swapped twice; one with files kept back stays where it is, to look at.
--dry: check and report only. --scan: afterwards also check every STL under <folder> and list the ones still not clean
(Caliper skips some) in 'still_dirty.csv' in the backup folder. Every run writes 'caliper_swap_log.csv' there too.
"""
import os, sys, re, csv, glob, time, shutil, struct, hashlib
import numpy as np

TOL_BOX, TOL_95, TOL_MAX, TOL_TRIS = 0.05, 0.01, 0.25, 0.05
STAMP = time.strftime('%Y-%m-%d')


def load(path):
    """(header, V, T) of a binary STL, vertices welded (bit-identical corners); (None, None, None) for ASCII or a short file."""
    with open(path, 'rb') as fh:
        d = fh.read()
    if len(d) < 84 or (d[:5].lower() == b'solid' and b'facet' in d[:512]):
        return None, None, None
    n = struct.unpack('<I', d[80:84])[0]
    if len(d) < 84 + 50 * n:
        return None, None, None
    v = np.ascontiguousarray(np.frombuffer(d[84:84 + 50 * n], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))['v'].reshape(-1, 3))
    _, first, inv = np.unique(v.view(np.dtype((np.void, 12))).ravel(), return_index=True, return_inverse=True)
    return d[:80], v[first].astype(np.float64), inv.reshape(-1, 3)


def _keys(E, n):
    return E[:, 0].astype(np.int64) * n + E[:, 1]


def faults(T):
    """open edges, non-manifold edges, flipped faces (a directed edge used twice), degenerate triangles"""
    n = int(T.max()) + 1
    deg = (T[:, 0] == T[:, 1]) | (T[:, 1] == T[:, 2]) | (T[:, 0] == T[:, 2])
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    _, c = np.unique(_keys(np.sort(e, 1), n), return_counts=True)
    _, dc = np.unique(_keys(e, n), return_counts=True)
    return {'open': int((c == 1).sum()), 'nonmanifold': int((c > 2).sum()), 'flipped': int((dc > 1).sum()), 'degenerate': int(deg.sum())}


def _cell_keys(P, g, off):
    k = np.floor((P + off) / g).astype(np.int64) + (1 << 20)
    return (k[:, 0] << 42) | (k[:, 1] << 21) | k[:, 2]


def nearest(Vref, P, g=0.005):
    """distance from each point of P to a vertex of Vref: exact nearest (scipy), or in Blender's Python an upper bound
    (<= g*sqrt(3)) for points sharing a grid cell with a vertex of Vref on one of two offset grids, exact for the rest"""
    try:
        from scipy.spatial import cKDTree
        return cKDTree(Vref).query(P)[0]
    except ImportError:
        pass
    d = np.full(len(P), np.inf)
    for off in (0.0, g / 2):
        kr, kp = _cell_keys(Vref, g, off), _cell_keys(P, g, off)
        order = np.argsort(kr); ks = kr[order]
        i = np.clip(np.searchsorted(ks, kp), 0, len(ks) - 1)
        hit = ks[i] == kp
        dd = np.linalg.norm(P[hit] - Vref[order[i[hit]]], axis=1)
        d[hit] = np.minimum(d[hit], dd)
    rest = np.where(~np.isfinite(d))[0]
    if len(rest):
        from mathutils.kdtree import KDTree          # Blender's Python, only for the few points the repair moved
        lo, hi = P[rest].min(0) - 1.0, P[rest].max(0) + 1.0
        near = np.where(np.all((Vref >= lo) & (Vref <= hi), axis=1))[0]
        kd = KDTree(len(near))
        for j in near:
            kd.insert(Vref[j], int(j))
        kd.balance()
        for j in rest:
            got = kd.find(P[j])
            d[j] = got[2] if got[1] is not None else np.inf
    return d


def _closest_on_tris(p, A, B, C):
    """distance from point p to each triangle (A, B, C rows): exact closest point (regions of Ericson's test)"""
    ab, ac, ap = B - A, C - A, p - A
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp, cp = p - B, p - C
    d3, d4, d5, d6 = (ab * bp).sum(1), (ac * bp).sum(1), (ab * cp).sum(1), (ac * cp).sum(1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = va + vb + vc
    den = np.where(np.abs(den) < 1e-30, 1e-30, den)
    v, w = vb / den, vc / den
    best = np.linalg.norm(A + ab * v[:, None] + ac * w[:, None] - p, axis=1)
    best = np.where((va >= 0) & (vb >= 0) & (vc >= 0), best, np.inf)
    for s_, e_ in ((A, B), (B, C), (C, A)):
        se = e_ - s_; t = np.clip(((p - s_) * se).sum(1) / np.maximum((se * se).sum(1), 1e-30), 0, 1)
        best = np.minimum(best, np.linalg.norm(s_ + se * t[:, None] - p, axis=1))
    return best


def surface_distance(V0, T0, P, d_vertex, tol):
    """refine the points whose nearest original vertex is further than tol: distance to the original surface
    (a re-triangulated flat face puts new vertices on the surface but far from any old vertex)"""
    d = d_vertex.copy()
    far = np.where(d > tol)[0]
    if not len(far):
        return d
    A, B, C = V0[T0[:, 0]], V0[T0[:, 1]], V0[T0[:, 2]]
    lo, hi = np.minimum(np.minimum(A, B), C), np.maximum(np.maximum(A, B), C)
    for j in far[:20000]:
        p = P[j]; r = d[j]
        m = np.all((lo <= p + r) & (hi >= p - r), axis=1)
        if m.any():
            d[j] = min(d[j], float(_closest_on_tris(p, A[m], B[m], C[m]).min()))
    return d


def library_root(path):
    d = os.path.dirname(path)
    for _ in range(14):
        if os.path.isfile(os.path.join(d, '_sources.csv')):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up
    return None


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    DRY, SCAN, NOMOVE = '--dry' in argv, '--scan' in argv, '--no-move' in argv
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    ROOT = os.path.abspath(args[0].strip('"'))
    if glob.glob(os.path.join(ROOT, '*_repaired.stl')):      # the Caliper output folder itself was dropped: work from its parent
        ROOT = os.path.dirname(ROOT)
    LIB = library_root(os.path.join(ROOT, 'x'))
    BACK = os.path.join(LIB, '_backups', 'caliper-' + STAMP) if LIB else os.path.join(ROOT, '_caliper_backups', STAMP)
    ORIGIN = LIB or ROOT                                   # backup paths mirror the paths below this
    rows, swapped = [], []
    # Caliper's output: any folder holding '*_repaired.stl' ('Caliper-repaired-<id>' by default, or the name chosen in Caliper)
    cal_dirs = sorted({os.path.dirname(f) for f in glob.glob(os.path.join(ROOT, '**', '*_repaired.stl'), recursive=True)
                       if '_backups' not in f and '_caliper_backups' not in f})
    print('Caliper folders under %s: %d%s' % (ROOT, len(cal_dirs), ' (dry run)' if DRY else ''))
    for cd in cal_dirs:
        home = os.path.dirname(cd)
        done_here = 0
        for rep in sorted(glob.glob(os.path.join(cd, '*_repaired.stl'))):
            name = re.sub(r'_repaired\.stl$', '.stl', os.path.basename(rep), flags=re.I)
            orig = os.path.join(home, name)
            if not os.path.isfile(orig) and re.match(r'^\d+-', name):
                orig = os.path.join(home, name.split('-', 1)[1])       # Caliper's '<batch no>-' prefix
            if not os.path.isfile(orig) and os.path.isfile(os.path.join(cd, name)):
                orig = os.path.join(cd, name)                          # written beside the original
            row = {'original': os.path.relpath(orig, ORIGIN), 'repaired': os.path.relpath(rep, ORIGIN)}
            if not os.path.isfile(orig):
                row['status'] = 'no original found'; rows.append(row); continue
            h0, V0, T0 = load(orig); h1, V1, T1 = load(rep)
            if V1 is None or V0 is None:
                row['status'] = 'not a binary STL'; rows.append(row); continue
            f0, f1 = faults(T0), faults(T1)
            box = float(np.abs(np.r_[V1.min(0) - V0.min(0), V1.max(0) - V0.max(0)]).max())
            d = surface_distance(V0, T0, V1, nearest(V0, V1), TOL_95)
            p95, dmax = float(np.percentile(d, 95)), float(d.max())
            row.update(tris_before=len(T0), tris_after=len(T1), box_shift=round(box, 4), move_95=round(p95, 4), move_max=round(dmax, 4),
                       **{k + '_before': v for k, v in f0.items()}, **{k + '_after': v for k, v in f1.items()})
            why = []
            if any(f1.values()): why.append('still has faults')
            if box > TOL_BOX: why.append('bounding box moved %.3f mm' % box)
            if p95 > TOL_95 or dmax > TOL_MAX: why.append('surface moved (95%% %.3f, max %.3f mm)' % (p95, dmax))
            if abs(len(T1) - len(T0)) > TOL_TRIS * len(T0): why.append('triangle count changed %d -> %d' % (len(T0), len(T1)))
            if why:
                row['status'] = 'kept original: ' + '; '.join(why); rows.append(row); continue
            if DRY:
                row['status'] = 'would swap'; rows.append(row); continue
            bk = os.path.join(BACK, os.path.relpath(orig, ORIGIN))
            os.makedirs(os.path.dirname(bk), exist_ok=True)
            if not os.path.exists(bk):
                shutil.copy2(orig, bk)
            shutil.copyfile(rep, orig + '.part'); os.replace(orig + '.part', orig)
            row['status'] = 'swapped'; row['md5'] = md5(orig); rows.append(row); swapped.append(row); done_here += 1
        n_here = len(glob.glob(os.path.join(cd, '*_repaired.stl')))
        if not DRY and not NOMOVE and n_here and done_here == n_here:    # all taken: out of the way (kept otherwise, to look at)
            dst = os.path.join(BACK, 'caliper-output', os.path.relpath(cd, ORIGIN))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(cd, dst)
        print('  %-90s %d swapped' % (os.path.relpath(cd, ROOT)[-90:], done_here))

    if swapped and LIB and not DRY:
        # parts the library keeps repaired: build_library.py leaves these alone
        p = os.path.join(LIB, '_repaired.csv'); have = []
        if os.path.isfile(p):
            with open(p, encoding='utf-8-sig', newline='') as fh:
                have = list(csv.reader(fh))[1:]
        keep = {r[0].lower(): r for r in have if r}
        for r in swapped:
            keep[r['original'].replace('/', '\\').lower()] = [r['original'].replace('/', '\\'), STAMP, str(r['tris_before']), str(r['tris_after']),
                                                             str(os.path.getsize(os.path.join(LIB, r['original']))), r['md5']]
        with open(p, 'w', encoding='utf-8-sig', newline='') as fh:
            w = csv.writer(fh, lineterminator='\r\n')
            w.writerow(['library path', 'repaired on', 'triangles before', 'triangles after', 'bytes', 'md5'])
            w.writerows(keep[k] for k in sorted(keep))

    dirty = []
    if SCAN:
        for f in sorted(glob.glob(os.path.join(ROOT, '**', '*.stl'), recursive=True)):
            if '_backups' in f or '_caliper_backups' in f or f.lower().endswith('_repaired.stl') or os.path.dirname(f) in cal_dirs:
                continue
            h, V, T = load(f)
            if V is None:
                dirty.append([os.path.relpath(f, ORIGIN), 'not a binary STL', '', '', '']); continue
            fl = faults(T)
            if any(fl.values()):
                dirty.append([os.path.relpath(f, ORIGIN), fl['open'], fl['nonmanifold'], fl['flipped'], fl['degenerate']])

    os.makedirs(BACK, exist_ok=True)
    log = os.path.join(BACK, 'caliper_swap_log.csv')
    fields = ['status', 'original', 'repaired', 'tris_before', 'tris_after', 'box_shift', 'move_95', 'move_max'] + \
             [k + s for s in ('_before', '_after') for k in ('open', 'nonmanifold', 'flipped', 'degenerate')] + ['md5']
    new = not os.path.isfile(log)
    with open(log, 'a', encoding='utf-8-sig' if new else 'utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fields, extrasaction='ignore', lineterminator='\r\n')
        if new:
            w.writeheader()
        w.writerows(rows)
    if SCAN:
        with open(os.path.join(BACK, 'still_dirty.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
            w = csv.writer(fh, lineterminator='\r\n')
            w.writerow(['file', 'open edges', 'non-manifold edges', 'flipped', 'degenerate'])
            w.writerows(dirty)
    n = lambda s: sum(1 for r in rows if r['status'].startswith(s))
    print('\n%d repaired files: %d %s, %d kept original, %d other' % (len(rows), n('swapped') + n('would swap'), 'would swap' if DRY else 'swapped',
                                                                      n('kept original'), len(rows) - n('swapped') - n('would swap') - n('kept original')))
    for r in rows:
        if not r['status'].startswith(('swapped', 'would swap')):
            print('  ', r['original'], '-', r['status'])
    if SCAN:
        print('still not clean after this run: %d (listed in %s)' % (len(dirty), os.path.join(BACK, 'still_dirty.csv')))
    print('log:', log)


if __name__ == '__main__':
    main()
