"""Golden placements: build the fixed squads (squads.json) with the TIOW Inbox that is installed, the way the Squad
Builder sends them, and compare every part's place (relative to its torso) with golden.json.

    blender --background --python tests/golden/run.py -- LIBRARY [record] [--only g01,g02] [--addon PATH]

  record       write golden.json from this run (do it when placements are known good, and after re-making squads)
  --only       just these models (a subset after a change)
  --addon      install this tiow_inbox.py first (the container; on the PC the installed add-on is used)
  --squads F   other squads than squads.json; --golden F  another reference file (a one-off before / after check)
Writes report.txt next to this file: one line per part that moved more than 0.05 mm / 0.1 deg, went missing or is
new; 'all N parts where they were' otherwise. Exit code 1 if anything differs. Costs no Claude usage on the PC:
Run checks.bat runs it."""
import bpy, json, math, os, sys, tempfile
from mathutils import Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
LIB = A[0] if A else "D:\\Kitbash Library"
record = "record" in A
only = A[A.index("--only") + 1].split(",") if "--only" in A else None
squads = json.load(open(A[A.index("--squads") + 1] if "--squads" in A else os.path.join(HERE, "squads.json"), encoding="utf-8"))
if only: squads = {k: v for k, v in squads.items() if k in only}

import addon_utils
bpy.ops.wm.read_homefile(use_empty=True)
for mod in ("bl_ext.user_default.part_sockets", "part_sockets"):
    try:
        if addon_utils.enable(mod, default_set=False): break
    except Exception: pass
if "--addon" in A:
    bpy.ops.preferences.addon_install(filepath=A[A.index("--addon") + 1], overwrite=True)
addon_utils.enable("tiow_inbox", default_set=False)
import tiow_inbox as T
prefs = T.get_prefs()
old = (prefs.inbox_path, prefs.builder_inbox)
prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
got, n, missing_files = {}, 0, []
try:
    T.process_inbox()
    for i, (m, parts) in enumerate(squads.items()):
        for p, cat, sock in parts:
            f = os.path.join(LIB, *p.split("/")) + ".stl"
            if not os.path.exists(f): missing_files.append(p); continue
            r = {"schemaVersion": 1, "path": f, "name": os.path.basename(p), "title": "", "category": cat, "tags": [],
                 "itemId": "", "sentAt": "", "model": m}
            if sock: r["socket"] = sock
            else: r["at"] = [80 * i, 0, 0]
            n += 1
            with open(os.path.join(inbox, "g-%04d.json" % n), "w", encoding="utf-8") as fh: json.dump(r, fh)
        T._state["beat"] = {}; T.process_inbox()
finally:
    prefs.inbox_path, prefs.builder_inbox = old         # never leave the test inboxes in Josh's preferences
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']


def maker_frame(o):
    """o's place as its maker's file would lie: a part whose origin was moved to its joint (kb.origin, notes 101)
    keeps 'origin.from_file' in its sidecar, so the reference stays good whichever way the file's origin lies"""
    try:
        d = json.load(open(os.path.splitext(o.get("tiow_src", ""))[0] + ".sockets.json", encoding="utf-8-sig"))
        # a variant's own sidecar; -1 is a mirror made on the spot and not saved (TIOW Inbox 1.17.10, notes 106): the file's, mirrored
        synth = o.get("tiow_variant") is not None and int(o["tiow_variant"]) < 0
        if o.get("tiow_variant") is not None and not synth: d = d["variants"][int(o["tiow_variant"])]["sidecar"]
        g = d["origin"]["from_file"]; G = Matrix([g[i:i + 4] for i in (0, 4, 8, 12)])
        G.translation = G.translation * (float(o.get("tiow_unit", 1.0)) or 1.0)
        if o.get("tiow_mirrored") or synth:           # mirrored on the spot (a right pad on a left arm): its mesh is the file's, mirrored
            MX = Matrix.Scale(-1, 4, (1, 0, 0)); G = MX @ G @ MX
        return o.matrix_world @ G
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return o.matrix_world.copy()


for m, parts in squads.items():
    mine = [o for o in obs if o.get("tiow_model") == m]
    stem = lambda o: os.path.splitext(os.path.basename(o.get("tiow_src", "")))[0]
    root = next((o for o in mine if stem(o) == os.path.basename(parts[0][0])), None)
    inv = maker_frame(root).inverted() if root else Matrix.Identity(4)
    for p, cat, sock in parts[1:] if root else []:
        o = next((x for x in mine if stem(x) == os.path.basename(p) and x is not root), None)
        if o is not None:
            got["%s|%s|%s" % (m, sock, p)] = [round(v, 4) for row in (inv @ maker_frame(o)) for v in row]
    if root: got["%s|root|%s" % (m, parts[0][0])] = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]

G = A[A.index("--golden") + 1] if "--golden" in A else os.path.join(HERE, "golden.json")
lines = []
if record or not os.path.exists(G):
    old_g = json.load(open(G, encoding="utf-8")) if os.path.exists(G) else {}
    if only: old_g.update(got); got_all = old_g
    else: got_all = got
    open(G, "w", encoding="utf-8", newline="\n").write(json.dumps(got_all, indent=0, sort_keys=True))
    lines.append("recorded %d parts in golden.json (TIOW Inbox %s)" % (len(got), ".".join(map(str, T.bl_info["version"]))))
    bad = 0
else:
    gold = json.load(open(G, encoding="utf-8"))
    if only: gold = {k: v for k, v in gold.items() if k.split("|")[0] in only}
    bad = 0
    for k in sorted(set(gold) | set(got)):
        if k not in got: bad += 1; lines.append("MISSING  " + k); continue
        if k not in gold: bad += 1; lines.append("NEW      " + k); continue
        a, b = Matrix([gold[k][i:i + 4] for i in (0, 4, 8, 12)]), Matrix([got[k][i:i + 4] for i in (0, 4, 8, 12)])
        d = (a.inverted() @ b)
        mm = (b.to_translation() - a.to_translation()).length
        # the turn from the matrix's skew part: acos of the trace alone turns a last-place rounding into 0.6 deg
        sn = 0.5 * math.sqrt((d[2][1] - d[1][2]) ** 2 + (d[0][2] - d[2][0]) ** 2 + (d[1][0] - d[0][1]) ** 2)
        deg = math.degrees(math.atan2(sn, (d[0][0] + d[1][1] + d[2][2] - 1) / 2))
        if mm > 0.05 or deg > 0.1: bad += 1; lines.append("MOVED    %s  %.2f mm, %.1f deg" % (k, mm, deg))
    lines.append(("all %d parts where they were" % len(got)) if not bad else "%d of %d parts differ" % (bad, len(gold)))
if missing_files: lines.append("not in the library (re-make squads?): " + ", ".join(missing_files[:8]))
open(os.path.join(HERE, "report.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines[-12:]))
sys.exit(1 if bad else 0)
