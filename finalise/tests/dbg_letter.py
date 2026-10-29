import bpy, sys, numpy as np
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
ctx = bpy.context; deps = ctx.evaluated_depsgraph_get()
O = bpy.data.objects
body = KF.Ray(O['23-Torso-2'], deps)
for pn in ['77-Arm-1-R-B', '78-Arm-1-L-A', '55-JumpPack-1', '1-Helmet-1', '29-Legs-2']:
    s = O[pn]; piece = KF.Ray(s, deps)
    pc = s.matrix_world @ (sum((Vector(v) for v in s.bound_box), Vector()) / 8.0)
    frame, how, pts, nrs = KF.joint_frame(KF.joint_socket(s), body, piece, pc)
    z = Vector((frame[0][2], frame[1][2], frame[2][2])); o = frame.translation
    rel = pts - np.array(o); ax = rel @ np.array(z); rad = rel - np.outer(ax, np.array(z)); rd = np.linalg.norm(rad, axis=1)
    print(pn, how, 'origin', np.round(o, 2), 'z', np.round(z, 2), 'contact radial max %.2f q90 %.2f' % (rd.max(), np.quantile(rd, 0.9)), 'axial spread %.2f..%.2f' % (ax.min(), ax.max()))
    # sample the face pair at a few radii in 8 directions
    x0 = Vector((frame[0][0], frame[1][0], frame[2][0])); y0 = z.cross(x0)
    for rr in (1.8, 2.2, 2.6, 3.2):
        row = []
        for k in range(8):
            a = np.radians(45 * k); q = o + (x0 * np.cos(a) + y0 * np.sin(a)) * rr
            b = body.cast(q + z * 0.6, -z, 1.2); p = piece.cast(q - z * 0.6, z, 1.2)
            row.append(('b%.2f' % (b[1].dot(z)) if b else 'b-') + '/' + ('p%.2f' % (p[1].dot(z)) if p else 'p-') + ('' if not (b and p) else ' d%.2f' % ((p[0] - b[0]).dot(z))))
        print('   r %.1f' % rr, ' | '.join(row))
