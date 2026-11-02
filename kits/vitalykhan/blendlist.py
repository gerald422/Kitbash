import sys, pathlib, json, numpy as np
from blender_asset_tracer import blendfile
bf = blendfile.open_cached(pathlib.Path(sys.argv[1]))
obs = []
for b in bf.find_blocks_from_code(b'OB'):
    name = b.id_name.decode('utf8', 'replace')[2:]
    try: M = np.array(b.get(b'object_to_world') if b.dna_type.has_field(b'object_to_world') else b.get(b'obmat'), float)
    except Exception: M = None
    try:
        M = np.array([[b.get((b'runtime', b'object_to_world', b'ptr', i, j)) if False else 0 for j in range(4)] for i in range(4)])
    except Exception: pass
    loc = [b.get((b'loc', i)) for i in range(3)]; rot = [b.get((b'rot', i)) for i in range(3)]; sc = [b.get((b'size', i)) for i in range(3)]
    data = b.get_pointer(b'data'); dname = data.id_name.decode('utf8', 'replace')[2:] if data is not None else None
    par = b.get_pointer(b'parent'); pname = par.id_name.decode()[2:] if par is not None else None
    nv = None
    if data is not None and data.code == b'ME':
        try: nv = data.get(b'verts_num')
        except Exception:
            try: nv = data.get(b'totvert')
            except Exception: nv = None
    obs.append(dict(name=name, type=b.get(b'type'), data=dname, parent=pname, loc=[round(x, 3) for x in loc], rot=[round(x, 3) for x in rot], scale=[round(x, 4) for x in sc], verts=nv))
cols = []
for b in bf.find_blocks_from_code(b'GR'):
    cols.append(b.id_name.decode('utf8', 'replace')[2:])
json.dump(dict(objects=obs, collections=cols), open('captain_objects.json', 'w'), indent=0)
print(len(obs), 'objects;', 'collections:', cols)
for o in obs: print('%-45s t%-2s v%-8s par %-15s loc %s rot %s sc %s' % (o['name'][:45], o['type'], o['verts'], (o['parent'] or '')[:15], o['loc'], o['rot'], o['scale']))
