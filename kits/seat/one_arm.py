"""Every pauldron on one arm (Nov 27, Josh): "put all of these onto one arm ... That will also show me any outliers".

    BL kits/seat/one_arm.py -- SRC.blend OUT.blend [--skip ID,ID] [--skip-kit 26,..]
  BL = blender --background --factory-startup --python

From the pauldron-on-the-shell file (one column per pauldron): each pauldron keeps its place in its shell (its own ->
the shell's crown, the shell as built: the arm's Pad R) and is moved into the first column's shell, so all of them sit
on the one Arm 2B R together. The other columns (torso, spacer, arm, shell) are removed. Each pauldron's origin is put
on the crown (the mesh doesn't move), the start of Josh's plan to give every pauldron the shell's origin and roll;
kb_seated is reset so read / compare see only his later moves. Pack collections are kept, to hide or show a pack."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
import geom as G, batch as B, carry_by_shape as CS


def main(A):
    src, out = A[0], A[1]
    skip = set((B.opt(A, "--skip", "") or "").split(",")) - {""}
    skip_kit = [k for k in (B.opt(A, "--skip-kit", "") or "").split(",") if k]
    if os.path.exists(out): raise SystemExit("%s exists: never overwritten" % out)
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    built = lambda o: G.M4(o["kb_seated"]) @ G.M4(o["kb_own_in_obj"])        # own -> world, as built
    pads = sorted((i for i in by if i.endswith("_pad")), key=lambda i: int(i[1:-4]))
    col = pads[0][:-4]; sh0 = by[col + "_shell"]
    sh0.matrix_world = G.mat(G.M4(sh0["kb_seated"])); bpy.context.view_layer.update()
    F0 = built(sh0) @ G.M4(by[pads[0]]["kb_on_frame"])                       # the crown of the one shell kept
    moved, dropped, worst = 0, [], 0.0
    for i in pads:
        o = by[i]
        if i in skip or any(c.name.startswith(k) for c in o.users_collection for k in skip_kit):
            dropped.append(i); continue
        X = np.linalg.inv(built(by[o["kb_parent"]]) @ G.M4(o["kb_on_frame"])) @ B.own(o)   # own -> its shell's crown
        o.parent = sh0; o["kb_parent"] = sh0["kb_id"]
        o.rotation_mode = 'QUATERNION'; o.matrix_world = G.mat(F0 @ X @ np.linalg.inv(G.M4(o["kb_own_in_obj"])))
        bpy.context.view_layer.update(); CS.rebake(o, F0)
        o["kb_seated"] = G.flat16(np.array(o.matrix_world)); moved += 1
        worst = max(worst, float(np.abs(np.linalg.inv(F0) @ B.own(o) - X).max()))          # its place in the shell kept
    gone = [o for i, o in by.items() if (not i.startswith(col + "_") and not i.endswith("_pad")) or i in dropped]
    for o in gone: bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    print("on one arm: %d pauldrons (place in the shell kept to %.6f); left out: %s; %d column pieces removed"
          % (moved, worst, " ".join(dropped) or "none", len(gone)), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
