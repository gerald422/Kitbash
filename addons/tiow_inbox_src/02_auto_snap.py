# ---------------------------------------------------------------- auto-snap

# Part type -> the joint it goes on. "socket": the socket name, or a list
# of socket names to choose from (belt bits). "sided": the name ends in R or L,
# taken from the part's name ("77-Arm-1-R-B", "Arm_L_03", "LeftOrientated").
# "fit": snap with this fit type's offset on that socket instead of the
# socket's own. "mirrorLeft": a part with no side in its name, going onto a
# left socket, whose folder only has a right-hand fit, is mirrored and placed
# as the mirror image of the right one (Mar Fil's shin pads and pauldrons
# come as right-hand parts; their "...-Mirrored" copies count as lefts).
# Shin and Pad anchors are exact three-point frames, so pads don't settle.
# "rock": before settling, let the part tilt up to this many degrees about
# the anchor so it sits flush on the surface instead of touching at one edge.
# "settle": after snapping, slide the part along this socket axis until it
# touches the model ("-Z" = into the surface for anchors). "touch": stop when
# that percent of the part's inside touches, not at the first touch, so a
# cuff round the knee or a lug can sink in. "sink": then press it in this far
# (mm), so a pad printed with its host merges into it. "pushOut": false =
# settle only closes a gap and never pushes a part off the model.
# "spans": other sockets the part also covers (a two-handed weapon comes
# with both arms: it snaps to Shoulder R and clears Shoulder L, and an arm
# later snapped onto Shoulder L replaces it). "mirrorSides": the part has a
# fit for one side only (Mar Fil's jump-pack fins are left pieces); on the
# other side it is mirrored. Your library's _library.json "joints" replaces
# this table. "Hands" are bare hands (Intercessors V2), on the arm's Hand
# socket like anything held; a hand carries a Grip socket at its wrist, where
# "Hand-less Weapons" (Mar Fil's '...-NoHand' parts) go. "Bikes": the Outrider
# bike's rear body, on the rider's legs (the legs are exported sitting on it);
# it carries one socket per "Bike Parts" piece, each saved for that piece
# (tiow_holds), so a bike part finds its own spot whatever is selected.
# "Cables" go on a Cable socket like the heavy weapons' (the Techmarine's arm
# cables, on their arm); "Servo Arms" and "Mechadendrites" on the Techmarine
# backpack (a servo arm's shoulder ball in its seat). "Two-Handed Held": a
# gun held in both hands with no arms of its own (Turtle Ninja's bolter
# poses): it goes in the right hand, and the left arm of the same pose set
# meets its other grip.
# Waists come in two kinds: Mar Fil's (plug and stomach plating on the legs,
# "Waist") and flat ones (Marta and Turtle Ninja legs, "Flat Waist"). Legs go
# on whichever their fits say ("byFit"). A Mar Fil torso has no Flat Waist, so
# flat legs bring an "adaptor" (a body adaptor from the Adaptors folder in
# Preferences) onto its Waist and stand on the adaptor's Flat Waist. A
# Turtle Ninja torso has both; "exclusive" sockets are alternatives, so legs
# on one replace legs on the other.
BELT = ["Hip R", "Hip L", "Belt Back"]           # belt bits; the front of the belt is the loincloth's
BIKE = ["Bike Front", "Front Wing", "Front Wheel", "Rear Wheel", "Exhaust R", "Exhaust L",
        "Handle R", "Handle L", "Bike Guns"]
