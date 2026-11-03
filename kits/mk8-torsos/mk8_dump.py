import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/mk8/mk8.blend")
out={}
for o in bpy.data.objects:
    if o.type!='MESH': continue
    me=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    me.calc_loop_triangles()
    v=np.empty(len(me.vertices)*3,np.float32); me.vertices.foreach_get('co',v); v=v.reshape(-1,3)
    t=np.empty(len(me.loop_triangles)*3,np.int32); me.loop_triangles.foreach_get('vertices',t)
    M=np.array(o.matrix_world); v=v@M[:3,:3].T+M[:3,3]
    out[o.name+'|v']=v; out[o.name+'|t']=t.reshape(-1,3)
np.savez("/home/claude/work/mk8/mk8_meshes.npz",**out)
print(len(out)//2,"meshes")
