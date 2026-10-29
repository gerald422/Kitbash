"""Cross-kit marines: parts from Assault Marines V2, Veteran / Bladeguard, Intercessors V2 and the Chaplain mixed on
one model, against single-kit marines for comparison. For each joint: did it snap where it should, and how the two
parts meet there (closest approach, deepest cut, share of the part's surface near the joint that touches)."""
exec(open("/home/claude/test/v18/common18.py").read())
from mathutils.bvhtree import BVHTree
OUT = "/home/claude/test/v111/out"
AM = "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL"
VS = "All Mar All the time/VeteranSquad/VeteranSquad"; BG = "All Mar All the time/VeteranBladeSquad/VeteranBladeSquad"
IV = "Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL"
CJ = "All Mar All the time/ChaplainWithJumpPack (1)/ChaplainWithJumpPack"
OR = "All Mar All the time/Outriders (1)/Outriders"; TM = "All Mar All the time/Techmarine (2)/Techmarine"
KITS = ((AM, "AM"), (VS, "Vet"), (BG, "BG"), (IV, "IV2"), (CJ, "CJ"), (OR, "OR"), (TM, "TM"))
def kit_of(rel): return next(k for p, k in KITS if rel.startswith(p))
deps = bpy.context.evaluated_depsgraph_get()
_trees = {}
def tree_of(ob):
    if ob.name not in _trees:
        v, t = T._world_tris(ob, bpy.context.evaluated_depsgraph_get()); _trees[ob.name] = BVHTree.FromPolygons(v.tolist(), t.tolist())
    return _trees[ob.name]
def contact(child, parent, centre, r=7.0):
    _trees.pop(parent.name, None)
    v, t = T._world_tris(child, bpy.context.evaluated_depsgraph_get())
    c = np.array(centre); k = np.linalg.norm(v - c, axis=1) < r
    P = v[k]
    if len(P) > 6000: P = P[np.random.default_rng(0).choice(len(P), 6000, replace=False)]
    if not len(P): return None
    tr = tree_of(parent); sd = []
    for p in P:
        hit = tr.find_nearest(Vector(p), 3.0)
        if hit[0] is None: continue
        sd.append((Vector(p) - hit[0]).dot(hit[1]))
    if not sd: return (9.9, 0.0, 0.0)
    sd = np.array(sd)
    return (float(np.abs(sd).min()), float(max(0.0, -np.percentile(sd, 2))), float((np.abs(sd) < 0.15).mean() * len(sd) / max(1, k.sum())))
rows = []
def on(p, want): return p is not None and p.parent is not None and p.parent.get("ws_type") in want
def put(label, host, rel, cat, want, sel=None):
    want = (want,) if isinstance(want, str) else want
    select(sel or host); p = send(rel, cat)
    ok = on(p, want)
    ck(f"{label}: {os.path.basename(rel)} on {'/'.join(want)}", ok, T._state["last"])
    if ok:
        par = p.parent.parent if p.parent.parent is not None else host
        m = contact(p, par, p.parent.matrix_world.translation)
        rows.append((label, p.parent.get("ws_type"), kit_of(rel), str(par.get("tiow_kit", "")), m))
        p["tiow_kit"] = kit_of(rel)
    return p if ok else None
