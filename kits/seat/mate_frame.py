"""A part's mating origin, from the shape of its mating surface, not from where the maker exported it (Nov 27).

    BL kits/seat/mate_frame.py -- test BATCH.blend OUT.json     (pauldrons: against the inner-surface carry)
  BL = blender --background --factory-startup --python

Josh: fits carry wrongly where each STL's origin is somewhere else (Mar Fil works: a pack shares one); he wants a
consistent origin for parts hung off a host (pauldrons, shin pads, wrist armour). Part Sockets' Set Origin at Flat
puts it at the area centre of the flat with +Z out of it, roll arbitrary (from the world axes). Here, the same rule on
the mating surface (a flat, or a pauldron's inner surface: `carry_by_shape.inner`), plus the spin from the surface's
outline: its long direction (principal axis of the area, in the plane across +Z), the end picked by where more of the
area lies (third moment). Too round (axes within RATIO) or too even (SKEW) to pick: flagged, never guessed.

test: every pauldron carried by inner surface in the batch (kb_applied) against the seat it was carried from: the
seat's mating frame, put on this one through both mating frames, should land where the inner surface match did."""
import os, sys, json, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import geom as G, batch as B, carry_by_shape as CS

RATIO, SKEW = 1.15, 0.05


def frame_of(T):
    """mating frame (4x4, own coordinates) of a surface given as triangles T (n,3,3), normals pointing away from the
    part (out of the face): (frame, axis ratio, skew)"""
    N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); A = np.linalg.norm(N, axis=1) / 2
    C = T.mean(1); w = A / A.sum(); c = (C * w[:, None]).sum(0)
    z = (N / 2).sum(0); z /= np.linalg.norm(z)
    Q = C - c; Q = Q - np.outer(Q @ z, z)                                  # across +Z
    S = (Q * w[:, None]).T @ Q; ev, V = np.linalg.eigh(S)
    x = V[:, 2]; x = x - (x @ z) * z; x /= np.linalg.norm(x)
    s = float((w * (Q @ x) ** 3).sum() / max((w * (Q @ x) ** 2).sum(), 1e-12) ** 1.5)
    if s < 0: x = -x
    y = np.cross(z, x); F = np.eye(4); F[:3, 0], F[:3, 1], F[:3, 2], F[:3, 3] = x, y, z, c
    return F, float(np.sqrt(ev[2] / max(ev[1], 1e-12))), abs(s)


def inner_tris(o):
    """the pauldron's inner surface triangles, own coordinates, normals turned out of the face (toward the hollow,
    i.e. away from the part's material, which is what 'out of the mating face' means for an inside)"""
    Ki = np.linalg.inv(G.M4(o["kb_own_in_obj"])); T = G.tris(o) @ Ki[:3, :3].T + Ki[:3, 3]
    keep = CS.inner_keep(T)
    return T[keep]


def test(A):
    src, out = A[1], A[2]
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    def frame(o):
        p = by[o["kb_parent"]]; return G.M4(p["kb_seated"]) @ G.M4(p["kb_own_in_obj"]) @ G.M4(o["kb_on_frame"])
    X = lambda o: np.linalg.inv(frame(o)) @ B.own(o)                        # own -> shell frame
    cache = {}
    def mf(i):
        if i not in cache: cache[i] = frame_of(inner_tris(by[i]))
        return cache[i]
    rows = []
    for i, o in sorted(by.items(), key=lambda kv: int(re.sub(r"\D", "", kv[0].split("_")[0]) or 0)):
        m = re.match(r"inner surface fit to (p\d+_pad) .*, ([\d.]+) mm", o.get("kb_applied", ""))
        if not i.endswith("_pad") or not m: continue
        j = m.group(1); rms = float(m.group(2))
        (Fo, ro, so), (Fj, rj, sj) = mf(i), mf(j)
        Xo = X(o); Xp = X(by[j]) @ Fj @ np.linalg.inv(Fo)                  # through the mating frames
        P = inner_tris(o).reshape(-1, 3)[::7]
        d = np.linalg.norm((P @ Xo[:3, :3].T + Xo[:3, 3]) - (P @ Xp[:3, :3].T + Xp[:3, 3]), axis=1)
        flag = [w for w, bad in (("round", min(ro, rj) < RATIO), ("even", min(so, sj) < SKEW)) if bad]
        r = dict(id=i, name=o.name, ref=j, inner_rms=rms, off_mm=round(float(d.mean()), 3), off_max=round(float(d.max()), 3),
                 turn=round(G.ang(Xo, Xp), 2), ratio=[round(ro, 2), round(rj, 2)], skew=[round(so, 3), round(sj, 3)], flag=flag)
        rows.append(r)
        print("%-9s %-46s on %-8s inner %.3f  mating-frame carry off %6.2f mm (max %6.2f) %6.1f deg  ratio %.2f/%.2f skew %.2f/%.2f %s"
              % (i, o.name[:46], j, rms, r["off_mm"], r["off_max"], r["turn"], ro, rj, so, sj, " ".join(flag)), flush=True)
    good = [r for r in rows if r["inner_rms"] <= 0.03]
    agree = [r for r in good if r["off_mm"] < 0.3 and r["turn"] < 3]
    print("\nof %d sure inner-surface matches, the mating-frame carry agrees (under 0.3 mm, 3 deg) on %d" % (len(good), len(agree)))
    print("  of those not flagged: %d of %d" % (sum(1 for r in agree if not r["flag"]), sum(1 for r in good if not r["flag"])))
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: {"test": test}[A[0]](A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
