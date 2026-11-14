"""Write one of Josh's connectors (an open surface in his .blend, cut in place from a reference part) to a binary STL in
the reference part's own FILE coordinates: the object's mesh data, not its world placement. (Nov 14, notes 097: his
`legs.blend` object carries an 11.7 deg turn; its mesh data sits on Legs 1B exactly, its world placement 3.7 mm off.)
Connector STLs come from the maker's meshes: they never go in this repo.

    blender --background --factory-startup --python connector_export.py -- CONNECTOR.blend OBJECT OUT.stl
"""
import sys, struct
import bpy, bmesh
import numpy as np

blend, name, out = sys.argv[sys.argv.index("--") + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=blend); o = bpy.data.objects[name]
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces)
T = np.array([[list(v.co) for v in f.verts] for f in bm.faces]); bm.free()
with open(out, "wb") as f:
    f.write(b"\0" * 80); f.write(struct.pack("<I", len(T)))
    for t in T:
        n = np.cross(t[1] - t[0], t[2] - t[0]); l = np.linalg.norm(n); n = n / l if l else n
        f.write(struct.pack("<12fH", *n, *t.reshape(-1), 0))
print("connector_export: %s %s -> %s, %d triangles, object matrix identity: %s" % (
    blend, name, out, len(T), bool(np.allclose(np.array(o.matrix_world), np.eye(4), atol=1e-6))))
