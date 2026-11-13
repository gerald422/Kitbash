"""Run Caliper's own batch repair over a folder and everything under it, with no clicking.

    "Caliper Repair.bat" <folder> [all]         (drop a folder on the .bat)
    python caliper_repair.py <folder> [--all] [--dry] [--timeout seconds]
    (a Python with numpy: Blender's is the one the .bat uses)

Caliper (0.9.1) has a command line for its batch: 'Caliper.exe --batch-repair <config> <folder> <export parent>'. It
takes one folder's direct STL files, 256 at most, and repairs every one of them, clean or not. So for each folder under
<folder> this script:

  1. checks every STL with caliper_swap.py's fault test (open / non-manifold edges, flipped faces, degenerate
     triangles) and keeps the ones with a fault (--all: every binary STL, as Caliper's own batch would);
  2. copies those, 256 at a time, into a short work folder in the temp folder (%TEMP%\\caliper_work, or under
     CALIPER_WORK=<folder>) and runs Caliper on it. Never on the library's own drive: D: is exFAT and Caliper's batch
     refuses any path there ('Batch paths must not be links/reparse points'); it also has no long-path support and
     the library has paths past 259 characters;
  3. moves Caliper's output folder beside the originals as 'Caliper-repaired-<id>', its files named
     '<batch no>-<original name>_repaired.stl': exactly what Caliper's window leaves, and what Caliper Swap reads.

Nothing is replaced here: the originals stay as they are until Caliper Swap has checked each repaired file (same
place, no faults) and backed the original up. A file that already has a repaired copy waiting is left out, so a run
that was stopped can be started again and carries on.

Parts to leave as the maker made them: '_caliper_keep.txt' at the top of the library, a library path per line
('# why' lines above, as in _hidden.txt). They are not sent again.

--dry: only list the files with faults. --timeout: passed to Caliper. CALIPER=<path to Caliper.exe> if it isn't in
%LOCALAPPDATA%\\Programs\\CaliperView. Log: 'caliper_repair_log.csv' where Caliper Swap keeps its own (the library's
'_backups\\caliper-<date>\\', elsewhere '<folder>\\_caliper_backups\\<date>\\').
"""
import os, sys, re, csv, json, time, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import caliper_swap as CS            # load / faults / library_root: one fault test for both tools
except ImportError as e:
    sys.exit('caliper_repair.py needs numpy and caliper_swap.py beside it (%s): run it with Blender\'s Python, as '
             'Caliper Repair.bat does.' % e)

BATCH = 256                              # Caliper: 'Batch supports at most 256 STL files'
BATCH_BYTES = 3 << 29                    # and 1.5 GB a batch, so the work folder stays small
MARK = 'caliper_repair.tmp'              # marks a work folder as this script's own


def lp(p):
    """the path in Windows' long form, so paths past 259 characters open"""
    p = os.path.abspath(p)
    return p if os.name != 'nt' or p.startswith('\\\\') else '\\\\?\\' + p


def show(p):
    return p[4:] if p.startswith('\\\\?\\') else p


def find_caliper():
    for exe in (os.environ.get('CALIPER', ''),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'CaliperView', 'Caliper.exe'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'CaliperView', 'CaliperView.exe')):
        if exe and os.path.isfile(exe):
            cfg = os.path.join(os.path.dirname(exe), 'repair-backend.cfg')
            if os.path.isfile(cfg):
                return exe, cfg
    return None, None


def is_stl(name):
    n = name.lower()
    return n.endswith('.stl') and not n.endswith('_repaired.stl')


def is_output(d):
    """a folder of Caliper's output: it holds '*_repaired.stl'"""
    try:
        return any(n.lower().endswith('_repaired.stl') for n in os.listdir(d))
    except OSError:
        return False


def waiting(folder, names):
    """the originals in this folder that already have a repaired copy in a Caliper folder beside them"""
    have, low = set(), {n.lower() for n in names}
    for sub in os.listdir(folder):
        d = os.path.join(folder, sub)
        if not os.path.isdir(d) or sub.startswith('_'):
            continue
        for n in os.listdir(d):
            if not n.lower().endswith('_repaired.stl'):
                continue
            o = re.sub(r'_repaired\.stl$', '.stl', n, flags=re.I).lower()
            if o not in low and re.match(r'^\d+-', o):
                o = o.split('-', 1)[1]                     # Caliper's '<batch no>-' in front
            have.add(o)
    return have


def folders(root):
    """(folder, [stl names]) for every folder under root with STLs; '_' folders and Caliper's own output are skipped"""
    for d, dn, fs in os.walk(root):
        dn[:] = sorted(x for x in dn if not x.startswith('_') and not is_output(os.path.join(d, x)))
        names = sorted(f for f in fs if is_stl(f))
        if names:
            yield d, names


