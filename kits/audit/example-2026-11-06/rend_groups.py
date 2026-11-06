import bpy, sys
sys.path.insert(0, "/home/claude/kitbash/tests")
import rend
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/example issues.blend")
sc = bpy.context.scene
sc.world.color = (0.9, 0.9, 0.9)
cam = rend.setup(sc, 600)
def ob(prefix): return next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith(prefix))
CH, LG, BS = ob("MarFil Techmarine - Chest"), ob("MarFil Intercessor - Legs 1"), ob("base_32")
BP, PR, PL = ob("BBoosty Medusas Mortals - Backpack"), ob("BBoosty Medusas Mortals - Shoulder Pad Studs"), ob("BBoosty Medusas Mortals - Shoulder Pad Bolts")
AR, AL = ob("MarFil Assault - Arm 7B R"), ob("MarFil Intercessor - Arm 1 L")
LC, BK, TN = ob("Marta Jul 2026 - Loincloth 5"), ob("MarFil Assault - Buckle"), ob("TN Mk10 Assault - Jump Pack")
HPL, HPR = ob("MarFil Assault - Hip Plate L"), ob("MarFil Assault - Hip Plate R")
V = {"front": (0, 1, 0), "back": (0, -1, 0), "right": (-1, 0, 0), "left": (1, 0, 0), "top": (0, 0, 1)}
groups = {
 "waist": ([CH, LG], [rend.BLUE, rend.ORANGE], ["front", "right", "left", "back"]),
 "base": ([LG, BS], [rend.ORANGE, rend.GREY], ["front", "right"]),
 "pack": ([CH, BP], [rend.BLUE, rend.GREEN], ["back", "top", "right"]),
 "pads": ([CH, AR, AL, PR, PL], [rend.BLUE, rend.GREY, rend.GREY, rend.PURPLE, rend.RED], ["front", "back", "top", "right", "left"]),
 "belt": ([LG, LC, BK, HPL, HPR], [rend.ORANGE, rend.RED, rend.GREEN, rend.GREY, rend.GREY], ["front", "right"]),
 "beltback": ([LG, TN, HPL, HPR], [rend.ORANGE, rend.PURPLE, rend.GREY, rend.GREY], ["back", "right", "top"]),
}
for g, (obs, cols, vs) in groups.items():
    rend.render(sc, "/home/claude/work/ex/r", g, obs, {v: V[v] for v in vs}, cols)
