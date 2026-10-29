import re, json
TYPES = json.loads(open('/home/claude/tiow_blender/_library.json').read())['partTypes']
T = {a: k for k, al in TYPES.items() for a in al}
STRIP = ["raw","rawstl","stl","mirrored","mirror","sergeant","support","supported","presupported"]
def library_part_type(path):
    for f in reversed(path.split('/')[:-1]):
        w = re.sub(r'[_\-\s]+', ' ', f.lower()).strip().split(' ')
        while len(w) > 1 and w[-1] in STRIP: w.pop()
        t = T.get(' '.join(w))
        if t: return t
    return None
RULES = [('Shoulder Pads', r'shoulder.?pad|pauldron'), ('Shin Pads', r'shin.?pad'), ('Knee Pads', r'knee.?pad'), ('Heads', r'helmet|head'),
         ('Chests', r'chest|torso'), ('Legs', r'legs?'), ('Jump Packs', r'jump.?pack|jet.?pack'), ('Backpacks', r'back.?pack'), ('Arms', r'arm(?!or)'),
         ('Weapons', r'weapon|sword|gun|bolter|pistol|rifle|melta|axe|hammer|fist|claw|spear'), ('Bodies', r'body')]
def guess_category(path):
    t = library_part_type(path)
    if t: return t
    bits = path.split('/')[:-1][::-1]; fn = path.split('/')[-1]
    for text in [fn] + bits:
        for name, rx in RULES:
            if re.search(rx, text, re.I): return name
    return 'Unclassified'
