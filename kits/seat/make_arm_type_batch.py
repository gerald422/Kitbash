"""Stage 4 pads, file 2 of Josh's plan (Nov 26, notes 173): each arm type once, the shell placed on it (its Pad R),
for Josh to set and take a setup-only shoulder cut from ("it should just be all arm types ... It shouldnt need to be
every single arm"; the matching looks at the shoulder only).

    BL kits/seat/make_arm_type_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME ARM_TYPES.json
  BL = blender --background --factory-startup --python

Columns: Torso 2, the spacer and the arm as written in stage 3 (locked), the full-size shell (movable, turns about its
crown: its place is the arm's Pad R and Pad L) and Shoulder Pad 1 riding on it by its written fit (locked, for the
look). First the arm types he seated on Nov 23 (his seat file), the shell where he put the guide; then one right arm
per kit whose arms matched none of his cuts as the same shoulder (`match_arm_types.py`: "same" under 0.06 mm; near
matches are not trusted, a dome patch lands near any dome), the shell where Arm 2B R's sits on the torso."""
import os, sys, json, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
import geom as G, batch as B, make_torso_batch as MT, make_pad_batch as MP, make_pauldron_batch as MPB


def main(A):
    spec_out, blend_out, name, types_json = A[0], A[1], A[2], A[3]
    lib = MT.LIB; res = json.load(open(types_json, encoding="utf-8"))["arms"]
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(MT.SRC["seat"]), load_ui=False); bpy.context.view_layer.update()
    ob = bpy.data.objects; S_sh = MT.sockets(MT.T2)
    A_2b = S_sh["Shoulder R"] @ G.M4(B.sidecar(lib, MT.ARM)["fits"]["Shoulder R"]); pad_2b = MT.sockets(MT.ARM)["Pad R"]
    objs, log = [], []

    def column(k, arm_rel, short, shell_pose, shell_on, note):
        tid = "t%d" % k; at = [MT.GAP * (k % MT.PER_ROW), 0, -MT.ROW_GAP * (k // MT.PER_ROW)]
        sh = {"id": tid + "_shell", "role": "part", "name": short + " Shell (Pad R)", "connector": MPB.SHELL, "parent": tid + "_arm",
              "joint": "Shell on the arm (Pad R)", "pose": shell_pose, "note": note,
              "write": {"host": tid + "_arm", "socket": "Pad R", "mirror": "Pad L", "half": "socket"}}
        sh.update(shell_on)
        return [{"id": tid, "role": "host", "name": "Torso 2 for " + short, "rel": MT.T2, "pose": {"place": True}, "at": at},
                {"id": tid + "_spacer", "role": "check", "name": short + " Spacer", "connector": {"kind": "spacer", "from": "arms", "obj": "Springles Spacer"},
                 "parent": tid, "on": "Shoulder R", "pose": {"at_pivot": True, "shift_from": [MT.T2, "Shoulder R"]}},
                {"id": tid + "_arm", "role": "check", "name": short + " (locked)", "rel": arm_rel, "parent": tid + "_spacer", "on": "arm seat", "pose": {"fit": "Shoulder R"}},
                sh,
                {"id": tid + "_pad", "role": "check", "name": short + " Shoulder Pad 1 (rides on the shell)", "rel": MT.PAD, "parent": tid + "_shell", "on": "crown", "pose": {"fit": "Pad R"}}]

    k = 0; seeded = set()
    for an in sorted(o.name for o in ob if o.name.startswith("Adapter - ")):
        arm_name = an[len("Adapter - "):]; arm_rel = MP.rel_of(arm_name)
        if arm_name not in ob or ob[arm_name].get("kb_mirrored") or not arm_rel or "Shoulder R" not in (B.sidecar(lib, arm_rel).get("exact") or []): continue
        if arm_rel == MT.ARM: continue                                        # Arm 2B R's Pad R is his (stage 1)
        n = sum(1 for r in res if r["type"] == arm_name.replace("TN ", "TN ") and r["grade"] == "same")
        objs += column(k, arm_rel, os.path.basename(arm_rel), {"from": "seat", "obj": an, "relative_to": [arm_name, "t%d_arm" % k]}, {"on": "self"},
                       "your Nov 23 seat for this arm type: set the shell, then take the shoulder cut under it (setup only)")
        log.append("seeded  %-46s your Nov 23 seat" % os.path.basename(arm_rel)[:46]); seeded.add(arm_rel); k += 1
    kits = collections.defaultdict(list)
    for r in res:
        if r["grade"] == "same" or r["left"] or r["rel"] in seeded or r["rel"] == MT.ARM: continue
        p = r["rel"].split("/"); kits["/".join(p[:3] if p[0].startswith("Marta") else p[:2])].append(r)
    for kt, rs in sorted(kits.items()):
        r = sorted(rs, key=lambda r: (r["grade"] != "none", r["rel"]))[0]; rel = r["rel"]
        A_x = S_sh["Shoulder R"] @ G.M4(B.sidecar(lib, rel)["fits"]["Shoulder R"])
        S = np.linalg.inv(A_x) @ A_2b @ pad_2b
        objs += column(k, rel, os.path.basename(rel), {"at_pivot": True}, {"on": "Pad R", "on_matrix": G.flat16(S)},
                       "new arm type (kit %s, %d arms not matched as the same shoulder): set the shell, then take the shoulder cut under it" % (kt, len(rs)))
        log.append("new     %-46s %s, %d arms (best: %s %.3f)" % (os.path.basename(rel)[:46], kt[:50], len(rs), r["best"], r["rms"])); k += 1
    spec = {"name": name, "stage": "4 (arms' sockets): the shell per arm type", "out": blend_out, "sources": dict(MT.SRC, pads=MPB.PADS),
            "about": "Each arm type once: set the shell on the locked arm (its place is that type's Pad R), then take the shoulder cut under it (setup only). Shoulder Pad 1 rides on the shell for the look.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("%d columns" % k); print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