marines = []
def marine(label, cursor, chest, legs, rock=None, arms=(), hands=(), grips=(), head=None, pack=None, topper=None, pads=(), shins=(), belt=(), two=None):
    select(None); t = send(chest, "Bodies", cursor); t["tiow_kit"] = kit_of(chest)
    lg = put(label, t, legs, "Bodies", "Waist")
    if rock and lg: put(label, lg, rock, "Bases", "Base")
    A_ = {}
    for sd, rel in arms:
        A_[sd] = put(label, t, rel, "Arms", f"Shoulder {sd}")
    H_ = {}
    for sd, rel, cat in hands:
        if A_.get(sd): H_[sd] = put(label, A_[sd], rel, cat, f"Hand {sd}")
    for sd, rel in grips:
        if H_.get(sd): put(label, H_[sd], rel, "Weapons", f"Grip {sd}")
    if two: put(label, t, two, "Weapons", "Shoulder R")
    if head: put(label, t, head, "Heads", "Neck")
    pk = put(label, t, pack, "Backpacks", "Back") if pack else None
    if topper and pk: put(label, pk, topper, "Backpacks", "Back Top")
    for sd, rel in pads:
        if A_.get(sd): put(label, A_[sd], rel, "Shoulder Pads", f"Pad {sd}")
    for sd, rel in shins:
        if lg is None: continue
        s_ = sock(lg, f"Shin {sd}")
        ck(f"{label}: legs have a Shin {sd} anchor", s_ is not None)
        if s_ is not None: put(label, lg, rel, "Knee Pads", f"Shin {sd}", sel=s_)
    for rel in belt:
        if lg: put(label, lg, rel, "Accessories", ("Hip R", "Hip L", "Belt Front", "Belt Back"))
    if lg is not None and "Outriders" in legs:
        bk = put(label, lg, f"{OR}/Bike/RawSTL/19-Body-1.stl", "Vehicles", "Bike")
    marines.append((label, t))
# single-kit marines (baselines)
marine("AM", (0, 0, 0), f"{AM}/Chest/22-Torso-1.stl", f"{AM}/Legs/29-Legs-2.stl",
       arms=(("R", f"{AM}/Arms/106-Arm-7-R-A.stl"), ("L", f"{AM}/Arms/109-Arm-7-L-B.stl")),
       hands=(("R", f"{AM}/Melee/175-ChainSword-1-R.stl", "Melee"), ("L", f"{AM}/Pistols/LeftOrientated/Weapons-Assault211-BoltPistol-L.stl", "Pistols")),
       head=f"{AM}/Helmet-Heads/3-Helmet-3.stl", pack=f"{AM}/JumpPacks/56-JumpPack-2.stl", pads=(("R", f"{AM}/ShoulderPads/63-ShoulderPad-2.stl"),))
marine("IV2", (60, 0, 0), f"{IV}/Chest-Raw/12-Chest-1.stl", f"{IV}/Legs-Raw/17-Legs-1.stl",
       arms=(("R", f"{IV}/Arms-Raw/57-Arm-1-R.stl"), ("L", f"{IV}/Arms-Raw/Arms-Left/58-Arm-2-L.stl")),
       hands=(("R", f"{IV}/Hands-Raw/273-Hand-1-R.stl", "Hands"), ("L", f"{IV}/Hands-Raw/Hand-Left/274-Hand-2-L.stl", "Hands")),
       grips=(("R", f"{IV}/Melee-NoHand/246-ChainSword-NoHand.stl"), ("L", f"{IV}/Weapons-NoHand-Raw/262-BoltPistol-NoHand.stl")),
       head=f"{IV}/Helmets-Heads-Raw/1-Helmet-1.stl", pack=f"{IV}/BackPacks-Raw/266-BackPack-1.stl",
       pads=(("R", f"{IV}/ShoulderPad-Raw/49-ShoulderPad-1.stl"), ("L", f"{IV}/ShoulderPad-Raw/50-ShoulderPad-2.stl")),
       shins=(("R", f"{IV}/ShinPad-Raw/42-ShinPad-A.stl"), ("L", f"{IV}/ShinPad-Raw/ShinPad-Left/42-ShinPad-A-L.stl")))
marine("Vet", (120, 0, 0), f"{VS}/Body/Body-RawSTL/12-Chest-A.stl", f"{VS}/Body/Body-RawSTL/17-Body-A.stl",
       arms=(("R", f"{VS}/Arms/Arms-RawSTL/142-Arm-A.stl"), ("L", f"{VS}/Arms/Arms-Mirrored/143-Arm-B-Mirrored.stl")),
       hands=(("R", f"{VS}/Melee/Melee-RawSTL/132-Sword-B.stl", "Melee"), ("L", f"{VS}/Weapons/Weapons-Mirrored/100-Gun-5-B-Mirrored.stl", "Pistols")),
       head=f"{VS}/Helmets/Helmet-RawStl/1-Helmet-A.stl", pack=f"{VS}/Backpacks/BackPacks-RawSTL/23-Backpack-A.stl",
       pads=(("R", f"{VS}/ShoulderPads/ShoulderPads-RawSTL/44-ShoulderPad-R-A.stl"), ("L", f"{VS}/ShoulderPads/ShoulderPads-RawSTL/57-ShoulderPad-L-A.stl")),
       shins=(("R", f"{VS}/ShinPads/ShinPads-RawSTL/31-ShinPad-A.stl"), ("L", f"{VS}/ShinPads/ShinPads-Mirrored/31-ShinPad-A-Mirrored.stl")))
