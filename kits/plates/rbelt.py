import bpy, sys, numpy as np, pickle, json
from mathutils import Matrix
sys.path.insert(0, '/home/claude/test'); import rend
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
mp = pickle.load(open('mfplate.pkl', 'rb')); BF = pickle.load(open('beltfront.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'; VW, TW = load(WP)
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
# arrow: cone out along Z (2.5 mm) + a stub along Y (up)
k = 12; t = np.linspace(0, 2 * np.pi, k, endpoint=False)
AV = 1.4 * np.vstack([np.c_[0.45 * np.cos(t), 0.45 * np.sin(t), np.zeros(k)], [[0, 0, 2.5]], np.c_[0.15 * np.cos(t), np.zeros(k), 0.15 * np.sin(t)], np.c_[0.15 * np.cos(t), np.full(k, 1.6), 0.15 * np.sin(t)]])
AT = [[i, (i + 1) % k, k] for i in range(k)] + [[k + 1 + i, k + 1 + (i + 1) % k, k + 1 + k + i] for i in range(k)] + [[k + 1 + (i + 1) % k, k + 1 + k + (i + 1) % k, k + 1 + k + i] for i in range(k)]
AT = np.array(AT)
bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene; rend.setup(scene, 1000)
GREEN, YEL = (0.2, 0.8, 0.3, 1), (0.95, 0.8, 0.2, 1)
jobs = [('1A', LD % '1A'), ('6A', LD % '6A'), ('3A L', LD % '3A L'), ('S2', LS % 2)]
for n, (a, path) in enumerate(jobs, 1):
    VA, TA = load(path + '.stl'); sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    obs = [mesh('legs', VA, TA, M)] + [mesh('plate' + s, VW, TW, M @ mp['res'][(a, s)]['W']) for s in 'RL']; cols = [rend.GREY, rend.BLUE, rend.BLUE]
    for t, A in BF[a].items():
        obs.append(mesh(t, AV, AT, M @ A)); cols.append(GREEN if t.startswith('Belt Front ') else YEL)
    rend.render(scene, '/home/claude/work/plates', 'b%d' % n, obs, {'front': (0.15, 1, 0.3), 'back': (0.2, -1, 0.3)}, cols)
    for o in obs: bpy.data.objects.remove(o)
