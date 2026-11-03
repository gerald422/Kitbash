import bpy, sys, numpy as np, pickle, json
from mathutils import Matrix
sys.path.insert(0, '/home/claude/test'); import rend
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
mp = pickle.load(open('/home/claude/work/plates/mfplate.pkl', 'rb')); hs = pickle.load(open('/home/claude/work/plates/holster_socket.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
VW, TW = load(WP); VH, TH = load(hs['hf'])
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene; rend.setup(scene, 420)
RED = (0.85, 0.3, 0.3, 1)
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
jobs = [('S%d' % n, LS % n) for n in range(1, 6)] + [('%dA L' % n, LD % ('%dA L' % n)) for n in (2, 3, 4)]
for n, (a, path) in enumerate(jobs, 1):
    VA, TA = load(path + '.stl'); sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    obs = [mesh('legs', VA, TA, M)] + [mesh('plate' + s, VW, TW, M @ mp['res'][(a, s)]['W']) for s in 'RL']
    obs.append(mesh('hol', VH, TH, M @ mp['res'][(a, 'L')]['W'] @ hs['S_wp'] @ hs['inv_fp']))
    rend.render(scene, '/home/claude/work/plates', 'r%d' % n, obs, {'left': (-1, 0.1, 0.2), 'backleft': (-0.6, -1, 0.25)}, [rend.GREY, rend.BLUE, rend.BLUE, RED])
    for o in obs: bpy.data.objects.remove(o)
