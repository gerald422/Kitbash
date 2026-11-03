import bpy, sys, numpy as np, pickle, json
from mathutils import Matrix
sys.path.insert(0, '/home/claude/test'); import rend
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
mp = pickle.load(open('/home/claude/work/plates/mfplate.pkl', 'rb')); hs = pickle.load(open('/home/claude/work/plates/holster_socket.pkl', 'rb'))
BF = pickle.load(open('/home/claude/work/plates/beltfront.pkl', 'rb')); BK = pickle.load(open('/home/claude/work/plates/buckle_final.pkl', 'rb')); FT = pickle.load(open('fits.pkl', 'rb')); BS = pickle.load(open('/home/claude/work/plates/buckle_sockets.pkl', 'rb')); VB, TB = load('/mnt/user-data/uploads/Desktop/buckle.stl'); TRS = pickle.load(open('/home/claude/work/plates/trophy_spots.pkl', 'rb')); SF = pickle.load(open('sheath_fit.pkl', 'rb'))['fit_on_plate_socket']
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'; VW, TW = load(WP)
CBL = '/mnt/user-data/uploads/d/Kitbash Library/CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Loinclothes/Accessories/CyberBrush Bug Hunters - Loinclothe %d'
CBD = '/mnt/user-data/uploads/d/Kitbash Library/CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Belt Decorations/Accessories/CyberBrush Bug Hunters - Belt Decoration %d.stl'
SH = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/Accesory/%s.stl'
def mesh(name, V, T, Mw):
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(T.size); me.loops.foreach_set('vertex_index', T.ravel()); me.polygons.add(len(T))
    me.polygons.foreach_set('loop_start', np.arange(0, T.size, 3)); me.polygons.foreach_set('loop_total', np.full(len(T), 3)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(Mw.tolist()); return ob
def tf(P, M): return P @ M[:3, :3].T + M[:3, 3]
def settle(Pi, Wi, A, tree, S, N):
    """slide the part along the anchor's Z until it just touches the legs (signed distance by nearest-sample normal)"""
    z = A[:3, 2]; best = 0; X0 = tf(Pi, Wi); X0 = X0[np.abs((X0 - A[:3, 3]) @ A[:3, 1]) < 3.0]     # only the top band of the part (like TIOW's settle on the belt)
    for t in np.arange(3.0, -3.01, -0.05):
        X = X0 + z * t; d, j = tree.query(X); sd = ((X - S[j]) * N[j]).sum(1)
        if (sd[d < 0.6] < -0.1).mean() > 0.002: break
        best = t
    T = np.eye(4); T[:3, 3] = z * best; return T @ Wi, best
bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene; rend.setup(scene, 1100)
RED, GREEN, ORANGE, PURPLE = (0.85, 0.3, 0.3, 1), (0.3, 0.75, 0.35, 1), (0.95, 0.6, 0.2, 1), (0.6, 0.45, 0.85, 1)
jobs = [('4A', LD % '4A', 1, (1, 3), '220-SheatPistol-6'), ('6A', LD % '6A', 2, (4, 5), '215-SheatPistol-1'), ('8A', LD % '8A', 4, (6, 7), '217-SheatPistol-3'), ('S2', LS % 2, 5, (8, 9), '219-SheatPistol-5')]
for n, (a, path, loin, (tr1, tr2), sh) in enumerate(jobs, 1):
    VA, TA = load(path + '.stl'); sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    from scipy.spatial import cKDTree
    Aw = VA[TA]; c = np.cross(Aw[:, 1] - Aw[:, 0], Aw[:, 2] - Aw[:, 0]); ar = np.linalg.norm(c, axis=1); rng = np.random.default_rng(0)
    i = rng.choice(len(TA), 300000, p=ar / ar.sum()); u, w = rng.random(300000), rng.random(300000); f = u + w > 1; u[f], w[f] = 1 - u[f], 1 - w[f]
    S = tf(Aw[i, 0] + (Aw[i, 1] - Aw[i, 0]) * u[:, None] + (Aw[i, 2] - Aw[i, 0]) * w[:, None], M); N = (c[i] / ar[i, None]) @ M[:3, :3].T; tree = cKDTree(S)
    obs = [mesh('legs', VA, TA, M)] + [mesh('plate' + s, VW, TW, M @ mp['res'][(a, s)]['W']) for s in 'RL']; cols = [rend.GREY, rend.BLUE, rend.BLUE]
    # tabard on the buckle spot (its Belt Front fit), settled like TIOW
    VL, TL = load(CBL % loin + '.stl'); fit = M16(json.load(open(CBL % loin + '.sockets.json'))['fits']['Belt Front'])
    obs.append(mesh('buckle', VB, TB, M @ BS['pose'][a])); cols.append(PURPLE)
    A = M @ BS['pose'][a] @ BS['TAB']; Wl, t = settle(samples(VL, TL, 20000), A @ fit, A, tree, S, N); print(a, 'tabard %d settled %.2f mm along the buckle spot' % (loin, t))
    obs.append(mesh('tabard', VL, TL, Wl)); cols.append(GREEN)
    for spot, k in (('Belt Front R', tr1), ('Belt Front L', tr2)):
        VD, TD = load(CBD % k); obs.append(mesh('trophy', VD, TD, M @ TRS[a][spot] @ FT['trophy %d' % k])); cols.append(ORANGE)
    VS, TS = load(SH % sh); obs.append(mesh('sheath', VS, TS, M @ mp['res'][(a, 'L')]['W'] @ hs['S_wp'] @ SF)); cols.append(RED)
    rend.render(scene, '/home/claude/work/acc', 'z%d' % n, obs, {'front': (0.0, 1, 0.2), 'frontleft': (-0.9, 1, 0.2), 'left': (-1, 0.05, 0.15), 'backleft': (-0.6, -1, 0.2)}, cols)
    for o in obs: bpy.data.objects.remove(o)
