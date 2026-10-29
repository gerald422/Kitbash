import bpy, numpy as np, struct, os, csv
bpy.ops.wm.open_mainfile(filepath="/home/claude/blend/actual.blend", load_ui=False)
R='/home/claude/liblift_actual'
rows={r['object']:r for r in csv.DictReader(open(f'{R}/_lift_report_3rd attempt finalising actual.csv'))}
def vol_tris(t): return np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
def raw(ob):
    me=ob.data; me.calc_loop_triangles(); n=len(me.loop_triangles)
    vi=np.empty(n*3,np.int32); me.loop_triangles.foreach_get("vertices",vi)
    co=np.empty(len(me.vertices)*3,np.float64); me.vertices.foreach_get("co",co)
    return co.reshape(-1,3)[vi.reshape(-1,3)]
def world(ob):
    t=raw(ob); M=np.array(ob.matrix_world); w=t.reshape(-1,3)@M[:3,:3].T+M[:3,3]; return w.reshape(-1,3,3)
def stl(p):
    b=open(p,'rb').read(); n=struct.unpack_from('<I',b,80)[0]
    return np.frombuffer(b,dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]),count=n,offset=84)['v'].reshape(-1,3,3).astype(np.float64)
for name in ['151-PowerAxe-2-2-B','Wing01_OpenR_AppliedMods.002','2','AntebrazoCable-Union']:
    ob=bpy.data.objects.get(name)
    if ob is None or name not in rows: print(name,'missing'); continue
    p=os.path.join(R,*rows[name]['library path'].split('/'))
    t=stl(p); w=world(ob)
    # world-space shape should equal exported shape moved by the part frame
    loc,rot,sc=ob.matrix_world.decompose()
    F=np.array(bpy.types.Object.bl_rna and __import__('mathutils').Matrix.LocRotScale(loc,rot,__import__('mathutils').Vector((1,1,1))))
    tw=(t.reshape(-1,3)@F[:3,:3].T+F[:3,3]).reshape(-1,3,3)
    same_shape=np.allclose(np.sort(tw.reshape(-1,3),axis=0),np.sort(w.reshape(-1,3),axis=0),atol=2e-3)
    print(f"{name:32s} raw vol {vol_tris(raw(ob)):9.2f}  world vol {vol_tris(w):9.2f}  exported vol {vol_tris(t):9.2f}  exported==what you see: {same_shape}")
