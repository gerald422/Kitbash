import bpy, numpy as np, pickle, json
from mathutils import Matrix
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
mp = pickle.load(open('mfplate.pkl', 'rb')); BS = pickle.load(open('buckle_sockets.pkl', 'rb'))
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
bpy.ops.wm.read_factory_settings(use_empty=True)
a = '8A'; VA, TA = load(LD % a + '.stl'); sc = json.load(open(LD % a + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
mesh('Legs 8A', VA, TA, M)
VB, TB = load('/mnt/user-data/uploads/Desktop/buckle.stl'); P0 = M @ BS['pose'][a]
Vw = VB @ P0[:3, :3].T + P0[:3, 3]; c = (Vw.min(0) + Vw.max(0)) / 2; T0 = np.eye(4); T0[:3, 3] = c
b = mesh('Buckle (move me)', Vw - c, TB, T0)
for ob in bpy.data.objects: ob.select_set(ob == b)
bpy.context.view_layer.objects.active = b
pickle.dump({'P0': P0, 'c': c, 'M': M}, open('buckle8a_ref.pkl', 'wb'))
bpy.context.scene.unit_settings.scale_length = 0.001; bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
bpy.ops.wm.save_as_mainfile(filepath='/mnt/user-data/outputs/plates-2026-11-03/buckle 8A.blend', compress=True); print('saved')
