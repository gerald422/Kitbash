import bpy, sys, numpy as np, pickle, json
from mathutils import Matrix
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
out = pickle.load(open('/home/claude/work/plates/plates.pkl', 'rb')); mp = pickle.load(open('/home/claude/work/plates/mfplate.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
bpy.ops.wm.read_factory_settings(use_empty=True)
a = '4A'; VA, TA = load(LD % a + '.stl'); sc = json.load(open(LD % a + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
mesh('Legs 4A', VA, TA, M)
VW, TW = load(WP)
for s in 'RL': mesh('WaistPlate ' + s, VW, TW, M @ mp['res'][(a, s)]['W'])
inv_fp, hf = mp['hol']['back (V1/V2/V4)']; VH, TH = load(hf)
P0 = M @ out[a]['L']['F'] @ inv_fp
hang = (M @ out[a]['L']['F'] @ np.r_[np.asarray(mp['hang_vk']).ravel()[:3], 1])[:3]
Vb = VH @ P0[:3, :3].T + P0[:3, 3] - hang
T0 = np.eye(4); T0[:3, 3] = hang
h = mesh('Holster', Vb, TH, T0)
pickle.dump({'P0': P0, 'hang': hang, 'MF': M @ out[a]['L']['F'], 'hf': hf}, open('/home/claude/work/plates/holster_blend_ref.pkl', 'wb'))
bpy.context.scene.unit_settings.scale_length = 0.001; bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
for ob in bpy.data.objects: ob.select_set(ob.name == 'Holster')
bpy.context.view_layer.objects.active = h
bpy.ops.wm.save_as_mainfile(filepath='/mnt/user-data/outputs/plates-2026-11-03/holster check 4A.blend', compress=True)
print('saved', np.round(hang, 3).tolist())
