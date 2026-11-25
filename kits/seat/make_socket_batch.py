"""Stage 4 (arms' sockets, docs/PLAN.md): one batch of right arms, each on the spacer on Torso 2 as written in stage 3,
with the check pieces Josh moves to show where the arm's sockets go (Nov 25, notes 169):

    BL kits/seat/make_socket_batch.py -- SPEC_OUT.json BATCH_OUT.blend NAME ARM_REL [ARM_REL ...]
  BL = blender --background --factory-startup --python

Per column: Torso 2 (locked), the spacer on Shoulder R (locked), the arm on it by its written fit (locked), and
- Pad R: the pauldron guide on the arm with Shoulder Pad 1 riding in it (by Pad 1's written fit). Josh moves the guide
  (it turns about its crown); its place is the arm's Pad R socket (and its mirror Pad L), the guide's frame kept in it
  (props.kb_connectors) as on Arm 2B R. It starts where Arm 2B R's guide sits on the torso: pads sit the same on the
  torso whatever the arm (skill kitbash-seat-by-shape).
- Hand R: Chain Sword 1 R in the hand by its fit from Josh's placement on Arm 2A R (ref_hand_fits.py). Josh moves it;
  its pivot is the arm's Hand R socket (and Hand L). Chain Sword 2 R / 3 R and Shield R share that socket. It starts
  on the arm's old Hand R socket, or where Arm 2A R's sits on the torso if it has none. Arms with the hand sculpted
  (noHand) get no Hand piece; arms with their own pad (noPad) get no guide.
The reference columns are locked: Arm 2B R with its guide and pad (stage 1) and Arm 2A R with its chain sword (the
four reference hand fits). Head faint, backpack and legs solid. The arm's live mirror shows on the left."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import geom as G, batch as B, make_torso_batch as MT

A2 = "Mar Fil - Tacticus/AssaultMarines-V2/"
ARM_2A = A2 + "Arms/MarFil Assault - Arm 2A R"
SWORD = A2 + "Melee/MarFil Assault - Chain Sword 1 R"


def sockets(rel): return {s["type"]: G.M4(s["matrix"]) for s in B.sidecar(MT.LIB, rel).get("sockets") or []}


def main(A):
    spec_out, blend_out, name, arms = A[0], A[1], A[2], A[3:]
    S_sh = sockets(MT.T2)["Shoulder R"]
    on_torso = lambda rel: S_sh @ G.M4(B.sidecar(MT.LIB, rel)["fits"]["Shoulder R"])     # arm own -> Torso 2 own
    A_2b, A_2a = on_torso(MT.ARM), on_torso(ARM_2A)
    pad_2b, hand_2a = sockets(MT.ARM)["Pad R"], sockets(ARM_2A)["Hand R"]
    objs = [{"id": "ref", "role": "host", "name": "REFERENCE Torso 2 (locked)", "rel": MT.T2, "pose": {"place": True}, "at": [0, 0, 0]}]
    objs += MT.column("ref", "REF ", None, locked=True)
    log = []

    def column(k, rel, locked):
        tid = "a%d" % k; short = os.path.basename(rel).replace("MarFil ", ""); sc = B.sidecar(MT.LIB, rel)
        at = [MT.GAP * (k % MT.PER_ROW), 0, -MT.ROW_GAP * (k // MT.PER_ROW)]
        role = "check" if locked else "part"; pre = ("REF " if locked else "") + short
        o = [{"id": tid, "role": "host", "name": "Torso 2 for " + short, "rel": MT.T2, "pose": {"place": True}, "at": at},
             {"id": tid + "_spacer", "role": "check", "name": short + " Spacer", "connector": {"kind": "spacer", "from": "arms", "obj": "Springles Spacer"},
              "parent": tid, "on": "Shoulder R", "mirror": True, "pose": {"at_pivot": True, "shift_from": [MT.T2, "Shoulder R"]}},
             {"id": tid + "_arm", "role": "check", "name": pre + " (locked)", "rel": rel, "parent": tid + "_spacer", "on": "arm seat", "mirror": True, "pose": {"fit": "Shoulder R"}}]
        A_x = on_torso(rel); own = sockets(rel); said = []
        if not sc.get("noPad"):
            S_pad = np.linalg.inv(A_x) @ A_2b @ pad_2b
            said.append("Pad R starts where Arm 2B R's guide sits on the torso (%s)" % ("old Pad R %.1f mm %.0f deg away" % tuple(G.off(S_pad, own["Pad R"])) if "Pad R" in own else "no old Pad R"))
            g = {"id": tid + "_guide", "role": role, "name": pre + " Guide (Pad R)", "connector": MT.GUIDE, "parent": tid + "_arm", "on": "Pad R",
                 "on_matrix": G.flat16(S_pad), "mirror": True, "joint": "Guide on the arm (Pad R)", "pose": {"at_pivot": True, "shift_from": [MT.ARM, "Pad R"]}}
            if not locked:
                g.update(note="move the guide (it turns about its crown) so the pad sits right; its place is this arm's Pad R",
                         write={"host": tid + "_arm", "socket": "Pad R", "mirror": "Pad L", "half": "socket"})
            o += [g, {"id": tid + "_pad", "role": "check", "name": pre + " Shoulder Pad 1", "rel": MT.PAD, "parent": tid + "_guide", "on": "crown", "mirror": True, "pose": {"fit": "Pad R"}}]
        if not sc.get("noHand"):
            S_hand = own["Hand R"] if "Hand R" in own else np.linalg.inv(A_x) @ A_2a @ hand_2a
            said.append("Hand R starts on %s" % ("its old Hand R" if "Hand R" in own else "Arm 2A R's place on the torso (no old Hand R)"))
            h = {"id": tid + "_hand", "role": role, "name": pre + " Chain Sword 1 R (Hand R)", "rel": SWORD, "parent": tid + "_arm", "on": "Hand R",
                 "on_matrix": G.flat16(S_hand), "mirror": True, "joint": "Weapon in the hand (Hand R)", "pose": {"fit": "Hand R"}}
            if not locked:
                h.update(note="move the sword so its hand sits right on the wrist; its pivot is this arm's Hand R (Chain Swords 2 / 3 R and Shield R share it)",
                         write={"host": tid + "_arm", "socket": "Hand R", "mirror": "Hand L", "half": "socket"})
            o.append(h)
        else: said.append("hand sculpted (noHand): no Hand piece")
        for sock, pid, ref_obj, prel, c, joint in MT.PIECES:
            o.append({"id": "%s_%s" % (tid, pid), "role": "neighbour" if pid == "head" else "check", "name": short + " " + ref_obj.split(" - ")[-1],
                      "rel": prel, "parent": tid, "on": sock, "pose": {"fit": sock}})
        log.append("%-34s %s%s" % (short[:34], "; ".join(said), " (reference, locked)" if locked else ""))
        return o

    k = 1
    objs += column(k, ARM_2A, True); k += 1
    for rel in arms:
        if rel in (ARM_2A, MT.ARM): continue                  # the references: locked, never rewritten here
        objs += column(k, rel, False); k += 1
    spec = {"name": name, "stage": "4 (arms' sockets)", "out": blend_out, "sources": MT.SRC,
            "about": "Each column: move the guide (Pad R) and the chain sword (Hand R) on the locked arm. The first two columns are the references (Arm 2B R with its guide and pad, Arm 2A R with its sword), locked.",
            "objects": objs}
    json.dump(spec, open(spec_out, "w", encoding="utf-8"), indent=1)
    print("\n".join(log)); print("SPEC", spec_out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