# mixed
marine("X1", (180, 0, 0), f"{IV}/Chest-Raw/13-Chest-2.stl", f"{AM}/Legs/30-Legs-3.stl",
       arms=(("R", f"{VS}/Arms/Arms-RawSTL/142-Arm-A.stl"), ("L", f"{AM}/Arms/128-Arm-11-L-A.stl")),
       hands=(("R", f"{IV}/Hands-Raw/273-Hand-1-R.stl", "Hands"), ("L", f"{AM}/Pistols/LeftOrientated/Weapons-Assault211-BoltPistol-L.stl", "Pistols")),
       grips=(("R", f"{IV}/Melee-NoHand/246-ChainSword-NoHand.stl"),),
       head=f"{CJ}/Head/Head-Raw-STL/1-Head.stl", pack=f"{IV}/BackPacks-Raw/266-BackPack-1.stl",
       pads=(("R", f"{CJ}/ShoulderPads/ShoulderPads-Raw-STL/7-ShoulderPad-Right.stl"), ("L", f"{VS}/ShoulderPads/ShoulderPads-RawSTL/57-ShoulderPad-L-A.stl")),
       shins=(("R", f"{IV}/ShinPad-Raw/42-ShinPad-A.stl"), ("L", f"{IV}/ShinPad-Raw/ShinPad-Left/42-ShinPad-A-L.stl")),
       belt=(f"{CJ}/Accesories/Accesories-Raw-STL/24-Badge.stl", f"{CJ}/Accesories/Accesories-Raw-STL/26-Grenade.stl"))
marine("X2", (240, 0, 0), f"{AM}/Chest/23-Torso-2.stl", f"{IV}/Legs-Raw/20-Legs-4.stl", rock=f"{IV}/Rocks-Raw/283-Rock-16.stl",
       arms=(("R", f"{CJ}/Arms/Arms-Raw-STL/13-Arm-Right-A.stl"), ("L", f"{CJ}/Arms/Arms-Raw-STL/17-Arm-Left-A.stl")),
       hands=(("R", f"{CJ}/Weapons/Weapons-Raw-STL/22-Crozius.stl", "Melee"), ("L", f"{CJ}/Weapons/Weapons-Raw-STL/21-AbsolvorPistol.stl", "Pistols")),
       head=f"{AM}/Helmet-Heads/7-Helmet-7.stl", pack=f"{CJ}/Jumppack/Jumppack-Raw-STL/11-Jumppack.stl", topper=f"{CJ}/Jumppack/Jumppack-Raw-STL/12-Exhaust.stl",
       pads=(("R", f"{IV}/ShoulderPad-Raw/51-ShoulderPad-3.stl"), ("L", f"{IV}/ShoulderPad-Raw/54-ShoulderPad-6.stl")),
       shins=(("R", f"{VS}/ShinPads/ShinPads-RawSTL/31-ShinPad-A.stl"), ("L", f"{VS}/ShinPads/ShinPads-Mirrored/31-ShinPad-A-Mirrored.stl")),
       belt=(f"{CJ}/Accesories/Accesories-Raw-STL/23-Book.stl", f"{CJ}/Accesories/Accesories-Raw-STL/25-Holster.stl"))
