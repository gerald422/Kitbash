import bpy, numpy as np, pickle, json
from mathutils import Matrix
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
NB = pickle.load(open('buckle_anchor2.pkl', 'rb'))
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
bpy.ops.wm.read_factory_settings(use_empty=True)
ref = {}
for i, (a, path, lab) in enumerate([('S2', LS % 2, 'Standing 2 (reference, correct)'), ('6A', LD % '6A', '6A'), ('8A', LD % '8A', '8A'), ('S3', LS % 3, 'Standing 3')]):
    sc = json.load(open(path + '.sockets.json')); O = np.eye(4); O[0, 3] = 40 * i; M = O @ S_WAIST @ M16(sc['fits']['Waist'])
    V, T = load(path + '.stl'); mesh('Legs ' + lab, V, T, M)
    e = bpy.data.objects.new('Buckle ' + lab, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = 3
    bpy.context.scene.collection.objects.link(e); e.matrix_world = Matrix((M @ NB[a]).tolist()); ref[e.name] = (a, M)
pickle.dump(ref, open('buckle_blend_ref.pkl', 'wb'))
bpy.context.scene.unit_settings.scale_length = 0.001; bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
bpy.ops.wm.save_as_mainfile(filepath='/mnt/user-data/outputs/plates-2026-11-03/buckle check.blend', compress=True); print('saved')
