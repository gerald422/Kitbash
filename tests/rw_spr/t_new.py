"""Nov 9 batch through TIOW Inbox 1.17.7 (sent like the Squad Builder does): new parts mixed with Mar Fil and Springles
both ways. Checks every requested part snapped, how far each new part is from its host (closest approach) and how deep
it cuts in, and renders each model.   python t_new.py -- WORKLIB TIOW_FILE OUTDIR"""
import bpy, json, os, sys, tempfile, math
import numpy as np
from mathutils.bvhtree import BVHTree
W, TIOW, OUTD = sys.argv[sys.argv.index("--") + 1:][:3]
sys.path.insert(0, "/home/claude/kitbash/tests"); import rend
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
RW = "Redwarden/"; SP = "Springles/"; MF = "MarFil/"
TOR_RW = RW + "Prime Techmarine torso (Flat Bottom)"; TOR_MF = MF + "MarFil Assault - Torso 1"
LEGS = MF + "MarFil Assault - Legs 1A"; A76 = MF + "MarFil Assault - Arm 1A R"; A7B = MF + "MarFil Assault - Arm 7B R"
SPR_R = SP + "Springles Pattern C - Melee Arm 1 R"; SPR_L = SP + "Springles Pattern C - Melee Arm 1 L"
MODELS = {
  "rw_body": [(TOR_RW, "Chests", None), (LEGS, "Legs", "Waist"), (A76, "Arms", "Shoulder R"), (SPR_L, "Arms", "Shoulder L"),
              (RW + "Mk7 Cog Pad", "Shoulder Pads", "Pad R"), (RW + "Mk6 Techmarine Pad", "Shoulder Pads", "Pad L"),
              (RW + "Mk7 Techmarine Helmet", "Heads", "Neck"), (SP + "mk4 vox backpack", "Backpacks", "Back")],
  "mf_body": [(TOR_MF, "Chests", None), (LEGS, "Legs", "Waist"), (SPR_R, "Arms", "Shoulder R"), (A7B, "Arms", "Shoulder L"),
              (SP + "mk4 riveted", "Shoulder Pads", "Pad R"), (SP + "blank pad v1", "Shoulder Pads", "Pad L"),
              (SP + "mk5 helmet v1", "Heads", "Neck"), (SP + "mk2 vox anvillus backpack", "Backpacks", "Back"),
              (SP + "pouch", "Accessories", "Hip R"), (SP + "frag grenade single", "Grenades", "Hip L"), (SP + "tigris mag pouch top", "Accessories", "Belt Back")],
  "mix": [(TOR_MF, "Chests", None), (LEGS, "Legs", "Waist"), (A76, "Arms", "Shoulder R"), (SPR_L, "Arms", "Shoulder L"),
          (RW + "Gravis Techmarine Pad", "Shoulder Pads", "Pad R"), (SP + "mk6 studded", "Shoulder Pads", "Pad L"),
          (SP + "alt mk5 helmet v1", "Heads", "Neck"), (SP + "mk6 vox backpack", "Backpacks", "Back"),
          (SP + "augery scanner", "Accessories", "Hip R"), (SP + "gas mask", "Accessories", "Hip L")],
}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True); bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); n = 0
for i, (m, parts) in enumerate(MODELS.items()):
    for p, cat, sock in parts:
        r = {"schemaVersion": 1, "path": W + "/" + p + ".stl", "name": os.path.basename(p), "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": m}
        if sock: r["socket"] = sock
        else: r["at"] = [80 * i, 0, 0]
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
def bvh(o):
    me = o.data; return BVHTree.FromPolygons([o.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
def verts(o): return [o.matrix_world @ v.co for v in o.data.vertices]
def inside_depth(o, others):
    """closest approach to the others (mm) and the deepest cut (mm, sampled vertices inside another mesh by ray parity)."""
    trees = [bvh(x) for x in others]; V = verts(o)[::max(1, len(o.data.vertices) // 1500)]
    close = min(min((t.find_nearest(v)[3] or 9e9) for t in trees) for v in V)
    deep = 0.0; who = ""; where = None
    from mathutils import Vector
    D = [Vector(d).normalized() for d in ((0.0123, 0.0177, 1), (1, 0.031, -0.017), (-0.023, -1, 0.041))]
    def odd(t, v, d):
        k = 0; p = v.copy()
        for _ in range(12):
            h = t.ray_cast(p, d, 500)
            if h[0] is None: break
            k += 1; p = h[0] + d * 1e-4
        return k % 2
    for v in V:
        for t, x in zip(trees, others):
            # inside only if all three rays agree: one ray out through an open end (helmet neck, pad shell) is not a cut
            if all(odd(t, v, d) for d in D):
                dd = t.find_nearest(v)[3]
                if dd > deep: deep, who, where = dd, os.path.basename(x.get("tiow_src", x.name))[:30], o.matrix_world.inverted() @ v
    if deep > 0.65: print("        deepest in %s at part-local %s" % (who, tuple(round(c, 1) for c in where)))
    return close, deep
for m, parts in MODELS.items():
    mine = [o for o in obs if o.get("tiow_model") == m]
    names = [o.get("tiow_src", "") for o in mine]
    for p, cat, sock in parts:
        o = next((x for x in mine if os.path.basename(x.get("tiow_src", "")).startswith(os.path.basename(p))), None)
        ck("%s: %s placed%s" % (m, os.path.basename(p), (" on " + sock) if sock else ""), o is not None, names)
        if o is None or not sock or not (p.startswith(RW) or p.startswith(SP + "mk") or p.startswith(SP + "alt") or p.startswith(SP + "blank") or "pouch" in p or "grenade" in p or "scanner" in p or "mask" in p or p == TOR_RW):
            continue
        hosts = [x for x in mine if x is not o]
        if sock in ("Hip R", "Hip L", "Belt Back"):
            # belt bits are judged against the legs they hang on; a hanging arm reaching the hip is the pose, not the fit
            hosts = [x for x in hosts if x.get("tiow_category") == "Legs"]
        close, deep = inside_depth(o, hosts)
        print("      %-34s closest %.2f mm, deepest cut %.2f mm" % (os.path.basename(p)[:34], close, deep))
        ck("%s: %s touches (closest <= 0.5 mm)" % (m, os.path.basename(p)), close <= 0.5, close)
        ck("%s: %s cuts in <= 0.65 mm" % (m, os.path.basename(p)), deep <= 0.65, deep)
os.makedirs(OUTD, exist_ok=True)
sc = bpy.context.scene; rend.setup(sc, 520)
COL = {"Chests": rend.BLUE, "Legs": rend.GREY, "Arms": rend.GREY, "Shoulder Pads": rend.PURPLE, "Heads": rend.ORANGE, "Backpacks": rend.GREEN,
       "Accessories": rend.RED, "Grenades": rend.RED}
for m in MODELS:
    ms = [o for o in obs if o.get("tiow_model") == m]
    rend.render(sc, OUTD, m, ms, {"front": (0.35, 1, 0.25), "back": (-0.35, -1, 0.3), "right": (1, 0.2, 0.15), "left": (-1, 0.2, 0.15)}, [COL.get(o.get("tiow_category"), rend.GREY) for o in ms])
print("FAILS:", fails if fails else "none")
