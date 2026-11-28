"""A locked outline of the reference arm on every column of an arm batch (Nov 28, Josh: "give me an outline locked
version on each arm that has the reference arm on it. It can be difficult to judge the shape without something to
compare against").

    BL kits/seat/add_ref_arm.py -- SRC.blend OUT.blend [--rel LIBRARY_PATH]
  BL = blender --background --factory-startup --python

For every column (a torso tN with an arm tN_arm): Arm 2B R (or --rel) on that torso as written (Torso 2's Shoulder R x
its Shoulder R fit: the same spacer seat every arm has), drawn as wire, unselectable, every transform locked, in the
column's collection. One mesh shared by all of them. Ids tN_refarm, role "check", so batch read / write ignore them."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B, make_torso_batch as MT


def main(A):
    src, out = A[0], A[1]; rel = B.opt(A, "--rel", MT.ARM); lib = MT.LIB
    if os.path.exists(out): raise SystemExit("%s exists: never overwritten" % out)
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    sc = B.sidecar(lib, rel)
    A_t = MT.sockets(MT.T2)["Shoulder R"] @ G.M4(sc["fits"]["Shoulder R"])       # the reference arm in the torso's frame
    proto = B.make_mesh("REF " + os.path.basename(rel) + " (outline)", B.stl_tris(lib, rel, sc), np.eye(4)); me = proto.data
    bpy.data.objects.remove(proto, do_unlink=True)
    n = 0
    for i, arm in sorted(by.items()):
        if not i.endswith("_arm"): continue
        t = i[:-4]; tor = by.get(t)
        if tor is None: continue
        o = bpy.data.objects.new(("REF %s outline - %s" % (os.path.basename(rel).split(" - ")[-1], arm.name))[:63], me)
        for c in arm.users_collection: c.objects.link(o)
        W = B.own(tor) @ A_t
        o.parent = tor; o.matrix_parent_inverse = tor.matrix_world.inverted(); o.matrix_world = G.mat(W)
        o.display_type = 'WIRE'; o.show_in_front = False; o.hide_select = True; o.hide_render = True
        o.lock_location = o.lock_rotation = o.lock_scale = (True, True, True)
        o["kb_id"] = t + "_refarm"; o["kb_role"] = "check"; o["kb_rel"] = rel; o["kb_on"] = "Shoulder R (reference outline)"
        o["kb_own_in_obj"] = G.flat16(np.eye(4)); o["kb_on_frame"] = G.flat16(np.linalg.inv(B.own(tor)) @ W)
        bpy.context.view_layer.update(); o["kb_seated"] = G.flat16(np.array(o.matrix_world)); n += 1
    print("reference outline (%s) on %d arms" % (os.path.basename(rel), n), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
