"""Render an assembly: JSON [{"src": stl or npz path, "M": 16 floats (world), "color": [r,g,b,a]}] + views."""
import bpy, sys, json, os, numpy as np
from mathutils import Matrix
sys.path.insert(0, "/home/claude/test"); import rend
spec = json.load(open(sys.argv[sys.argv.index('--') + 1]))
out = spec['out']; os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; rend.setup(scene, spec.get('res', 700))
obs, cols = [], []
for i, p in enumerate(spec['parts']):
    src = p['src']
    if src.endswith('.npz'):
        d = np.load(src); V, F = d['V'], d['F']
        me = bpy.data.meshes.new('m%d' % i)
        me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
        me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel())
        me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', np.arange(0, F.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(F), 3))
        me.update(); ob = bpy.data.objects.new('o%d' % i, me); scene.collection.objects.link(ob)
    else:
        before = set(bpy.data.objects); bpy.ops.wm.stl_import(filepath=src); ob = [o for o in bpy.data.objects if o not in before][0]
    M = np.array(p['M']).reshape(4, 4)
    if np.linalg.det(M[:3, :3]) < 0:
        ob.data.transform(Matrix(M.tolist())); ob.data.flip_normals(); ob.matrix_world = Matrix.Identity(4)
    else:
        ob.matrix_world = Matrix(M.tolist())
    obs.append(ob); cols.append(tuple(p.get('color', rend.GREY)))
views = spec.get('views', {"front": (0.15, 1, 0.1), "side": (1, 0.1, 0.05), "back": (-0.3, -1, 0.2), "top": (0.1, 0.3, 1)})
files = rend.render(scene, os.path.dirname(out), os.path.basename(out), obs, views, cols, pad=spec.get('pad', 1.05))
print(json.dumps(files))
