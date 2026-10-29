import bpy, sys, json, numpy as np
sys.path.insert(0, "/home/claude/test"); import rend
from mathutils import Matrix
L = "/mnt/user-data/uploads/d/Kitbash Library/"
idx = {p['name']: p for p in json.load(open(L + "_builder/index.json", encoding="utf-8"))['parts']}
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; rend.setup(sc, 600)
def load(name, mat):
    p = idx[name]; bpy.ops.wm.stl_import(filepath=L + p['path'].replace('\\', '/')); o = bpy.context.selected_objects[0]
    o.matrix_world = Matrix(np.array(mat, float).reshape(4, 4).tolist()); return o
pairs = [("Marta May 2026 - Legs 1", "base 40mm"), ("Marta May 2026 - Legs 1", "Base (IronFather)"), ("MarFil Assault - Legs 6A", "base 40mm"),
         ("MarFil Intercessor - Legs 10", "Base (IronFather)"), ("MarFil Intercessor - Legs 10", "Textured Base"), ("MarFil Assault - Legs 6A", "32_mm_1")]
for i, (lg, bn) in enumerate(pairs):
    S = np.array([s['m'] for s in idx[lg]['sockets'] if s['t'] == 'Base'][0]).reshape(4, 4)
    a = load(lg, np.linalg.inv(S).ravel()); b = load(bn, idx[bn]['fits']['Base'])
    rend.render(sc, "/home/claude/kits/basefix", f"pair{i}", [a, b], {"side": (1, 0.15, 0.05), "front": (0.15, -1, 0.05)}, [rend.GREY, rend.ORANGE], pad=1.0)
    for o in (a, b): bpy.data.objects.remove(o)
