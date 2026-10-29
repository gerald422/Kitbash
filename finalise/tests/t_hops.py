"""Hard Ops path: HOps' real add() with a stand-in for its preferences (HOps can't register without a GPU)."""
import bpy, sys, types, time
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import addon_utils
addon_utils.enable("bl_ext.user_default.hardops", default_set=False, handle_error=lambda e: None)
import kitbash_finalise as KF
hb = KF.hops_bool(); ha = KF.hops_addon()
print('hops modules', hb is not None, ha is not None)
class HopsObj(bpy.types.PropertyGroup):
    status: bpy.props.StringProperty(default="UNDEFINED")
bpy.utils.register_class(HopsObj)
if not hasattr(bpy.types.Object, 'hops'):
    bpy.types.Object.hops = bpy.props.PointerProperty(type=HopsObj)
class HopsScene(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)
bpy.utils.register_class(HopsScene)
bpy.types.Scene.hops = bpy.props.PointerProperty(type=HopsScene)
class HopsMat(bpy.types.PropertyGroup):
    material_mode: bpy.props.StringProperty(default='MATERIAL')
    active_material: bpy.props.StringProperty(default='')
    color_prob: bpy.props.FloatProperty(default=0.5)
bpy.utils.register_class(HopsMat)
bpy.types.WindowManager.Hard_Ops_material_options = bpy.props.PointerProperty(type=HopsMat)
class NS(types.SimpleNamespace):
    def __getattr__(self, k): return False
prop = NS(boolean_solver='FLOAT', sort_modifiers=True, workflow='DESTRUCTIVE', workflow_modifier='MODIFIER', workflow_mode='ANGLE')
pref = NS(property=prop, behavior=NS(auto_smooth=False), color=NS(colection_color='COLOR_01'), ui=NS())
ha.preference = lambda: pref
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
ctx = bpy.context; scene = ctx.scene; vl = ctx.view_layer
if not hasattr(bpy.types.Object, 'hops'):
    bpy.types.Object.hops = bpy.props.PointerProperty(type=HopsObj)
scene.ws_conn_shape = 'LONG'
bpy.data.objects.remove(bpy.data.objects['Weapons-Assault211-BoltPistol-L'])
torso = bpy.data.objects['23-Torso-2']
for o in vl.objects: o.select_set(False)
torso.select_set(True); vl.objects.active = torso
root, parts = KF.FA_OT_finalise._scan(None, ctx)
for it in ctx.window_manager.fa_items: it.split = it.part in {'77-Arm-1-R-B', '1-Helmet-1'}
try:
    r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True)
except Exception as e:
    import traceback; traceback.print_exc(); r = None
print('finalise', r); print(scene.fa_last_log)
print('hops prefs restored:', prop.boolean_solver, prop.workflow)
for h in [o for o in bpy.data.objects if o.get('fa_role') == 'host']:
    print('  %-22s' % h.name, [(m.name, m.operation[:3], m.solver[:3], m.show_viewport, m.object.name[:20]) for m in h.modifiers])
cut = bpy.data.collections.get('Cutters'); print('Cutters collection:', cut and len(cut.objects))
r = bpy.ops.fa.apply('EXEC_DEFAULT'); print('apply', r); print(scene.fa_last_log)
print('left over:', [o.name for o in bpy.data.objects if o.get('fa_build') and o.get('fa_role') != 'piece'])
