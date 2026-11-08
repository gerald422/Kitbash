"""Render a grid of cells (each a list of (V, T, rgba)) in one Workbench render per view. Run under bpy."""
import bpy, numpy as np, math
from mathutils import Matrix, Vector
def _scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'; sc.display.shading.show_cavity = True
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.92, 0.92, 0.92)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 100000
    return sc, cam
def render(cells, out, views, cols=8, cell=None, px=220, labels=None, recentre=False):
    """views: {name: (dir to camera, up)} in cell coords. Cells laid out on the plane facing each view."""
    sc, cam = _scene()
    allv = np.vstack([V for c in cells for V, T, _ in c]); ctr = (allv.min(0) + allv.max(0)) / 2
    if recentre:     # each cell centred on its last item, everything further than half a cell cut away
        out_cells = []
        for c in cells:
            k = c[-1][0].mean(0); h = cell / 2
            cc = []
            for V, T, rgba in c:
                V = V - k; ok = (np.abs(V) < h).all(1); T2 = T[ok[T].all(1)]
                cc.append((V, T2, rgba))
            out_cells.append(cc)
        cells = out_cells; ctr = np.zeros(3)
    if cell is None:
        cell = 1.5 * max(float(np.ptp(np.vstack([V for V, T, _ in c]), axis=0).max()) for c in cells if c)
    cells = [[(V - ctr, T, rgba) for V, T, rgba in c] for c in cells]
    obs = []
    for i, c in enumerate(cells):
        for V, T, rgba in c:
            me = bpy.data.meshes.new("m"); me.from_pydata(V.tolist(), [], T.tolist()); me.update()
            o = bpy.data.objects.new("o", me); o.color = rgba; sc.collection.objects.link(o); obs.append((i, o))
    rows = (len(cells) + cols - 1) // cols
    files = []
    for vn, (d, up) in views.items():
        d = Vector(d).normalized(); u = Vector(up); y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        R = Matrix((x, y, d)).transposed()
        for i, o in obs:
            r, c = divmod(i, cols)
            off = x * (c * cell) - y * (r * cell)
            o.matrix_world = Matrix.Translation(off)
        centre = x * ((cols - 1) * cell / 2) - y * ((rows - 1) * cell / 2)
        cam.matrix_world = Matrix.LocRotScale(centre + d * 5000, R.to_quaternion(), None)
        cam.data.ortho_scale = max(cols, rows) * cell
        centre = centre
        sc.render.resolution_x = px * cols; sc.render.resolution_y = px * rows
        cam.data.sensor_fit = 'HORIZONTAL' if cols >= rows else 'VERTICAL'
        f = f"{out}_{vn}.png"; sc.render.filepath = f; bpy.ops.render.render(write_still=True); files.append(f)
    return files
