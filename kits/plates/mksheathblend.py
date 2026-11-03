import bpy, numpy as np, pickle, json
from mathutils import Matrix
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
mp = pickle.load(open('/home/claude/work/plates/mfplate.pkl', 'rb')); hs = pickle.load(open('/home/claude/work/plates/holster_socket.pkl', 'rb')); FT = pickle.load(open('fits.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
SH = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/Accesory/220-SheatPistol-6.stl'
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
bpy.ops.wm.read_factory_settings(use_empty=True)
a = '4A'; VA, TA = load(LD % a + '.stl'); sc = json.load(open(LD % a + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
mesh('Legs 4A', VA, TA, M); VW, TW = load(WP)
for s in 'RL': mesh('WaistPlate ' + s, VW, TW, M @ mp['res'][(a, s)]['W'])
VH, TH = load(hs['hf']); h = mesh('VK holster (your approved spot, for reference)', VH, TH, M @ mp['res'][(a, 'L')]['W'] @ hs['S_wp'] @ hs['inv_fp']); h.hide_set(True)
P0 = M @ mp['res'][(a, 'L')]['W'] @ hs['S_wp'] @ hs['inv_fp'] @ FT['sheath_220-SheatPistol-6']
VS, TS = load(SH); Vw = VS @ P0[:3, :3].T + P0[:3, 3]; c = (Vw.min(0) + Vw.max(0)) / 2
T0 = np.eye(4); T0[:3, 3] = c; sh = mesh('Sheath (move me)', Vw - c, TS, T0)
for ob in bpy.data.objects: ob.select_set(ob == sh)
bpy.context.view_layer.objects.active = sh
pickle.dump({'P0': P0, 'c': c, 'M': M}, open('sheath_blend_ref.pkl', 'wb'))
bpy.context.scene.unit_settings.scale_length = 0.001; bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
bpy.ops.wm.save_as_mainfile(filepath='/mnt/user-data/outputs/plates-2026-11-03/sheath check 4A.blend', compress=True); print('saved')
