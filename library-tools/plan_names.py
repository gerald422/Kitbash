"""Readable names for the Kitbash Library: "<Maker> <Kit> - <Part>".

    python3 plan_names.py _sources.csv names.csv [kits.csv]

Reads the library index (library path, type) and writes names.csv:
library path, new name, new path, maker, kit, type, why. Folders stay as they
are; only file names change. kits.csv (folder -> short kit name) overrides the
table below, so a kit's short name can be changed and the plan run again.
Bases and Bits keep their names.
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

MAKERS = {"Mar Fil": "MarFil", "Marta PunkGirl": "Marta", "Turtle Ninja": "TN", "BBoosty": "BBoosty",
          "CyberBrush": "CyberBrush", "Springles": "Springles"}
# "maker - range\kit folder" -> short kit name; "*" = name the kit by its first subfolder (TN's builders)
KITS = {
    "BBoosty - Heresy\\Chaplain": "Chaplain", "BBoosty - Heresy\\Consul": "Consul",
    "BBoosty - Heresy\\IH_Shoulderpads": "Iron Hands Pads", "BBoosty - Heresy\\IronFather": "Iron Father",
    "BBoosty - Heresy\\Medusas Mortals": "Medusas Mortals", "BBoosty - Heresy\\Praetor with Paragon Blade": "Praetor",
    "BBoosty - Heresy\\ServoArms": "Servo Arms",
    "CyberBrush - Tacticus\\Light armor Marine torso & Tactical": "Light Armour",
    "CyberBrush - Tacticus\\Space Bugs Hunters": "Bug Hunters",
    "Mar Fil - Tacticus\\AssaultMarines-V2": "Assault", "Mar Fil - Tacticus\\BackPackUpdate": "Backpacks",
    "Mar Fil - Tacticus\\ChaplainOnBike-Bits": "Bike Chaplain", "Mar Fil - Tacticus\\ChaplainWithJumpPack": "Jump Chaplain",
    "Mar Fil - Tacticus\\HelmetsUpdate": "Helmets", "Mar Fil - Tacticus\\Intercessors-V2": "Intercessor",
    "Mar Fil - Tacticus\\Outriders": "Outrider", "Mar Fil - Tacticus\\Techmarine": "Techmarine",
    "Mar Fil - Tacticus\\VeteranBladeSquad": "Bladeguard", "Mar Fil - Tacticus\\VeteranSquad": "Veteran",
    "Marta PunkGirl - Gravis\\Aggressor V2": "Aggressor", "Marta PunkGirl - Gravis\\Heavy GURLS": "Heavy Gurls",
    "Marta PunkGirl - Gravis\\angry-heavy-gurl-v220240603-1-npo6h3": "Angry Heavy Gurl",
    "Marta PunkGirl - Gravis\\thicc BOI with BASE terrain 40mm": "Thicc Boi",
    "Marta PunkGirl - Gravis\\update heavy flying": "Heavy Flying",
    "Marta PunkGirl - Phobos\\phobois part3-eliminators-last update 05.01.23": "Eliminators",
    "Marta PunkGirl - Tacticus\\04 April 2025": "Apr 2025", "Marta PunkGirl - Tacticus\\07 July 2025": "Jul 2025",
    "Marta PunkGirl - Tacticus\\10 Oct 2025": "Oct 2025", "Marta PunkGirl - Tacticus\\2023.09 Monster Hunter": "Monster Hunter",
    "Marta PunkGirl - Tacticus\\40 base with wall": "Base Wall",
    "Marta PunkGirl - Tacticus\\47 January Asian theme 2026": "Jan 2026",
    "Marta PunkGirl - Tacticus\\48 February 2026": "Feb 2026", "Marta PunkGirl - Tacticus\\51 May 2026": "May 2026",
    "Marta PunkGirl - Tacticus\\52 June 2026": "Jun 2026", "Marta PunkGirl - Tacticus\\53 July 2026": "Jul 2026",
    "Marta PunkGirl - Tacticus\\55 September 2026": "Sep 2026", "Marta PunkGirl - Tacticus\\56 October 2026": "Oct 2026",
    "Marta PunkGirl - Tacticus\\Apothecary": "Apothecary", "Marta PunkGirl - Tacticus\\BT shoulder and helms free": "Black Templars",
    "Marta PunkGirl - Tacticus\\Bits Blood Angels Pt2": "Blood Angels 2", "Marta PunkGirl - Tacticus\\Bits Death Watch": "Deathwatch",
    "Marta PunkGirl - Tacticus\\Bits Imperial Fist": "Imperial Fists", "Marta PunkGirl - Tacticus\\Bits Imperial Fist Pt2": "Imperial Fists 2",
    "Marta PunkGirl - Tacticus\\Bits Salamander": "Salamanders", "Marta PunkGirl - Tacticus\\Bits Ultramarine": "Ultramarines",
    "Marta PunkGirl - Tacticus\\Bits Ultramarine Pt2": "Ultramarines 2",
    "Marta PunkGirl - Tacticus\\Captain with Relic Shield": "Relic Captain", "Marta PunkGirl - Tacticus\\GURL bionics": "Gurl Bionics",
    "Marta PunkGirl - Tacticus\\GURLS": "Gurls", "Marta PunkGirl - Tacticus\\Regular sharks May25": "Sharks",
    "Marta PunkGirl - Tacticus\\SALE files August 2025": "Aug 2025", "Marta PunkGirl - Tacticus\\SW Bits 10 October 2024": "Space Wolves",
    "Marta PunkGirl - Tacticus\\Techmarine": "Techmarine", "Marta PunkGirl - Tacticus\\Techmarine V2": "Techmarine V2",
    "Marta PunkGirl - Tacticus\\bionics-for-bois-and-gurls-september-23": "Bionics",
    "Marta PunkGirl - Tacticus\\d2420251125-1-bd6hiy": "Executions",
    "Marta PunkGirl - Tacticus\\ghostrider models June 2026": "Ghostrider",
    "Marta PunkGirl - Tacticus\\loyalty reward (6 no3)": "Loyalty 6-3", "Marta PunkGirl - Tacticus\\loyalty-reward-6m-1": "Loyalty 6-1",
    "Marta PunkGirl - Tacticus\\loyalty-reward-9m-2": "Loyalty 9-2",
    "Marta PunkGirl - Tacticus\\monster-hunter-boi-september-23": "Monster Hunter Boi",
    "Marta PunkGirl - Tacticus\\phobia bases": "Phobia",
    "Marta PunkGirl - Terminator\\Bits Space Wolf Terminator": "SW Terminator",
    "Marta PunkGirl - Terminator\\Gloomy Angels Terminators": "Gloomy Angels",
    "Marta PunkGirl - Weapons\\Primary Combo Weapons": "Combo Weapons",
    "Springles - Heresy\\patternC arms": "Pattern C", "Springles - Heresy\\patternP arms": "Pattern P",
    "Springles - Heresy\\patternS arms": "Pattern S",
    "Springles - Weapons\\assault cannon": "Assault Cannon", "Springles - Weapons\\banestrike weapons": "Banestrike",
    "Springles - Weapons\\carsoran power axes": "Carsoran Axes", "Springles - Weapons\\heavy weapons": "Heavy Weapons",
    "Springles - Weapons\\special weapons": "Special Weapons", "Springles - Weapons\\umbra bolters": "Umbra Bolters",
    "Turtle Ninja - Heresy\\Legion Moritat": "Moritat", "Turtle Ninja - Heresy\\Librarian Custom": "Librarian",
    "Turtle Ninja - Heresy\\Mk2-6 Builder": "*", "Turtle Ninja - Heresy\\Mk4 Tactical Squad": "Mk4 Tactical",
    "Turtle Ninja - Heresy\\Mk6 Addon 1": "Mk6 Addon", "Turtle Ninja - Heresy\\Mk6 Assault Addon 1": "Mk6 Assault",
    "Turtle Ninja - Heresy\\Mk7-8 Assault Intercessors Addon 1": "Mk7-8 Assault", "Turtle Ninja - Heresy\\Mk7-8 Builder": "Mk7-8",
    "Turtle Ninja - Tacticus\\Mk10 Assault Intercessor + Jumppack Addon": "Mk10 Assault",
    "Turtle Ninja - Tacticus\\Mk10 Leg (Update 1)": "Mk10 Legs",
}
# the part-type folder's word, for a file whose name doesn't say what it is
TYPE_WORD = {"Arms": "Arm", "Legs": "Legs", "Heads": "Head", "Chests": "Torso", "Melee": "Melee", "Pistols": "Pistol",
             "Shoulder Pads": "Shoulder Pad", "Knee Pads": "Shin Pad", "Two-Handed Guns": "Gun", "Two-Handed Melee": "Melee",
             "Two-Handed Held": "Gun", "Hand-less Weapons": "Weapon", "Accessories": "Accessory", "Loincloths": "Loincloth", "Backpacks": "Backpack",
             "Jump Packs": "Jump Pack", "Shields": "Shield", "Hands": "Hand", "Heavy Weapons": "Heavy Weapon",
             "Backpack Toppers": "Topper", "Heavy Weapon Cables": "Cable", "Cables": "Cable", "Servo Arms": "Servo Arm",
             "Grenades": "Grenade", "Seals": "Seal", "Bike Parts": "Bike Part", "Bikes": "Bike", "Cloaks": "Cloak",
             "Mechadendrites": "Mechadendrite", "Forearm Armour": "Forearm", "Pack Fins": "Fin", "Adapters": "Adapter"}
# words split out of run-together names, and the makers' own spellings
WORDS = {"shinpad": "Shin Pad", "shinpads": "Shin Pads", "chin": "Shin", "shoulderpad": "Shoulder Pad",
         "kneepad": "Knee Pad", "powersword": "Power Sword", "powerfist": "Power Fist", "jumppack": "Jump Pack",
         "backpack": "Backpack", "chainsword": "Chain Sword", "boltpistol": "Bolt Pistol", "termi": "Termi",
         "thicc": "Thicc", "gurl": "Gurl", "gurls": "Gurls", "boi": "Boi", "2h": "2H", "hw": "HW", "ih": "IH",
         "da": "DA", "bt": "BT", "sw": "SW", "apoth": "Apoth", "mk": "Mk", "mh": "MH", "hm": "HM",
         "lm": "LM", "um": "UM", "dw": "DW", "ba": "BA", "if": "IF", "sa": "SA"}
# folders that say nothing about the part (dropped when a folder is used to tell parts apart)
FILLER = {"bits", "rawstl", "raw", "stl", "stls", "extra", "update", "updates", "part", "files", "individual", "dual", "the",
          "and", "with", "of", "for", "v2", "marta", "punkgirl", "intercessors", "intercessors-bits"}
SIDE_WORDS = {"r": "R", "l": "L", "right": "R", "left": "L"}
# words that say what the part is: never taken out for repeating the kit's name
PART_WORDS = {"arm", "arms", "leg", "legs", "torso", "chest", "body", "helmet", "head", "pad", "pads", "shoulder",
              "shin", "knee", "pistol", "sword", "axe", "hammer", "fist", "hand", "backpack", "pack", "jump", "belt",
              "shield", "gun", "bolter", "cannon", "upper", "lower", "cable", "grenade", "seal", "cloak", "booster"}


def split_words(s):
    """'Mirrored-170-PowerFist-B-4' -> ['Mirrored', '170', 'Power', 'Fist', 'B', '4']"""
    s = s.replace("(", " ( ").replace(")", " ) ")
    s = re.sub(r"(?<![A-Za-z0-9.])2\.0(?![\d.])", " ", s)   # TN's '2.0' version tag ('Mk10_2.0_Arm')
    s = re.sub(r"\b([A-Z]{4,})([a-z]{3,})\b", r"\1 \2", s)  # DEATHgirls -> DEATH girls (IHShoulderpad stays)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)              # camelCase
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)        # HWBolter -> HW Bolter
    s = re.sub(r"(?<=[A-Za-z]{3})(?=\d)|(?<=\d)(?=[A-Za-z]{3})", " ", s)  # Assault213 -> Assault 213 (Mk8, V2 stay)
    return [w for w in re.split(r"[\s_\-,]+|(?<!\d)\.|\.(?!\d)", s) if w]   # '2.1' stays


def word(w):
    lw = w.lower()
    if lw in WORDS:
        return WORDS[lw]
    if w in ("(", ")") or re.fullmatch(r"\d+", w) or re.fullmatch(r"[A-Z]{2}", w):
        return w
    if re.fullmatch(r"[a-z]\d*|\d+[a-z]", w):
        return w.upper()
    return w[:1].upper() + w[1:].lower() if w.isupper() or w.islower() else w[:1].upper() + w[1:]


def part_name(stem, kitwords, sub, tfolder, numbered=False, kitlead=(), kitmarks=frozenset()):
    """(part words, side, catalogue number) from a file name. numbered: the
    maker puts a catalogue number in front (Mar Fil's '77-')."""
    side = None
    if re.search(r"(?i)mirrored|mirorred", stem):
        side = "L"
        stem = re.sub(r"(?i)[ _-]*\(?mirr?or+ed\)?", " ", stem)
    stem = re.sub(r"^Weapons-Assault(?=\d)", "", stem)        # Mar Fil's 'Weapons-Assault213-PlasmaPistol-L'
    m = re.match(r"^(R|L)(arm|Arm|ARM|hand|Hand|leg|Leg)(.*)$", stem)          # BBoosty 'RArm3'
    if m:
        side, stem = m.group(1), m.group(2) + " " + m.group(3)
    stem = re.sub(r"(?<![A-Za-z])([RL])(arm)(?=\b|\d|\s|$)", lambda m: m.group(1) + " " + m.group(2), stem, flags=re.I)  # 'Rarm 5'
    ws = []
    sw = split_words(stem)
    for lead in kitlead:                     # the kit's own name in front ('patternC heavy Larm 3', 'Mk10_Assault_...')
        if len(sw) > len(lead) + 1 and [w.lower() for w in sw[:len(lead)]] == lead:
            if not any(w in PART_WORDS for w in lead):   # 'assault cannon belt fed' keeps its name
                sw = sw[len(lead):]
            break
    for w in sw:                             # run-together words split ('ShinPad' -> 'Shin Pad')
        ws += WORDS[w.lower()].split() if w.lower() in WORDS and " " in WORDS[w.lower()] else [w]
    cat = None
    if numbered and ws and re.fullmatch(r"\d+", ws[0]) and len(ws) > 1:      # Mar Fil's catalogue number
        cat = ws.pop(0)
    out, sides = [], []
    for w in ws:
        lw = w.lower()
        if lw in SIDE_WORDS and (len(ws) > 1):
            sides.append(SIDE_WORDS[lw])
            continue
        out.append(w)
    if sides:
        side = " ".join(sides) if len(set(sides)) > 1 else sides[-1]
    # the kit's own words in front ('Space Bug Hunters Fist 4'), and a mark the kit
    # already names ('Mk6_Arm_D_3' in Mk6 Addon), unless that leaves one word
    i = 0
    while i < len(out) - 1 and out[i].lower() in kitwords and out[i].lower() not in PART_WORDS:
        i += 1
    if i and out[i].lower() in PART_WORDS and (out[i].lower() in kitwords or singular(out[i].lower()) in kitwords):
        i = 0                                # 'Servo Arm ...' in Servo Arms, 'Carsoran Power Axe' in Carsoran Axes
    cand = [w for w in out[i:] if not (re.fullmatch(r"(?i)mk\d+", w) and w.lower() in kitmarks)]
    if sum(1 for w in cand if re.search(r"[A-Za-z0-9]", w)) >= 2 or not any(re.search(r"[A-Za-z]{2,}", w) for w in out):
        out = cand
    out = [word(w) for w in out]
    # a run of words said twice ('thiccboi priest thiccboi priest')
    for n in (3, 2, 1):
        k = 0
        while k + 2 * n <= len(out):
            if [x.lower() for x in out[k:k + n]] == [x.lower() for x in out[k + n:k + 2 * n]] and \
                    not all(re.fullmatch(r"\d+", x) for x in out[k:k + n]):
                del out[k + n:k + 2 * n]
            else:
                k += 1
    # join a number and its letter, or a letter and its number: '6 B' -> '6B', 'A 1' -> 'A1'
    j = []
    for w in out:                            # a letter and its number first ('Pose 3 C 5' -> 'Pose 3 C5')
        if j and re.fullmatch(r"[A-Z]", j[-1]) and re.fullmatch(r"\d+", w):
            j[-1] += w
        else:
            j.append(w)
    k = []
    for w in j:                              # then a number and its letter ('Legs 6 B' -> 'Legs 6B')
        if k and re.fullmatch(r"\d+", k[-1]) and re.fullmatch(r"[A-Z]", w):
            k[-1] += w
        else:
            k.append(w)
    j = k
    generic = {"new", "version", "update", "updated", "generic", "free", "alt", "set"}
    if not any(re.search(r"[A-Za-z]{2,}", w) and w.lower() not in generic for w in j):
        # nothing says what it is ('4', '114-Mirrored'): its folders do
        lead = [word(singular(w)) for w in sub if w.lower() not in kitwords and w.lower() not in FILLER
                and re.search(r"[A-Za-z]{2,}", w)]
        lead = [w for i, w in enumerate(lead) if w not in lead[:i]]
        tw = TYPE_WORD.get(tfolder, tfolder)
        if lead and (tw in ("Melee", "Accessory") or tw.lower().rstrip("s") in {x.lower().rstrip("s") for x in lead}):
            tw = ""
        if cat and not j:
            j = [cat]
            cat = None
        j = lead + ([tw] if tw else []) + j
    return j, side, cat


def singular(w):
    return re.sub(r"(?i)(?<=[a-z])(?<!s)s$", "", w) if len(w) > 3 else w


def main():
    src, out_path = sys.argv[1], sys.argv[2]
    kits = dict(KITS)
    if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
        with open(sys.argv[3], encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("kit folder") and r.get("short name"):
                    kits[r["kit folder"]] = r["short name"]
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    plan = []
    for r in rows:
        p = r["library path"]
        parts = p.split("\\")
        top = parts[0]
        stem, ext = os.path.splitext(parts[-1])
        if top in ("Bases", "Bits") or len(parts) < 3:
            plan.append(dict(old=p, name=stem, maker="", kit="", type=r["type"], why="kept (bases and adaptors)"))
            continue
        maker = MAKERS.get(top.split(" - ")[0], top.split(" - ")[0])
        kf = "\\".join(parts[:2])
        kit = kits.get(kf)
        sub = parts[2:-2]                    # folders between the kit and the type folder
        if kit == "*":
            kit, sub = (sub[0], sub[1:]) if sub else (parts[1], sub)
        if not kit:
            kit = re.sub(r"[_-]+", " ", parts[1]).title()
        kitwords = {w.lower() for w in split_words(kit) + split_words(parts[1])
                    if re.search(r"[A-Za-z]{2,}", w) and not re.fullmatch(r"(?i)mk\d+", w)}
        kitwords |= {singular(w) for w in kitwords}
        kitmarks = {w.lower() for w in kit.split() if re.fullmatch(r"(?i)mk\d+", w)}
        kitwords |= kitmarks
        subw = [w for s in sub for w in split_words(s)]
        kitlead = [[w.lower() for w in split_words(kit)], [w.lower() for w in split_words(parts[1])]]
        j, side, cat = part_name(stem, kitwords, subw, parts[-2], numbered=(maker == "MarFil"), kitlead=kitlead,
                                kitmarks=kitmarks)
        name = f"{maker} {kit} - {' '.join(j)}" + (f" {side}" if side else "")
        near = ""
        for f in reversed(sub):              # the nearest folder that says something
            ws_ = [word(w) for w in split_words(f)]
            if any(w.lower() not in FILLER for w in ws_):
                near = " ".join(ws_)
                break
        plan.append(dict(old=p, name=name, maker=maker, kit=kit, type=r["type"], why="", _cat=cat, _sub=subw, _near=near,
                         _kitwords=kitwords, _side=side, _j=j))
    # two files with the same name: tell them apart by catalogue number, then folder, then a count
    for rnd in range(3):
        groups = defaultdict(list)
        for e in plan:
            groups[e["name"].lower()].append(e)
        clash = [g for g in groups.values() if len(g) > 1]
        if not clash:
            break
        for g in clash:
            for e in g:
                if "_j" not in e:
                    continue
                if rnd == 0 and e["_cat"]:
                    e["name"] = e["name"] + f" #{e['_cat']}"
                    e["why"] = "catalogue number added (name was shared)"
                elif rnd == 1 and e["_near"]:
                    e["name"] = e["name"] + f" ({e['_near']})"
                    e["why"] = "folder added (name was shared)"
            if rnd == 2:
                for i, e in enumerate(sorted(g, key=lambda x: x["old"])):
                    if i:
                        e["name"] = e["name"] + f" ({i + 1})"
                        e["why"] = "count added (name was shared)"
    bad = re.compile(r'[<>:"/\\|?*]')
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["library path", "new name", "new path", "maker", "kit", "type", "note"])
        for e in plan:
            name = re.sub(r"\s+\)", ")", re.sub(r"\(\s+", "(", re.sub(r"\s+", " ", e["name"]))).strip()
            name = bad.sub("-", name)
            ext = os.path.splitext(e["old"])[1]
            newp = "\\".join(e["old"].split("\\")[:-1] + [name + ext])
            w.writerow([e["old"], name, newp, e["maker"], e["kit"], e["type"], e["why"]])
    names = Counter(e["name"].lower() for e in plan)
    print(len(plan), "files;", sum(1 for e in plan if e["why"].startswith("kept")), "kept;",
          sum(1 for v in names.values() if v > 1), "names still shared")


if __name__ == "__main__":
    main()
