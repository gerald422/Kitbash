"""Source sidecars for the Nov 9 batch, written beside the files in D:\\new cults (then the library tools file them).
Never over an existing sidecar. Out: <out>/<rel>.sockets.json + list.json."""
import sys, os, json, re, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/rw_spr"); from common import *
W = "/home/claude/work/new/"; OUT = sys.argv[1]
heads = json.load(open(W + "heads.json")); pads = json.load(open(W + "pads.json")); packs = json.load(open(W + "packs.json"))
belt = json.load(open("/mnt/user-data/uploads/d/Kitbash Library/_backups/springles-redwarden-2026-11-09/belt_fits.json"))
files = json.load(open(W + "all_new.json"))           # every new file (relative to D:\new cults), from the device
EQ = "Springles/accessorys and equipment/"
def category(rel):
    low = rel.lower(); f = os.path.basename(low)
    if rel.startswith(RW):
        return {"Helmets": "Heads", "Sholderpads": "Shoulder Pads", "Torso": "Chests"}[rel[len(RW):].split("/")[0]]
    if "/mk5 helmets/" in low or "/mk5 alt helmets/" in low: return "Heads"
    if "/shoulder pads/" in low: return "Shoulder Pads"
    if low.startswith(EQ.lower()):
        sub = rel[len(EQ):].split("/")[0].lower()
        if "/" not in rel[len(EQ):]: return "Unsorted"                         # vox earpiece (digital kitbash only)
        if "no hand" in f: return "Hand-less Weapons"
        if sub == "accessorys":
            return "Grenades" if re.search(r"grenade|melta bomb", f) else "Accessories"
        return {"back gear": "Backpack Toppers", "combat knife": "Melee", "held helmets": "Hands", "held kit": "Hands",
                "holster": "Plate Accessories", "holster bolter": "Plate Accessories", "sheaths": "Plate Accessories",
                "removed helmets": "Accessories", "scanner arms": "Forearm Armour", "unsheathing weapons": "Melee",
                "vox backpacks": "Backpacks"}[sub]
    raise KeyError(rel)
def build(rel):
    stem = os.path.splitext(os.path.basename(rel))[0]; cat = category(rel)
    d = {"schemaVersion": 1, "part": stem, "category": cat}
    spr = rel.startswith("Springles/")
    if spr: d["scale"] = SPR_SCALE
    fits, notes, sockets = {}, {}, []
    if rel in heads:
        fits["Neck"] = heads[rel]["fit"]; notes["Neck"] = "Josh's Assault helmet 1 neck seat matched onto it (match %.3f mm)" % heads[rel]["med"]
    if rel in pads:
        p = pads[rel]; fits[p["side"]] = p["fit"]
        notes["Pad"] = "Josh's pad 62 matched onto it (x%.2f, match %.3f mm), his Pad R fit carried across about 62's shell centre" % (p["scale_vs_62"], p["med"])
    if rel in packs:
        fits["Back"] = packs[rel]["fit"]; notes["Back"] = packs[rel]["note"]
    b = belt.get(os.path.basename(rel)) if rel.startswith(EQ + "accessorys/") else None
    if b and "fit" in b:
        for t in ("Hip R", "Hip L", "Belt Back"): fits[t] = b["fit"]
        notes["belt"] = "stands on the plate, thin across X, flat back on %s: back face centre on the anchor; TIOW rocks and settles it" % b["back"]
    if cat == "Chests":
        import torso
        S, note = torso.sockets()
        for t, M in S.items():
            sockets.append({"type": t, "name": stem + "_socket_" + t, "matrix": flat(M), "display_type": "ARROWS", "display_size": 3.0,
                            "props": {"tiow_from": note}})
        d["upright"] = flat(M4(rz(np.pi), np.zeros(3)))
        notes["upright"] = "front is -Y in the file: turned 180 deg to face +Y like Mar Fil's torsos"
    if not fits and cat not in ("Chests",):
        notes["category"] = "filed without a fit (Nov 9): " + ("Prepare's hand rule finds the grip" if cat in ("Melee", "Hands", "Pistols") else "needs Josh's reference placement")
    d["sockets"] = sockets; d["fits"] = fits; d["notes"] = notes
    d["original"] = {"name": stem, "folder": os.path.basename(os.path.dirname(rel)), "path": rel.replace("/", "\\")}
    return d
if __name__ == "__main__":
    import collections
    made = {}; c = collections.Counter(); nf = collections.Counter()
    for rel in files:
        d = build(rel); made[rel] = d; c[d["category"]] += 1; nf[d["category"]] += bool(d["fits"] or d["sockets"])
        q = os.path.join(OUT, rel[:-4] + ".sockets.json"); os.makedirs(os.path.dirname(q), exist_ok=True)
        json.dump(d, open(q, "w", encoding="utf-8"), indent=1)
    json.dump(sorted(made), open(os.path.join(OUT, "list.json"), "w"), indent=0)
    for k in sorted(c): print("%-18s %3d  with fits %3d" % (k, c[k], nf[k]))
    print(len(made), "sidecars")