marine("X3", (300, 0, 0), f"{VS}/Body/Body-RawSTL/12-Chest-A.stl", f"{CJ}/Legs/Legs-Raw-STL/4-Legs-B-ChaplainWithJumppack.stl", rock=f"{CJ}/Rocks/Rocks-Raw-STL/28-Rock-B.stl",
       arms=(("R", f"{IV}/Arms-Raw/59-Arm-3-R.stl"), ("L", f"{IV}/Arms-Raw/Arms-Left/60-Arm-4-L.stl")),
       hands=(("R", f"{IV}/Melee-Handed-Raw/241-PowerSword-A-R.stl", "Melee"), ("L", f"{AM}/Pistols/LeftOrientated/Weapons-Assault211-BoltPistol-L.stl", "Pistols")),
       head=f"{IV}/Helmets-Heads-Raw/8-Head-1.stl", pack=f"{AM}/JumpPacks/57-JumpPack-3.stl",
       pads=(("R", f"{BG}/ShoulderPads/ShoulderPads-RawSTL/56-ShoulderPad-1.stl"), ("L", f"{BG}/ShoulderPads/ShoulderPads-Mirrored/56-ShoulderPad-1-Mirrored.stl")),
       shins=(("R", f"{CJ}/ShinPads/ShinPads-Raw-STL/9-ShinPad-Right.stl"), ("L", f"{CJ}/ShinPads/ShinPads-Raw-STL/10-ShinPad-Left.stl")))
marine("X4", (360, 0, 0), f"{CJ}/Chest/Chest-Raw-STL/2-ChestChaplain.stl", f"{VS}/Body/Body-RawSTL/17-Body-A.stl",
       arms=(("R", f"{AM}/Arms/126-Arm-11-R-A.stl"), ("L", f"{AM}/Arms/109-Arm-7-L-B.stl")),
       hands=(("R", f"{VS}/Melee/Melee-RawSTL/132-Sword-B.stl", "Melee"), ("L", f"{CJ}/Weapons/Weapons-Raw-STL/21-AbsolvorPistol.stl", "Pistols")),
       head=f"{VS}/Helmets/Helmet-RawStl/1-Helmet-A.stl", pack=f"{VS}/Backpacks/BackPacks-RawSTL/23-Backpack-A.stl",
       pads=(("R", f"{CJ}/ShoulderPads/ShoulderPads-Raw-STL/7-ShoulderPad-Right.stl"), ("L", f"{CJ}/ShoulderPads/ShoulderPads-Raw-STL/8-ShoulderPad-Left.stl")),
       shins=(("R", f"{IV}/ShinPad-Raw/45-ShinPad-D.stl"), ("L", f"{IV}/ShinPad-Raw/ShinPad-Left/45-ShinPad-D-L.stl")),
       belt=(f"{CJ}/Accesories/Accesories-Raw-STL/23-Book.stl", f"{CJ}/Accesories/Accesories-Raw-STL/25-Holster.stl"))
marine("X5", (420, 0, 0), f"{BG}/Body/Body-RawSTL/17-Chest-1.stl", f"{AM}/Legs(JumpPack)/35-Legs-2-A.stl",
       arms=(("R", f"{IV}/Bolter-Individual-Raw/125-Bolter-A-1-R.stl"), ("L", f"{IV}/Bolter-Individual-Raw/Bolter-Individual-Left/131-Bolter-A-2-Individual-L.stl")),
       head=f"{CJ}/Head/Head-Raw-STL/1-Head.stl", pack=f"{AM}/JumpPacks/59-JumpPack-5.stl",
       shins=(("R", f"{IV}/ShinPad-Raw/47-ShinPad-F.stl"), ("L", f"{IV}/ShinPad-Raw/ShinPad-Left/47-ShinPad-F-L.stl")))
marine("X6", (480, 0, 0), f"{IV}/Chest-Raw/14-Chest-3.stl", f"{VS}/Body/Body-Mirrored/21-Body-E-Mirrored.stl", two=f"{VS}/Weapons/Weapons-RawSTL/70-Gun-1-A.stl",
       head=f"{AM}/Helmet-Heads/12-Head-4.stl", pack=f"{IV}/BackPacks-Raw/266-BackPack-1.stl",
       shins=(("R", f"{BG}/Shin-Pads/Shin-Pads-RawSTL/29-Shin-Pad-1.stl"), ("L", f"{BG}/Shin-Pads/Shin-Pads-Mirrored/29-Shin-Pad-1-Mirrored.stl")))