def run_caliper(exe, cfg, src, out, timeout):
    """Caliper's batch on one folder: (its report, None) or (None, why it failed)"""
    cmd = [exe, '--batch-repair', cfg, src, out] + (['--timeout', str(timeout)] if timeout else [])
    try:
        r = subprocess.run(cmd, capture_output=True)
    except OSError as e:
        return None, 'could not start Caliper: %s' % e
    text = r.stdout.decode('utf-8', 'replace')
    try:
        return json.loads(text[text.index('{'):]), None
    except ValueError:
        return None, ('Caliper exit %d: %s' % (r.returncode, (text or r.stderr.decode('utf-8', 'replace')).strip()[-300:]))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ALL, DRY = '--all' in argv or 'all' in argv, '--dry' in argv
    timeout = int(argv[argv.index('--timeout') + 1]) if '--timeout' in argv else 0
    args = [a for i, a in enumerate(argv) if not a.startswith('--') and a != 'all' and (i == 0 or argv[i - 1] != '--timeout')]
    if not args:
        sys.exit(__doc__)
    root = os.path.abspath(args[0].strip('"'))
    if not os.path.isdir(root):
        sys.exit('not a folder: ' + root)
    exe, cfg = find_caliper()
    if not exe and not DRY:
        sys.exit('Caliper.exe (with repair-backend.cfg beside it) was not found in %LOCALAPPDATA%\\Programs\\CaliperView: '
                 'set CALIPER to its path.')
    lib = CS.library_root(os.path.join(root, 'x'))
    origin = lib or root
    back = os.path.join(lib, '_backups', 'caliper-' + CS.STAMP) if lib else os.path.join(root, '_caliper_backups', CS.STAMP)
    work = os.path.join(os.environ.get('CALIPER_WORK') or tempfile.gettempdir(), 'caliper_work')
    if os.path.isdir(work):
        if not os.path.isfile(os.path.join(work, MARK)):
            sys.exit('%s exists and is not this script\'s: move it away first.' % work)
        shutil.rmtree(work)                                # left by a run that was stopped

    keep = set()
    if lib and os.path.isfile(os.path.join(lib, '_caliper_keep.txt')):
        with open(os.path.join(lib, '_caliper_keep.txt'), encoding='utf-8-sig') as fh:
            keep = {l.strip().replace('/', os.sep).lower() for l in fh if l.strip() and not l.lstrip().startswith('#')}
    todo = list(folders(lp(root)))
    total = sum(len(n) for _, n in todo)
    print('%s: %d STL files in %d folders%s' % (root, total, len(todo), ' (dry run: nothing is repaired)' if DRY else ''))
    rows, seen, n_fault, n_done, n_fail, n_wait, out_dirs, t0 = [], 0, 0, 0, 0, 0, [], time.time()
    stopped = None
    try:
        for folder, names in todo:
            rel = os.path.relpath(show(folder), origin)
            have = waiting(folder, names)
            send = []
            for name in names:
                seen += 1
                if seen % 250 == 0:
                    print('  checked %d of %d, %d with faults, %d repaired (%.0f min)' % (seen, total, n_fault, n_done, (time.time() - t0) / 60))
                row = {'folder': rel, 'file': name}
                if os.path.join(rel, name).lower() in keep:
                    continue                               # Josh's choice: the original stays
                if name.lower() in have:
                    n_wait += 1; row['status'] = 'a repaired copy is already waiting'; rows.append(row); continue
                try:
                    h, V, T = CS.load(os.path.join(folder, name))
                except OSError as e:
                    row['status'] = 'could not read: %s' % e; rows.append(row); continue
                if V is None or not len(T):
                    row['status'] = 'not a binary STL: left alone'; rows.append(row); continue
                f = CS.faults(T); row.update(f, tris_before=len(T))
                if any(f.values()):
                    n_fault += 1
                elif not ALL:
                    continue                               # clean: not logged, not sent
                row['status'] = 'has faults' if any(f.values()) else 'clean'
                rows.append(row); send.append(row)
            if DRY or not send:
                continue
            chunks, size = [[]], 0
            for r in send:                                 # 256 files and 1.5 GB a batch at most
                b = os.path.getsize(os.path.join(folder, r['file']))
                if chunks[-1] and (len(chunks[-1]) == BATCH or size + b > BATCH_BYTES):
                    chunks.append([]); size = 0
                chunks[-1].append(r); size += b
            for chunk in chunks:
                size = sum(os.path.getsize(os.path.join(folder, r['file'])) for r in chunk)
                for where, need in ((os.path.dirname(work), 3 * size + (1 << 30)), (origin, size + (1 << 29))):
                    free = shutil.disk_usage(where).free
                    if free < need:
                        stopped = 'not enough free space on %s for the next batch (%.1f GB free)' % (os.path.splitdrive(where)[0], free / 2 ** 30)
                        raise StopIteration
                src, out = os.path.join(work, 'in'), os.path.join(work, 'out')
                os.makedirs(src); os.makedirs(out)
                open(os.path.join(work, MARK), 'w').close()
                for r in chunk:
                    shutil.copyfile(os.path.join(folder, r['file']), os.path.join(src, r['file']))
                rep, err = run_caliper(exe, cfg, src, out, timeout)
                by = {i.get('name', '').lower(): i for i in (rep or {}).get('items', [])}
                if not by:                                 # Caliper refused the whole batch: the next would go the same way
                    why = err or (rep or {}).get('message') or (rep or {}).get('technical_error') or 'no report'
                    for r in chunk:
                        n_fail += 1; r['status'] = 'Caliper refused the batch: ' + why
                    stopped = 'Caliper refused the batch (%s). Work folder: %s' % (why, work)
                    raise StopIteration
                made = (rep or {}).get('export_folder', '')
                dest = ''
                if made and os.path.isdir(made) and os.listdir(made):
                    tag = os.path.basename(made); short = tag[:len('Caliper-repaired-') + 8]
                    dest = os.path.join(folder, short if not os.path.exists(os.path.join(folder, short)) else tag)
                    shutil.move(made, dest); out_dirs.append(dest)
                for r in chunk:
                    i = by.get(r['file'].lower())
                    if i is None:
                        n_fail += 1; r['status'] = err or (rep or {}).get('message') or 'Caliper did not report on it'; continue
                    r['tris_after'] = i.get('triangles_after', '')
                    got = os.path.join(dest, os.path.basename(i.get('destination', ''))) if dest and i.get('destination') else ''
                    if i.get('status') == 'Exported' and got and os.path.isfile(got):
                        n_done += 1; r['status'] = 'repaired'; r['repaired'] = os.path.relpath(show(got), origin)
                    else:
                        n_fail += 1; r['status'] = 'Caliper: %s %s' % (i.get('status', ''), i.get('error') or i.get('technical_error') or '')
                shutil.rmtree(work)
                print('  %-86s %3d sent, %3d repaired' % (rel[-86:], len(chunk), sum(1 for r in chunk if r['status'] == 'repaired')))
    except StopIteration:
        pass
    except KeyboardInterrupt:
        stopped = 'stopped by you: run it again to carry on'
    finally:
        if os.path.isfile(os.path.join(work, MARK)):
            shutil.rmtree(work, ignore_errors=True)
        if rows:
            os.makedirs(back, exist_ok=True)
            log = os.path.join(back, 'caliper_repair_log.csv')
            new = not os.path.isfile(log)
            with open(log, 'a', encoding='utf-8-sig' if new else 'utf-8', newline='') as fh:
                w = csv.DictWriter(fh, ['status', 'folder', 'file', 'open', 'nonmanifold', 'flipped', 'degenerate', 'tris_before', 'tris_after', 'repaired'],
                                   extrasaction='ignore', lineterminator='\r\n')
                if new:
                    w.writeheader()
                w.writerows(rows)

    print('\n%d of %d STL files checked in %.0f min: %d with faults' % (seen, total, (time.time() - t0) / 60, n_fault))
    if n_wait:
        print('%d already had a repaired copy waiting (left out)' % n_wait)
    if DRY:
        bad = [r for r in rows if r['status'] == 'has faults']
        for r in bad[:40]:
            print('   %s\\%s - open %d, non-manifold %d, flipped %d, degenerate %d' % (r['folder'], r['file'], r['open'], r['nonmanifold'], r['flipped'], r['degenerate']))
        if len(bad) > 40:
            print('   ... and %d more, in the log' % (len(bad) - 40))
    else:
        print('%d repaired by Caliper into %d folder(s) beside the originals, %d not repaired' % (n_done, len(out_dirs), n_fail))
        for r in rows:
            if r['status'] not in ('repaired', 'has faults', 'clean', 'a repaired copy is already waiting') and not r['status'].startswith('Caliper refused'):
                print('   %s\\%s - %s' % (r['folder'], r['file'], r['status']))
    if stopped:
        print('STOPPED: ' + stopped)
    if rows:
        print('log:', log)
    if n_done or n_wait:
        print('The originals are unchanged. Caliper Swap checks each repaired file and puts it in place.')
    sys.exit(3 if stopped else 0 if (n_done or n_wait) else 1)


if __name__ == '__main__':
    main()
