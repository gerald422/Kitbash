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
from the page (_hidden.txt). A weapon that comes with its hand mates at the wrist: no cut, one of each hand design is
placed on the arm's wrist from its library fit (notes 104)."""
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
    "Backpacks": [("backpack mount", "cut the mount on one backpack", ("backpack mount",))],
    "Jump Packs": [("jump pack mount", "cut the mount on one jump pack", ("jump pack mount",))],
    "Two-Handed Guns": [("shoulder disc", "cut the shoulder disc on one arm", ("shoulder disc",))],
    "Two-Handed Melee": [("shoulder disc", "cut the shoulder disc on one arm", ("shoulder disc",))],
    "Heavy Weapons": [("shoulder disc", "cut the shoulder disc on one arm", ("shoulder disc",))],
}
for t in ("Hands", "Melee", "Pistols", "Shields", "Two-Handed Held"):     # they come with their hand: it mates at the wrist
    JOINTS[t] = [("hand at wrist", "no cut: one weapon of each hand design placed on the wrist from its library fit (notes 104)",
                  ("hand at wrist A",))]
HANDLESS = ("no hand", "handless", "hand-less", "without hand")       # not used (Josh, Nov 15): weapons without a wrist
HINT = {"shoulder disc": "Arm", "pad spot": "Arm", "wrist": "Arm", "waist": "Legs", "shin spot": "Legs", "pad inside": "Pad",
        "shin pad inside": "Pad", "neck": "Hel", "backpack mount": "Pack", "jump pack mount": "Pack", "hand at wrist": ""}
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
        if isinstance(c, dict) and c.get("maker"):
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
    for e in idx["parts"]:
        maker = e["path"].split("\\")[0]; t = e["type"]
        if is_hidden(e) or "rigging required" in e["path"].lower() or t in SKIP: continue
        if maker.startswith("Marta") and t == "Heads": continue
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
    PLACE, AUTO = ("pad inside", "shin pad inside"), ("hand at wrist",)
    kind = lambda j: "auto" if j in AUTO else "place" if j in PLACE else "cut"
    cnt = lambda m, k: sum(1 for j in need[m] if kind(j) == k)
    total = sum(cnt(m, "cut") for m in need); places = sum(cnt(m, "place") for m in need); autos = sum(cnt(m, "auto") for m in need)
    w("# Connectors still to cut"); w("")
    w("Generated by `kits/connectors/cuts_needed.py` from the page index and the written `Seat connectors` runs; run it "
      "again after a cut. One cut a maker folder and joint first: the search then shows which kits share it (Mar Fil's "
      "Veteran / Bladeguard neck turned out to be its own), and only those that don't need a cut of their own. A pad "
      "or shin pad needs no cut: place one on the arm's pad spot / the legs' shin spot and its inside is taken from it.")
    if unsearched:
        w(""); w("**No cut needed, a search to run:** types whose connector already exists but that haven't been searched with it:")
        for m, c in unsearched.items(): w("- %s: %s." % (m, ", ".join("%s %d (the %s)" % (t, n, k) for (t, k), n in c.most_common())))
    w(""); w("**%d cuts and %d pads to place, across %d maker folders; and %d weapon groups whose hand is taken from a fitted "
             "weapon, no work from you.** Torsos (stay on their sockets), accessories and belt "
             "bits (last), bases, Marta heads (deferred), Turtle Ninja \"Rigging Required\" folders, weapons without a hand (not used) and hidden parts are "
             "left out." % (total, places, len(need), autos)); w("")
    w("| Maker folder | Cuts | Pads to place | Weapon hands (no work) | Parts waiting | Already seated by a connector |"); w("|---|---|---|---|---|---|")
    order = sorted(need, key=lambda m: -sum(len(v) for v in need[m].values()))
    for m in order: w("| %s | %d | %d | %d | %d | %d |" % (m, cnt(m, "cut"), cnt(m, "place"), cnt(m, "auto"), sum(len(v) for v in need[m].values()), done[m]))
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
    out = os.path.join(REPO, "docs", "cuts-needed.md")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(W) + "\n")
    print("%s: %d cuts, %d pads to place, %d weapon hand groups (no work), %d maker folders" % (out, total, places, autos, len(need)))
    for m in order: print("  %-36s %2d cuts, %d to place, %4d parts" % (m, cnt(m, "cut"), cnt(m, "place"), sum(len(v) for v in need[m].values())))


if __name__ == "__main__":
    main()
