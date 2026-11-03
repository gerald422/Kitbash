import bpy, sys, numpy as np, pickle, json
from mathutils import Matrix
sys.path.insert(0, '/home/claude/test'); import rend
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
mp = pickle.load(open('/home/claude/work/plates/mfplate.pkl', 'rb')); BS = pickle.load(open('/home/claude/work/plates/buckle_sockets.pkl', 'rb')); TF = pickle.load(open('tab_fits.pkl', 'rb'))
VB, TB = load('/mnt/user-data/uploads/Desktop/buckle.stl'); WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'; VW, TW = load(WP)
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
CBL = '/mnt/user-data/uploads/d/Kitbash Library/CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Loinclothes/Accessories/CyberBrush Bug Hunters - Loinclothe %d'
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene; rend.setup(scene, 800)
TABS = {n: load(CBL % n + '.stl') for n in TF}
for i, (a, path) in enumerate([('4A', LD % '4A'), ('6A', LD % '6A'), ('8A', LD % '8A'), ('S2', LS % 2)]):
    VA, TA = load(path + '.stl'); sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    base = [mesh('legs', VA, TA, M), mesh('buckle', VB, TB, M @ BS['pose'][a])] + [mesh('plate', VW, TW, M @ mp['res'][(a, s)]['W']) for s in 'RL']
    for n, (VL, TL) in TABS.items():
        k = TF[n]['scale']; t = mesh('tab', VL, TL, M @ BS['pose'][a] @ BS['TAB'] @ TF[n]['fit'] @ np.diag([k, k, k, 1.0]))
        rend.render(scene, '/home/claude/work/acc', 'q%s_%d' % (a, n), base + [t], {'front': (0.0, 1, 0.2), 'side': (-1, 0.15, 0.1)}, [rend.GREY, (0.6, 0.45, 0.85, 1), rend.BLUE, rend.BLUE, (0.3, 0.75, 0.35, 1)])
        bpy.data.objects.remove(t)
    for o in base: bpy.data.objects.remove(o)
