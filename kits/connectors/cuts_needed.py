"""Which connectors Josh still has to cut (or pads to place), across every maker: docs/cuts-needed.md. No Blender.

    python kits/connectors/cuts_needed.py [--lib "D:/Kitbash Library"]

One cut a maker folder (maker + armour type) and joint, as Josh set it (Nov 14); the search then shows which kits
of that folder share it (Mar Fil: the Veteran / Bladeguard neck is its own design, notes 102), so a second cut for
a kit only follows a first run. Read from the page index (types, fits, sockets) and, for a maker that has a
connector config (kits/connectors/*.json), the written seat.py runs: a part a written run seated (sure, or a look
it wrote) is covered; a part the search found nothing on, or only a look it did not write, still needs its cut.

Left out on purpose: torsos (they stay on their sockets), accessories and belt bits (last, Josh Nov 15), bases,
cables and the other types the connector plan doesn't cover (counted at the end), Marta heads (deferred), Turtle
Ninja "Rigging Required" folders, weapons without a hand (Josh, Nov 15: not used, as Marta's torsos), parts hidden
from the page (_hidden.txt); for now (Josh, Nov 15) Marta Terminator / Gravis / Phobos and every maker's plain arms but Mar Fil's. A weapon that comes with its hand mates at the wrist: one cut per wrist style for every maker (Josh, Nov 15: 3 styles;
only the mating surface and the roll matter, not the rest of the mesh); a backpack at its mount face, one cut a folder."""
import sys, os, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# the joint a part type hangs from: what Josh cuts (or places), and which connector names in a config cover it
JOINTS = {
    "Arms": [("shoulder disc", "cut the shoulder disc on one arm", ("shoulder disc",)),
             ("pad spot", "cut the pad spot on that arm", ("pad spot",)),
             ("wrist", "cut the wrist on that arm", ("wrist A", "wrist B"))],
    "Legs": [("waist", "cut the waist on one legs", ("waist",)),
             ("shin spot", "cut the shin spot on those legs", ("shin spot",))],
    "Shoulder Pads": [("pad inside", "place one pad on the pad spot (the inside is cut from it)", ("pad inside",))],
    "Knee Pads": [("shin pad inside", "place one shin pad on the shin spot", ("shin pad inside",))],
    "Heads": [("neck", "cut the neck on one head", ("neck",))],
    "Backpacks": [("backpack mount", "cut the mount face (only what meets the back) on one backpack, as it sits on a Mar Fil torso's back", ("backpack mount",))],
    "Jump Packs": [("jump pack mount", "cut the mount on one jump pack", ("jump pack mount",))],
    "Two-Handed Guns": [("shoulder disc", "cut the shoulder disc on one arm", ("shoulder disc",))],
    "Two-Handed Melee": [("shoulder disc", "cut the shoulder disc on one arm", ("shoulder disc",))],
    "Heavy Weapons": [("shoulder disc", "cut the shoulder disc on one arm", ("shoulder disc",))],
}
for t in ("Hands", "Melee", "Pistols", "Shields", "Two-Handed Held"):     # they come with their hand: it mates at the wrist
    JOINTS[t] = [("hand at wrist", "one cut per wrist style, for every maker at once (see the top)", ("hand at wrist A",))]
HANDLESS = ("no hand", "handless", "hand-less", "without hand")       # not used (Josh, Nov 15): weapons without a wrist
GLOBAL = ("hand at wrist",)    # cut once per style for every maker (Josh, Nov 15: 3 wrist styles in the files), not per maker folder
WRIST_STYLES = 3
HINT = {"shoulder disc": "Arm", "pad spot": "Arm", "wrist": "Arm", "waist": "Legs", "shin spot": "Legs", "pad inside": "Pad",
        "shin pad inside": "Pad", "neck": "Hel", "backpack mount": "Pack", "jump pack mount": "Pack", "hand at wrist": ""}
# scope (Josh, Nov 15, notes 108): the base body is mostly Mar Fil, with weapons and customisation on top
NOT_NOW = ("Marta PunkGirl - Terminator", "Marta PunkGirl - Gravis", "Marta PunkGirl - Phobos")   # no Terminators (or Gravis, Phobos) for now
ARMS_FROM = ("Mar Fil",)    # plain arms: Mar Fil only (Josh, Nov 15); other makers' two-handed weapons (they carry their
                            # arms) and weapons with a hand are used, and Marta's legs (some unique poses); a posed arm may be added by name later
LATER = {"Accessories", "Plate Accessories", "Loincloths", "Trophies", "Seals", "Hip Plates", "Buckles", "Tabards"}
SKIP = {"Chests", "Bases"}