marine("X7", (540, 0, 0), f"{OR}/Torsos/RawSTL/12-Torso-ULTRA.stl", f"{TM}/Legs/Legs-Raw-STL/4-Legs-2.stl", rock=f"{TM}/Accesories/Raw-STL/42-TacticalRock.stl",
       arms=(("R", f"{TM}/Arms/Arms-Raw-STL/19-Arm-5-R.stl"), ("L", f"{OR}/Arms/RawSTL-Mirrored-(Left)/14-Arm-2-Mirrored-A.stl")),
       hands=(("R", f"{OR}/Weapons/WeaponsRawSTL(Right)/37-Sword-A.stl", "Melee"), ("L", f"{IV}/Hands-Raw/Hand-Left/274-Hand-2-L.stl", "Hands")),
       grips=(("L", f"{OR}/Weapons/WeaponsRawSTL(Right)/42-AxeNoHand.stl"),),
       head=f"{TM}/Helmet/Helmet-Raw-STL/1-Helmet.stl", pack=f"{TM}/Backpack/Backpack-Raw-STL/11-Techmarine-Backpack.stl", topper=f"{TM}/Weapons/Weapons-Raw-STL/36-ForgeBolter.stl",
       pads=(("R", f"{OR}/ShoulderPads/RawSTL/1-ShoulderPad-R.stl"), ("L", f"{TM}/ShoulderPads/Shoulderpad-Raw-STL/9-ShoulderPad-L.stl")),
       shins=(("R", f"{OR}/ShinPads/RawSTL(Right)/18-ShinPad-ULTRA.stl"), ("L", f"{TM}/Shinpads/Shinpads-Raw-STL/8-Shinpad-L.stl")),
       belt=(f"{OR}/Accesories/AccesoriesRawSTL/48-Pouch-1.stl",))
marine("X8", (600, 0, 0), f"{TM}/Chest/Chest-Raw-STL/2-Chest.stl", f"{OR}/Legs/RawSTL/2-Legs-B.stl",
       arms=(("R", f"{OR}/Arms(WithHandles)/RawSTL(Right)/8-ArmWithHandle-Right-B.stl"), ("L", f"{AM}/Arms/109-Arm-7-L-B.stl")),
       hands=(("L", f"{TM}/Weapons/Weapons-Raw-STL/35-GravPistol.stl", "Pistols"),),
       head=f"{IV}/Helmets-Heads-Raw/1-Helmet-1.stl", pack=f"{AM}/JumpPacks/56-JumpPack-2.stl",
       pads=(("L", f"{OR}/ShoulderPads/RawSTL/14-ShoulderPad-IH-2.stl"),),
       shins=(("R", f"{IV}/ShinPad-Raw/42-ShinPad-A.stl"), ("L", f"{IV}/ShinPad-Raw/ShinPad-Left/42-ShinPad-A-L.stl")),
       belt=(f"{TM}/Accesories/Raw-STL/39-PistolHolster-1.stl", f"{OR}/Accesories/AccesoriesRawSTL/51-PuritySeal-1.stl"))
print("\n%-5s %-11s %-6s %-6s %9s %9s %7s" % ("model", "joint", "part", "on", "closest", "deepcut", "touch"))
for lab, j, ck_, pk, m in rows:
    print("%-5s %-11s %-6s %-6s %s" % (lab, j, ck_, pk, "   no geometry near the joint" if m is None else "%8.2fmm %8.2fmm %6.0f%%" % (m[0], m[1], 100 * m[2])))
json.dump(rows, open(OUT + "/cross_rows.json", "w"))
V = {"front": (0, 1, 0.1), "q": (0.7, 0.7, 0.2), "side": (1, 0, 0.05), "back": (-0.4, -1, 0.25)}
COL = {"AM": rend.GREY, "Vet": rend.BLUE, "BG": rend.BLUE, "IV2": rend.ORANGE, "CJ": (0.55, 0.8, 0.5, 1), "OR": (0.75, 0.55, 0.85, 1), "TM": (0.9, 0.35, 0.35, 1)}
for nm, root in marines:
    obs = [o for o in [root] + list(T._descendants(root)) if o.type == 'MESH' and not o.hide_get()]
    rend.render(scene, OUT, "cross_" + nm, obs, V, [COL.get(str(o.get("tiow_kit", "")), rend.GREY) for o in obs])
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/cross_test.blend")
print("\nFAILS:", fails)