DEFAULT_JOINTS = {
    "Arms": {"socket": "Shoulder", "sided": True},
    "Two-Handed Guns": {"socket": "Shoulder R", "spans": ["Shoulder L"]},
    "Two-Handed Melee": {"socket": "Shoulder R", "spans": ["Shoulder L"]},
    "Two-Handed Held": {"socket": "Hand R"},
    "Heavy Weapons": {"socket": "Shoulder R", "spans": ["Shoulder L"]},
    "Pistols": {"socket": "Hand", "sided": True},
    "Melee": {"socket": "Hand", "sided": True},
    "Shields": {"socket": "Hand", "sided": True},
    "Hands": {"socket": "Hand", "sided": True},
    "Hand-less Weapons": {"socket": "Grip", "sided": True},
    "Forearm Armour": {"socket": "Forearm", "sided": True, "mirrorLeft": True},
    "Heads": {"socket": "Neck"},
    "Backpacks": {"socket": "Back"},
    "Jump Packs": {"socket": "Back"},
    "Backpack Toppers": {"socket": "Back Top"},
    "Heavy Weapon Cables": {"socket": "Cable"},
    "Cables": {"socket": "Cable"},
    "Servo Arms": {"socket": "Servo Arm"},
    "Mechadendrites": {"socket": "Mechadendrite"},
    "Bikes": {"socket": "Bike"},
    "Bike Parts": {"socket": BIKE},
    "Pack Fins": {"socket": "Pack Fin", "sided": True, "mirrorSides": True},
    "Legs": {"socket": ["Waist", "Flat Waist"], "byFit": True, "exclusive": ["Waist", "Flat Waist"],
             "adaptor": {"Flat Waist": "Waist"}},
    "Adapters": {"socket": "Waist", "exclusive": ["Waist", "Flat Waist"]},
    "Bases": {"socket": "Base"},
    "Shoulder Pads": {"socket": "Pad", "sided": True, "mirrorLeft": True},
    "Knee Pads": {"socket": "Shin", "sided": True, "mirrorLeft": True},
    "Accessories": {"socket": BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
    "Grenades": {"socket": BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
    "Seals": {"socket": BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
    "Trophies": {"socket": ["Trophy R", "Trophy L"] + BELT, "rock": 8, "settle": "-Z", "sink": 0.1},
    "Loincloths": {"socket": "Belt Front", "rock": 8, "settle": "-Z", "sink": 0.1},
    "Wings": {"socket": "Wing", "sided": True, "adaptor": {"Wing R": "Wing Mount R", "Wing L": "Wing Mount L"}},
    "Wing Mounts": {"socket": "Wing Mount", "sided": True},
    "Hip Plates": {"socket": "Plate", "sided": True},
    "Plate Accessories": {"socket": "Plate Hang", "sided": True,
                          "adaptor": {"Plate Hang R": "Plate R", "Plate Hang L": "Plate L"}},
    "Buckles": {"socket": "Buckle"},
    "Tabards": {"socket": "Tabard", "adaptor": {"Tabard": "Buckle"}},
    "Chest Equipment": {"socket": "Chest Equip", "sided": True},
    "Neck Guards": {"socket": "Neck Guard"},
    "Chest Inserts": {"socket": "Chest Insert"},
}
# Socket names from before the library rename, so library parts also snap
# into files set up the old way.
DEFAULT_ALIASES = {
    "Shoulder R": ["arm__Torso_r"], "Hand R": ["Wrist_socket_r"],
    "Forearm R": ["Wrist_Armout_r"], "Shield R": ["Shield_to_hand_r"],
    "Neck": ["Head"], "Back": ["Backpack"], "Hip R": ["Right Hip"],
    "Hip L": ["Left Hip"], "Belt Front": ["Tabard"],
}
LIBRARY_FILE = "_library.json"
FITS_FILE = "_fits.json"
_lib_cache = {}


def library_table(stl_path):
    """(joints, aliases) from the nearest _library.json above the STL, else the defaults."""
    d = os.path.dirname(os.path.abspath(stl_path))
    for _ in range(12):
        f = os.path.join(d, LIBRARY_FILE)
        if os.path.isfile(f):
            try:
                key = (f, os.path.getmtime(f))
                if key not in _lib_cache:
                    with open(f, encoding="utf-8") as fh:
                        data = json.load(fh)
                    _lib_cache.clear()
                    _lib_cache[key] = (data.get("joints") or DEFAULT_JOINTS,
                                       data.get("jointAliases") or DEFAULT_ALIASES)
                return _lib_cache[key]
            except (OSError, ValueError, AttributeError):
                break
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return DEFAULT_JOINTS, DEFAULT_ALIASES


def part_side(*texts):
    """'R', 'L' or None from words in the part's name and folder."""
    words = set()
    for t in texts:
        t = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(t or ""))
        words |= set(re.split(r"[^a-z]+", t.lower()))
    r = bool(words & {"r", "right", "rh"})
    l = bool(words & {"l", "left", "lh"})
    return "R" if r and not l else "L" if l and not r else None


def _part_sockets():
    """Part Sockets' sockets and core modules, wherever it is installed
    (bl_ext.user_default.part_sockets as an extension, part_sockets as a legacy add-on)."""
    sk = co = None
    for n, m in list(sys.modules.items()):
        if n.endswith("part_sockets.sockets") and hasattr(m, "snap_part_to_socket"):
            sk = m
        elif n.endswith("part_sockets.core") and hasattr(m, "detach_part"):
            co = m
    return (sk, co) if sk and co else None


def _descendants(ob):
    for c in ob.children:
        yield c
        yield from _descendants(c)


def _snapped_to(sock, co, among, tname=None):
    """Visible parts sitting on this socket - only those snapped with fit
    type `tname` when given (an arm and its pauldron share a Shoulder socket)."""
    out = []
    for o in among:
        if o.type == 'MESH' and o.get("ws_type") is None and not o.hide_get() \
                and co.snap_socket_of(o) is sock:
            if tname is None or (o.get("ws_snap_type") or sock.get("ws_type")) == tname:
                out.append(o)
    return out


def wanted_sockets(spec, side, aliases):
    base = spec.get("socket")
    if isinstance(base, list):
        names = [str(b) for b in base if b]
        if side:      # this side's sockets first
            names.sort(key=lambda n: 0 if n.endswith(" " + side) else 1)
    elif not base:
        return []
    elif spec.get("sided"):
        names = [f"{base} {side}"] if side else [f"{base} R", f"{base} L"]
    else:
        names = [str(base)]
    out = []
    for n in names:
        out.append(n)
        out += [a for a in aliases.get(n, []) if a not in out]
    return out


def _fit_of_fn(spec, side):
    """fit_of(socket): the fit type a part of this kind uses on that socket."""
    def fit_of(sock):
        st = str(sock.get("ws_type"))
        if not spec.get("fit"):
            return st
        if not spec.get("sided"):
            return str(spec["fit"])
        end = st.rsplit(" ", 1)[-1]
        return f"{spec['fit']} {end if end in ('R', 'L') else (side or 'R')}"
    return fit_of


def choose_socket(names, focus, co, view_layer, fit_of, prefer=None):
    """The socket to snap onto in the model around `focus` (what was selected
    before the import), and the part of the same kind already on it.
    `fit_of(socket)` is the fit type the new part would use there. `prefer`:
    the new part's name (or a set of names) - a free anchor saved where its
    maker put that part (tiow_holds) is used before the others.
    Returns (socket, part_on_it_or_None) or (None, None)."""
    if focus is None:
        return None, None
    pref = {prefer} if isinstance(prefer, str) else set(prefer or ())

    def order(o):
        held = 0 if pref & _holds(o) else 1
        return (held, names.index(o["ws_type"]), o.name)
    # a selected socket, or a selected part of the same kind on a matching socket, wins
    if focus.get("ws_type") in names:
        on = _snapped_to(focus, co, view_layer.objects, fit_of(focus))
        return focus, (on[0] if on else None)
    if focus.type == 'MESH':
        s = co.snap_socket_of(focus)
        if s is not None and s.get("ws_type") in names and \
                (focus.get("ws_snap_type") or s.get("ws_type")) == fit_of(s):
            return s, focus
    # the selected part's own sockets next (select a left hand, the weapon
    # goes in that hand), then the rest of the model
    root = focus
    while root.parent is not None:
        root = root.parent
    if focus.type == 'MESH' and focus is not root:
        own = sorted((c for c in focus.children if c.get("ws_type") in names), key=order)
        if own:
            members = [root] + list(_descendants(root))
            for s in own:
                on = _snapped_to(s, co, members, fit_of(s))
                if not on:
                    return s, None
            on = _snapped_to(own[0], co, members, fit_of(own[0]))
            return own[0], (on[0] if on else None)
    root = focus
    while root.parent is not None:
        root = root.parent
    socks = [o for o in _descendants(root) if o.get("ws_type") in names]
    if not socks:
        return None, None
    socks.sort(key=order)
    members = [root] + list(_descendants(root))
    taken = None
    for s in socks:
        on = _snapped_to(s, co, members, fit_of(s))
        if not on:
            return s, None
        if taken is None:
            taken = (s, on[0])
    return taken


def _world_tris(ob, deps):
    """World-space vertices and triangles of the evaluated mesh."""
    import numpy as np
    eo = ob.evaluated_get(deps)
    me = eo.to_mesh()
    try:
        me.calc_loop_triangles()
        v = np.empty(len(me.vertices) * 3, np.float64)
        me.vertices.foreach_get("co", v)
        t = np.empty(len(me.loop_triangles) * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", t)
    finally:
        eo.to_mesh_clear()
    mw = np.array(ob.matrix_world)
    v = v.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    return v, t.reshape(-1, 3)

