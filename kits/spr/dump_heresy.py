import bpy, json, numpy as np
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/actual.blend", load_ui=False)
out = {}; arrs = {}
for ob in bpy.data.objects:
    cols = [c.name for c in ob.users_collection]
    if ob.type == 'MESH' and ('HeresyArms_r' in cols or 'WS_import_heresey legs' in cols):
        me = ob.data; n = len(me.vertices); co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co)
        k = 'm%d' % len(arrs); arrs[k] = co.reshape(-1, 3)
        out[ob.name] = dict(key=k, coll=cols, mw=[list(r) for r in ob.matrix_world], parent=ob.parent.name if ob.parent else None,
                            props={kk: (str(ob[kk]))[:80] for kk in ob.keys()}, cons=[c.type for c in ob.constraints], mesh=me.name)
    if ob.type == 'EMPTY' and ob.get('ws_type') in ('HeresyArms_r', 'arm__Torso_r'):
        out['SOCK:' + ob.name] = dict(mw=[list(r) for r in ob.matrix_world], parent=ob.parent.name if ob.parent else None, type=ob.get('ws_type'))
np.savez_compressed('/home/claude/kits/spr/heresy.npz', **arrs)
json.dump(out, open('/home/claude/kits/spr/heresy.json', 'w'), indent=0)
print('objects', len(out))
