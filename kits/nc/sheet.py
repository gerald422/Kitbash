"""Contact sheets of the decimated parts: per part a front (-Y) and a side (+X) and top (+Z) view, labelled."""
import bpy, sys, os, glob, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "/home/claude/test"); import rend
import json
NPZ = "/home/claude/kits/nc/npz"; OUT = "/home/claude/kits/nc/sheets"; TMP = "/tmp/claude-0/sheet"
os.makedirs(TMP, exist_ok=True)
groups = {}
for f in sorted(glob.glob(NPZ + "/*.npz")):
    n = os.path.basename(f)[:-4].split('__')
    groups.setdefault('__'.join(n[:-1]), []).append(f)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; rend.setup(scene, 300)
def mesh(f):
    d = np.load(f); V, F = d['V'], d['F']
    me = bpy.data.meshes.new(os.path.basename(f))
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel())
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', np.arange(0, F.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(F), 3))
    me.update(); ob = bpy.data.objects.new(me.name, me); scene.collection.objects.link(ob); return ob, V
meta = {}
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for g, files in groups.items():
    if only and not any(o in g for o in only): continue
    for f in files:
        ob, V = mesh(f)
        lo, hi = V.min(0), V.max(0)
        gd = TMP + '/' + g.replace(' ', '_'); os.makedirs(gd, exist_ok=True)
        nm = os.path.basename(f)[len(g) + 2:-4]
        fs = rend.render(scene, gd, nm.replace(' ', '_'), [ob], {"front": (0, -1, 0), "side": (1, 0, 0), "top": (0, 0, 1)}, [rend.GREY])
        meta.setdefault(g, []).append([nm, fs, [float(x) for x in lo], [float(x) for x in hi]])
        bpy.data.objects.remove(ob); bpy.data.meshes.remove(bpy.data.meshes[os.path.basename(f)])
    print(g, len(files))
json.dump(meta, open(TMP + '/meta.json', 'w'))
