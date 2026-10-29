import bpy, time, resource, sys
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print('start %.0f MB' % rss())
O = bpy.data.objects
def test(host, cut, op, solver='MANIFOLD'):
    h = O[host]; c = O[cut]
    m = h.modifiers.new('t', 'BOOLEAN'); m.operation = op; m.object = c; m.solver = solver
    t = time.time(); deps = bpy.context.evaluated_depsgraph_get(); me = h.evaluated_get(deps).to_mesh()
    print('%-12s %-10s %-22s %-28s -> %7d faces %.1fs  maxrss %.0f MB' % (solver, op, host, cut, len(me.polygons), time.time() - t, rss()))
    h.evaluated_get(deps).to_mesh_clear(); h.modifiers.remove(m)
test('77-Arm-1-R-B', '63-ShoulderPad-2', 'UNION')
test('23-Torso-2', '77-Arm-1-R-B', 'DIFFERENCE')
test('23-Torso-2', '29-Legs-2', 'DIFFERENCE')
test('23-Torso-2', '1-Helmet-1', 'DIFFERENCE')
