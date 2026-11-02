"""Write each mesh object of a Blender 5 .blend as a binary STL (world coordinates), reading the file without Blender.
Meshes with more than THIN triangles are thinned by vertex clustering. python blend2stl.py file.blend outdir [thin_tris grid]"""
import sys, os, pathlib, struct, numpy as np
from blender_asset_tracer import blendfile
src, out = sys.argv[1], sys.argv[2]; THIN = int(sys.argv[3]) if len(sys.argv) > 3 else 1500000; GRID = float(sys.argv[4]) if len(sys.argv) > 4 else 0.06
os.makedirs(out, exist_ok=True)
bf = blendfile.open_cached(pathlib.Path(src))
def raw(blk): bf.fileobj.seek(blk.file_offset); return bf.fileobj.read(blk.size)
def deref(addr): return bf.block_from_addr.get(addr)
def cstr(addr):
    b = deref(addr); return raw(b).split(b'\0')[0].decode() if b else ''
SKIP = {'_bc_repeat', 'Bulge', 'Chamfered', 'Clip', 'Flat', 'Ribbed', 'Simple'}
only = set(sys.argv[5].split(',')) if len(sys.argv) > 5 else None
blocks = bf.blocks; pos = {id(b): i for i, b in enumerate(blocks)}
def local(me):
    """addr -> block among the DATA blocks written right after this ID (Blender 5 pointer ids repeat across IDs)"""
    i = pos[id(me)] + 1; L = {}
    while i < len(blocks) and blocks[i].code == b'DATA': L[blocks[i].addr_old] = blocks[i]; i += 1
    return L
for ob in bf.find_blocks_from_code(b'OB'):
    name = ob.id_name.decode()[2:]
    if ob.get(b'type') != 1 or name in SKIP or name.startswith(('Bolted', 'Flat.')) or (only and name not in only): continue
    me = ob.get_pointer(b'data'); nv, nl, npoly = me.get(b'totvert'), me.get(b'totloop'), me.get(b'totpoly'); L = local(me)
    n = me.get((b'attribute_storage', b'dna_attributes_num')); ap = me.get((b'attribute_storage', b'dna_attributes'), return_field=False) if False else None
    arr = [b for b in L.values() if b.dna_type.dna_type_id == b'Attribute'][0]; rb = raw(arr); A = {}
    for i in range(n):
        nm_p, dt, dom, st, dp = struct.unpack_from('<QhbB4xQ', rb, i * 24)
        if nm_p not in L or dp not in L: continue
        nm = raw(L[nm_p]).split(b'\0')[0].decode(); d = struct.unpack_from('<Q', raw(L[dp]), 0)[0]
        if d in L: A[nm] = L[d]
    P = np.frombuffer(raw(A['position']), np.float32)[:nv * 3].reshape(-1, 3).astype(np.float64)
    C = np.frombuffer(raw(A['.corner_vert']), np.int32)[:nl]
    po = [b for a_, b in L.items() if b.size == (npoly + 1) * 4 and b.dna_type.dna_type_id in (b'raw_data', b'int')]
    off = np.frombuffer(raw(po[-1]), np.int32)[:npoly + 1]
    assert off[0] == 0 and off[-1] == nl, (name, off[:3], off[-1], nl)
    sizes = np.diff(off); tris = []
    for k in np.unique(sizes):
        idx = off[:-1][sizes == k]
        for j in range(1, k - 1): tris.append(np.stack([C[idx], C[idx + j], C[idx + j + 1]], 1))
    T = np.concatenate(tris)
    if len(T) > THIN:
        key = np.floor(P / GRID).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
        cnt = np.bincount(inv); V2 = np.zeros((len(cnt), 3)); np.add.at(V2, inv, P); P = V2 / cnt[:, None]; T = inv[T]
        T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    loc = np.array([ob.get((b'loc', i)) for i in range(3)])
    P = P + loc                                          # every object here has no rotation/scale
    tri = P[T].astype(np.float32); nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(T), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])); rec['n'] = nrm; rec['v'] = tri
    with open(os.path.join(out, name + '.stl'), 'wb') as f: f.write(b'from captain blend'.ljust(80)); f.write(struct.pack('<I', len(T))); f.write(rec.tobytes())
    print('%-32s verts %8d tris %8d' % (name, nv, len(T)))
