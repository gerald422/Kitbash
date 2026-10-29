exec(open("/home/claude/test/v17/common17.py").read())
prefs.bionic_dir = "/home/claude/test/v118/kit"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
select(legs); bpy.ops.tiow.bionic_leg(side='R')
def n_eval():
    dg = bpy.context.evaluated_depsgraph_get(); e = legs.evaluated_get(dg); me = e.to_mesh(); n = len(me.vertices); e.to_mesh_clear(); return n
print('base verts', len(legs.data.vertices))
print('with both', n_eval())
legs.modifiers["TIOW Bionic Tidy"].show_viewport = False; vl.update(); print('boolean only', n_eval())
legs.modifiers["TIOW Bionic Tidy"].show_viewport = True; legs.modifiers["TIOW Bionic Cut"].show_viewport = False; vl.update(); print('tidy only', n_eval())
coll = T._bio_cut_collection(legs); print('cutters', [(o.name, len(o.data.vertices), o.hide_get(), o.hide_viewport) for o in coll.objects])
tm = legs.modifiers["TIOW Bionic Tidy"]; print('tidy inputs', {k: tm[k] for k in tm.keys()})
legs.modifiers["TIOW Bionic Cut"].show_viewport = True
ng = tm.node_group
for n in ng.nodes: print(n.bl_idname, n.name, [ (i.name, getattr(i,'default_value',None)) for i in n.inputs if not i.is_linked][:4])
for o in coll.objects: o.hide_set(False)
vl.update(); print('cutters visible ->', n_eval())
for o in coll.objects: o.hide_set(True)
cmpn = [n for n in ng.nodes if n.bl_idname=='FunctionNodeCompare' and n.data_type=='FLOAT'][0]
cmpn.inputs[1].default_value = -1.0; vl.update(); print('far threshold -1 ->', n_eval())
cmpn.inputs[1].default_value = 1.5