def opt(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def hidden(lib):
    paths, words, types = set(), [], set()
    try: lines = open(lib + "/_hidden.txt", encoding="utf-8-sig").read().splitlines()
    except OSError: lines = []
    for l in lines:
        l = l.strip()
        if not l or l.startswith("#"): continue
        if l.lower().startswith("word:"): words.append(l[5:].strip().lower())
        elif l.lower().startswith("type:"): types.add(l[5:].strip())
        else: paths.add(l.lower())
    return lambda e: e["path"].lower() in paths or e["type"] in types or any(w in e["name"].lower() for w in words)


def kit_of(path):
    p = path.split("\\")
    if len(p) < 3: return "(loose)"
    return p[1] + (" / " + p[2] if p[1].endswith("Builder") and len(p) > 3 else "")


def covered(lib):
    """{library path (backslashes, .stl): set of connector names a written run seated it by}, {maker: connectors}"""
    have, makers, searched = collections.defaultdict(set), {}, collections.defaultdict(set)
    for f in glob.glob(os.path.join(HERE, "*.json")):
        c = json.load(open(f, encoding="utf-8"))
        if isinstance(c, dict) and c.get("maker") and isinstance(c.get("types"), dict) and not c.get("origins_only"):   # seat.py configs only
            makers.setdefault(c["maker"], set()).update(x["name"] for v in c["types"].values() for x in v); searched[c["maker"]].update(c["types"])
    for T in sorted(glob.glob(lib + "/_backups/connectors-*")):
        if not os.path.exists(T + "/written.json"): continue
        wrote = set(json.load(open(T + "/written.json", encoding="utf-8"))["wrote"])
        for p in json.load(open(T + "/plan.json", encoding="utf-8")):
            k = p["rel"].replace("/", "\\") + ".stl"
            for name, f in (p.get("found") or {}).items():
                if f.get("level") == "sure" or (f.get("level") == "look" and p["rel"] in wrote): have[k].add(name)
        for c in json.load(open(T + "/work/config.json", encoding="utf-8"))["types"].values():     # reference parts: where the
            for x in c: have[x["ref"].replace("/", "\\") + ".stl"].update(y["name"] for y in c)   # type's connectors were cut
    return have, makers, searched


def main():
    lib = opt("--lib", "D:/Kitbash Library")
    idx = json.load(open(lib + "/_builder/index.json", encoding="utf-8"))
    is_hidden = hidden(lib); have, makers, searched = covered(lib)
    unsearched = collections.defaultdict(collections.Counter)                   # maker -> (type, connector) -> parts: no cut, a search
    need = collections.defaultdict(lambda: collections.defaultdict(list))         # maker -> (joint, how) -> [entries]
    later, other, done = collections.Counter(), collections.Counter(), collections.Counter()
    notnow, noarms = collections.Counter(), collections.Counter()
    for e in idx["parts"]:
        maker = e["path"].split("\\")[0]; t = e["type"]
        if is_hidden(e) or "rigging required" in e["path"].lower() or t in SKIP: continue
        if maker.startswith("Marta") and t == "Heads": continue
        if maker in NOT_NOW: notnow[maker] += 1; continue
        if t == "Arms" and not maker.startswith(ARMS_FROM): noarms[maker] += 1; continue
        if t == "Hand-less Weapons" or any(w in e["name"].lower() for w in HANDLESS): continue
        if t in LATER: later[maker] += 1; continue
        if t not in JOINTS: other[t] += 1; continue
        for joint, how, names in JOINTS[t]:
            if joint == "pad spot" and e.get("noPad"): continue
            if joint == "wrist" and e.get("noHand"): continue
            if joint == "shin spot" and not any(s["t"].startswith("Shin") for s in e.get("sockets") or []): continue
            if have.get(e["path"], set()) & set(names): done[maker] += 1; continue
            own = set(names) & makers.get(maker, set())
            if own and t not in searched[maker]: unsearched[maker][(t, sorted(own)[0])] += 1; continue
            need[maker][joint].append(e)
    W = []; w = W.append
    PLACE = ("pad inside", "shin pad inside")
    glob_wait = collections.Counter({m: sum(len(need[m][j]) for j in GLOBAL if j in need[m]) for m in need})
    for m in list(need):
        for j in GLOBAL: need[m].pop(j, None)
        if not need[m]: del need[m]
    cnt = lambda m, k: sum(1 for j in need[m] if (j in PLACE) == (k == "place"))
    total = sum(cnt(m, "cut") for m in need) + WRIST_STYLES; places = sum(cnt(m, "place") for m in need)
    w("# Connectors still to cut"); w("")
    w("> **Scope (Josh, Nov 15 2026; it has been lost before, keep it):** the base body is mostly Mar Fil, with weapons and "
      "customisation added on top. **Terminators and Gravis are not part of this system**: there is no expectation that they "
      "work in it, as they would need their own base fits (their own torsos, sockets and joints). They, and Marta Phobos, are "
      "left out here. **Plain arms: Mar Fil only.** From the other makers only their two-handed weapons and weapons with a hand "
      "attached (a specific posed arm may be added by name later); Marta's legs stay in for their unique poses."); w("")
    w("Generated by `kits/connectors/cuts_needed.py` from the page index and the written `Seat connectors` runs; run it "
      "again after a cut. One cut a maker folder and joint first: the search then shows which kits share it (Mar Fil's "
      "Veteran / Bladeguard neck turned out to be its own), and only those that don't need a cut of their own. A pad "
      "or shin pad needs no cut: place one on the arm's pad spot / the legs' shin spot and its inside is taken from it. "
      "")
    w(""); w("**Weapons with a hand: one cut per wrist style, %d in all, for every maker** (Josh, Nov 15: there are 3 wrist styles in "
      "the files; the fit is the mating surface and the roll, the rest of the mesh doesn't matter). On one weapon of each style, "
      "sat on a Mar Fil arm with that wrist as it should be held, cut **only the wrist end** (what meets the arm), not the fingers "
      "or the hand around it. The search then finds that wrist end on every weapon of every maker. Two-handed pieces that carry "
      "their arms go by the shoulder disc instead. Weapons waiting: %s." % (WRIST_STYLES, ", ".join("%s %d" % x for x in glob_wait.most_common() if x[1])))
    if unsearched:
        w(""); w("**No cut needed, a search to run:** types whose connector already exists but that haven't been searched with it:")
        for m, c in unsearched.items(): w("- %s: %s." % (m, ", ".join("%s %d (the %s)" % (t, n, k) for (t, k), n in c.most_common())))
    w(""); w("**%d cuts (the %d wrist styles and %d by maker folder) and %d pads to place.** Torsos (stay on their sockets), accessories and belt "
             "bits (last), bases, Marta heads (deferred), plain arms other than Mar Fil's, Marta Terminator / Gravis / Phobos (not now), Turtle Ninja \"Rigging Required\" "
             "folders, weapons without a hand (not used) and hidden parts are left out." % (total, WRIST_STYLES, total - WRIST_STYLES, places)); w("")
    w("| Maker folder | Cuts | Pads to place | Weapons waiting on the wrist styles | Other parts waiting | Already seated by a connector |"); w("|---|---|---|---|---|---|")
    order = sorted(need, key=lambda m: -sum(len(v) for v in need[m].values()))
    for m in order: w("| %s | %d | %d | %d | %d | %d |" % (m, cnt(m, "cut"), cnt(m, "place"), glob_wait[m], sum(len(v) for v in need[m].values()), done[m]))
    for m in order:
        w(""); w("## %s" % m); w("")
        if m in makers: w("Has connectors already (%s); these are what the search didn't find, kit by kit." % ", ".join(sorted(makers[m]))); w("")
        w("| Joint | What to do | Parts | Kits (parts) | A part to cut it on |"); w("|---|---|---|---|---|")
        for joint, es in sorted(need[m].items(), key=lambda x: [j for t in JOINTS.values() for j, _, _ in t].index(x[0])):
            how = next(h for t in JOINTS.values() for j, h, _ in t if j == joint)
            kits = collections.Counter(kit_of(e["path"]) for e in es)
            fitted = [e for e in es if e.get("fits") and (e.get("side") in (None, "R")) and HINT[joint].lower() in e["name"].lower()] or                      [e for e in es if HINT[joint].lower() in e["name"].lower()] or es
            best = max(kits, key=kits.get); ref = sorted([e for e in fitted if kit_of(e["path"]) == best] or fitted, key=lambda e: e["name"])[0]
            ks = ", ".join("%s (%d)" % (k, n) for k, n in kits.most_common(6)) + (", +%d more kits" % (len(kits) - 6) if len(kits) > 6 else "")
            w("| %s | %s | %d | %s | %s |" % (joint, how, len(es), ks, ref["name"]))
    w(""); w("## Not in the connector plan (left as they are)"); w("")
    w("Accessories and belt bits, last on purpose: " + ", ".join("%s %d" % x for x in later.most_common()) + ".")
    w(""); w("Other types: " + ", ".join("%s %d" % x for x in other.most_common()) + ".")
    w(""); w("Not for now (Josh, Nov 15): " + ", ".join("%s %d" % x for x in notnow.most_common()) + "; plain arms other than Mar Fil's: " +
             ", ".join("%s %d" % x for x in noarms.most_common()) + " (their two-handed weapons and weapons with a hand stay in).")
    out = os.path.join(REPO, "docs", "cuts-needed.md")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(W) + "\n")
    print("%s: %d cuts (%d wrist styles + %d by maker folder), %d pads to place, %d weapons on the wrist styles" % (out, total, WRIST_STYLES, total - WRIST_STYLES, places, sum(glob_wait.values())))
    for m in order: print("  %-36s %2d cuts, %d to place, %4d parts" % (m, cnt(m, "cut"), cnt(m, "place"), sum(len(v) for v in need[m].values())))


if __name__ == "__main__":
    main()
