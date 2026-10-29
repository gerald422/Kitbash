"""A marine with a bionic right leg through Kitbash Finalise 0.3.2: the bionic leg is its own piece (thigh +
shin + foot), no peg (it plugs onto the ball), the plug part of the body, the cut applied; pieces manifold."""
exec(open("/home/claude/test/v17/common17.py").read())
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
prefs.bionic_dir = "/home/claude/test/v118/kit"
OUT = "/home/claude/test/v118/out"
select(None); torso = send(f"{AM}/Chest/24-Torso-3.stl", "Chests", (0, 0, 0))
select(torso); legs = send(f"{AM}/Legs/29-Legs-2.stl", "Legs")
select(torso); send(f"{AM}/Arms/106-Arm-7-R-A.stl", "Arms")
select(legs); bpy.ops.tiow.bionic_leg(side='R'); vl.update()
P = T.bio_parts(legs, "R")
select(torso)
ctx = bpy.context
root, parts = KF.FA_OT_finalise._scan(None, ctx)
items = {it.part: it for it in ctx.window_manager.fa_items}
bad = [b.part for b in ctx.window_manager.fa_bad]
print("items", [(k, it.split, it.peg, it.depth) for k, it in items.items()]); print("non-manifold", bad)
th = items.get(P["thigh"].name)
ck("bionic thigh listed, prints apart, no peg", th is not None and th.split and not th.peg, th and (th.split, th.peg))
ck("shin and foot ride with the thigh (not split)", all(n in items and not items[n].split for n in (P["shin"].name, P["foot"].name)))
ck("plug part of the legs (not split)", P["plug"].name in items and not items[P["plug"].name].split)
ck("cutters, joints not parts", not any(n.startswith("Bionic Cut") or n.startswith("Bionic Knee") for n in items))
for it in ctx.window_manager.fa_items:
    if it.part != P["thigh"].name: it.split = False
t = time.time()
r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, use_exact=bool(bad), ident='B')
print(f"      [{time.time() - t:4.1f}s] finalise", r); print(scene.fa_last_log)
ck("finalise ran", r == {'FINISHED'})
ctrl = [o for o in bpy.data.objects if o.get('fa_role') == 'ctrl']
ck("kit parts clean (nothing for Exact)", not bad, bad)
ck("no peg on the bionic joint", not [o for o in bpy.data.objects if o.get('fa_role') in ('peg', 'cavity')],
   [(o.name, o.get('fa_role')) for o in bpy.data.objects if o.get('fa_role') in ('peg', 'cavity', 'ctrl')])
t = time.time(); bpy.ops.fa.apply('EXEC_DEFAULT'); print(f"      [{time.time() - t:4.1f}s] apply"); print(scene.fa_last_log)
pcs = [o for o in bpy.data.objects if o.get('fa_role') == 'piece']
print("pieces", [(o.name, len(o.data.vertices)) for o in pcs])
ck("two pieces: the body and the bionic leg", len(pcs) == 2, [o.name for o in pcs])
ck("both manifold", scene.fa_last_log.count(": manifold") == 2, scene.fa_last_log)
rend.setup(scene, 700)
rend.render(scene, OUT, "fa_pieces", pcs, {"front": (0.3, 1, 0.1), "side": (1, 0.2, 0.1), "below": (0.4, 0.5, -0.7)}, [rend.GREY, rend.BLUE])
print("FAILS:", fails)
