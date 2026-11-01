"""Josh's marine in base_jumpack.blend: the right wing (Wing01 Open), left wing (Wing03 Upwards) and both connectors as
point clouds in the TN Mk6 Universal pack's own file coordinates (his pack is enlarged; this takes it out).
python josh_points.py -- BLEND PACK_STL OUT_NPZ"""
import bpy, sys, struct
import numpy as np
BLEND, PACK, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.wm.open_mainfile(filepath=BLEND)
O = bpy.data.objects


def world(o):
    a = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", a); V = a.reshape(-1, 3)
    M = np.array(o.matrix_world); return V @ M[:3, :3].T + M[:3, 3]


b = open(PACK, "rb").read(); n = struct.unpack_from("<I", b, 80)[0]
S = np.frombuffer(b, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), count=n, offset=84)["v"].reshape(-1, 3)
pk = O["Mk6_Jumppack_Universal.001"]
a = np.empty(len(pk.data.vertices) * 3); pk.data.vertices.foreach_get("co", a); D = a.reshape(-1, 3)
t = S.min(0) - D.min(0)                          # the pack's mesh is its file moved (registered exactly: translation only)
G = np.array(pk.matrix_world) @ np.block([[np.eye(3), (-t)[:, None]], [np.zeros((1, 3)), np.ones((1, 1))]])
Gi = np.linalg.inv(G)
out = {}
for k, n_ in (("wingR", "Wing01_OpenR_AppliedMods.003"), ("wingL", "Wing03_UpwardsR.003"),
              ("mountL", "Backpack Connector - Arm 2 Joint.004"), ("mountR", "Backpack Connector - Arm 2 Joint.005")):
    W = world(O[n_]); out[k] = W @ Gi[:3, :3].T + Gi[:3, 3]
np.savez(OUT, **out)
print({k: v.shape for k, v in out.items()})
