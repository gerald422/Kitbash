"""Replay a regression test against another copy of the test library and log
where every sent part lands (socket, pose relative to its model's root).

    blender-python replay.py TEST.py LIBDIR LOG.json [RENAME_LOG.csv]

With a rename log, the test's file paths are translated to the renamed files
(so the same parts are sent). Compare two logs with cmp_logs.py."""
import csv, json, os, sys
test, libdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
MAP = {}
if len(sys.argv) > 4:
    with open(sys.argv[4], encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["status"] == "renamed":
                MAP[r["was"].replace("\\", "/")] = r["now"].replace("\\", "/")
src = open(test).read()
for c in ("/home/claude/test/v18/common18.py", "/home/claude/test/v17/common17.py"):
    line = f'exec(open("{c}").read())'
    if line in src:
        common = open(c).read().replace('LIB = "/home/claude/test/kitlib"', f'LIB = {libdir!r}')
        hook = '''
import numpy as _np
_LOG = []
_send0, _side0 = send, side
def _m(rel):
    return _MAP.get(rel.replace("\\\\", "/"), rel)
def send(rel, cat="Weapons", cursor=None):
    ob = _send0(_m(rel), cat, cursor)
    rec = {"i": len(_LOG), "rel": rel, "cat": cat, "status": T._state["last"][:160]}
    try:
        s = T._part_sockets()[1].snap_socket_of(ob) if ob is not None else None
        root = ob
        while root is not None and root.parent is not None: root = root.parent
        rec["sock"] = str(s.get("ws_type")) if s is not None else None
        rec["orig"] = str(ob.get("tiow_orig") or "") if ob is not None else ""
        if ob is not None and root is not None:
            M = _np.linalg.inv(_np.array([list(r) for r in root.matrix_world])) @ _np.array([list(r) for r in ob.matrix_world])
            rec["M"] = M.round(5).tolist()
    except Exception as exc:
        rec["err"] = repr(exc)
    _LOG.append(rec)
    return ob
def side(rel):
    return _side0(_m(rel))
import atexit
atexit.register(lambda: json.dump(_LOG, open(_OUT, "w"), indent=0))
'''
        src = src.replace(line, f"_MAP = {MAP!r}\n_OUT = {out!r}\nexec({common!r})\n" + hook)
        break
else:
    raise SystemExit("test doesn't use common17/18")
os.chdir(os.path.dirname(os.path.abspath(test)))
exec(compile(src, test, "exec"))
