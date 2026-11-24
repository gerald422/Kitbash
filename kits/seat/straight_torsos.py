"""The straight torso of each Turtle Ninja letter (and Redwarden's), for the stage 2 batches (notes 128).

    python kits/seat/straight_torsos.py [LIB]      -> one library path a line (no suffix), sorted

Turtle Ninja ships each torso as 9 copies (straight, twisted, leaned); only the straight one is used (Josh, notes 094).
A torso is straight when its old left shoulder is its right one mirrored across its own mirror plane (the waist
socket's turn, through the middle of the shoulders; make_torso_batch.mirror_frame) to 0.05 mm / 1 deg. The posed
copies miss by 18-26 deg; Mar Fil's torsos all pass (0.007 mm). Of a letter's passing copies the most symmetric one
is taken (the old Mk2-6 builder has a few nearly straight ones). Sockets only (the mating frames), no geometry.
Whole-body models (Moritat, Mk4 Tactical bodies, the Librarian) have no Waist and are left out.
Standard library + numpy (Blender's Python on the PC)."""
import os, sys, json, re
import numpy as np

MAKERS = ("Turtle Ninja - Heresy", "Turtle Ninja - Tacticus", "Redwarden - Tacticus")
MX = np.diag([-1.0, 1, 1, 1])


def off(A, B):
    R = A[:3, :3].T @ B[:3, :3]
    return float(np.linalg.norm(A[:3, 3] - B[:3, 3])), float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def straight(lib):
    best = {}
    for m in MAKERS:
        for d, _, fs in os.walk(os.path.join(lib, m)):
            for f in fs:
                if not f.endswith(".sockets.json"): continue
                sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig"))
                rel = os.path.relpath(os.path.join(d, f[:-13]), lib).replace("\\", "/")
                if sc.get("category") != "Chests" or "RIGGING" in rel.upper(): continue
                S = {s["type"]: np.array(s["matrix"], dtype=float).reshape(4, 4) for s in sc.get("sockets") or []}
                if not all(k in S for k in ("Shoulder R", "Shoulder L", "Waist", "Neck")): continue
                F = S["Waist"].copy(); F[:3, 3] = (S["Shoulder R"][:3, 3] + S["Shoulder L"][:3, 3]) / 2
                d_mm, d_deg = off(S["Shoulder L"], F @ MX @ np.linalg.inv(F) @ S["Shoulder R"] @ MX)
                if d_mm >= 0.05 or d_deg >= 1.0: continue
                letter = re.sub(r"\d+$", "", rel).strip(); k = d_deg + 10 * d_mm
                if letter not in best or k < best[letter][0]: best[letter] = (k, rel)
    return sorted(r for k, r in best.values())


if __name__ == "__main__":
    print("\n".join(straight(sys.argv[1] if len(sys.argv) > 1 else "D:/Kitbash Library")))
