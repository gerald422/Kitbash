# ---------------------------------------------------------------- anchors

ANCHORS_THREE = ("Shin R", "Shin L", "Pad R", "Pad L")
ANCHORS_TWO = ANCHORS_THREE[:2]              # older two-click shins (knee, ankle)
ANCHORS_ONE = ("Belt Front", "Belt Back", "Hip R", "Hip L")
CLICKS = {
    "Shin": ("the CIRCLE at one end of the ANKLE",
             "the CIRCLE at the other end of the ankle",
             "the TOP of the HOLE in the front of the shin"),
    "Pad": ("the FRONT CORNER of the arm's mini shoulder pad",
            "its BACK CORNER",
            "its TOP, at the inner edge by the shoulder joint"),
}


def _three_point_frame(anchor, pts, nrm, forward=None, outward=None):
    """Anchor frame from three points: the first two set a line, the third
    sits off it and is the anchor's origin.
    Shin: ankle circle, ankle circle, top of the shin hole -> X across the
    ankle, Y up the shin (from between the ankle circles to the hole), Z out
    of the front of the shin (the hole's opening).
    Pad: front corner, back corner, top of the arm's mini shoulder pad by the
    joint -> Y forward along the corners, Z from the corners' line to the top
    point, X = Y x Z. Which way along the corners is forward comes from
    `outward` (from the middle of the model out to this shoulder: X points
    out on a right arm, in on a left one), or failing that from `forward`.
    Left and right frames are mirror images, so a pad's left fit is its
    right fit mirrored across X. The order of the two corners or the two
    ankle circles doesn't matter."""
    a, b, c = pts
    if (a - b).length < 1e-6:
        raise ValueError("the first two clicks are on the same spot")
    line = (b - a).normalized()
    mid = (a + b) * 0.5
    off = (c - mid) - line * (c - mid).dot(line)
    if off.length < 0.05 * (a - b).length:
        raise ValueError("the third point is in line with the first two")
    if anchor.startswith("Shin"):
        x, y = line, off.normalized()
        z = x.cross(y)
        if z.dot(nrm[2]) < 0:
            x, z = -x, -z
    else:
        y = line
        z = off.normalized()
        x = y.cross(z)
        if outward is not None:
            # lateral: stays right however far the arm swings up or forward
            if x.dot(Vector(outward)) * (1 if anchor.endswith("R") else -1) < 0:
                y, x = -y, -x
        elif forward is not None and y.dot(Vector(forward)) < 0:
            y, x = -y, -x
    M = Matrix((x.normalized(), y.normalized(), z.normalized())).transposed().to_4x4()
    M.translation = c
    return M


def _forward_of(part):
    ps = _part_sockets()
    s0 = ps[1].snap_socket_of(part) if ps else None
    return (s0.matrix_world if s0 is not None else part.matrix_world).to_3x3() @ Vector((0, 1, 0))


def _outward_of(part, point):
    """From the middle of the model out to this side, for a part snapped onto
    a sided socket (an arm on Shoulder R): this socket minus its opposite
    number, or failing that the point minus the model's root, level. None
    if the part isn't on the model."""
    ps = _part_sockets()
    s0 = ps[1].snap_socket_of(part) if ps else None
    if s0 is None:
        return None
    t = str(s0.get("ws_type", ""))
    if t[-2:] in (" R", " L") and s0.parent is not None:
        other = t[:-1] + ("L" if t.endswith("R") else "R")
        for c in s0.parent.children:
            if c.get("ws_type") == other:
                v = s0.matrix_world.translation - c.matrix_world.translation
                if v.length > 1e-6:
                    return v.normalized()
    root = s0
    while root.parent is not None:
        root = root.parent
    up = (root.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    v = Vector(point) - root.matrix_world.translation
    v -= up * v.dot(up)
    return v.normalized() if v.length > 1e-6 else None


def make_anchor(part, anchor, points, normals, forward=None, kind="clicked"):
    """Create (or replace) an anchor socket on `part` from surface points
    (world space). Shin and Pad: three points (see _three_point_frame); an
    older two-point Shin (knee, ankle) still works. Belt and hip: one point -
    Z out of the surface, Y as close to up as it gets."""
    pts = [Vector(p) for p in points]
    nrm = [Vector(n).normalized() for n in normals]
    M = None
    if anchor in ANCHORS_THREE and len(pts) >= 3:
        outward = None
        if forward is None and anchor.startswith("Pad"):
            outward = _outward_of(part, pts[2])
            if outward is None:
                forward = _forward_of(part)
        M = _three_point_frame(anchor, pts[:3], nrm[:3], forward, outward)
    elif anchor in ANCHORS_TWO:
        if len(pts) < 2 or (pts[0] - pts[1]).length < 1e-6:
            raise ValueError("needs a knee point and an ankle point")
        y = (pts[0] - pts[1]).normalized()
        z = nrm[0] + nrm[1]
        if z.length < 1e-6:
            z = nrm[0].copy()
        origin = pts[0]
    elif anchor.startswith("Pad"):
        raise ValueError("a Pad anchor needs three points")
    else:
        z = nrm[0].copy()
        origin = pts[0]
        y = Vector((0, 0, 1))
        if abs(y.dot(z.normalized())) > 0.95:
            y = part.matrix_world.to_3x3() @ Vector((0, 1, 0))
    if M is None:
        z = (z - y * z.dot(y)).normalized()
        x = y.cross(z).normalized()
        M = Matrix((x, y, z)).transposed().to_4x4()
        M.translation = origin
    for c in list(part.children):
        if c.type == 'EMPTY' and c.get("ws_type") == anchor:
            bpy.data.objects.remove(c)
    ob = bpy.data.objects.new(f"{part.name}_socket_{anchor}"[:63], None)
    coll = part.users_collection[0] if part.users_collection else bpy.context.scene.collection
    coll.objects.link(ob)
    ob.empty_display_type = 'ARROWS'
    dims = part.dimensions
    # three-point anchors sit in a hole or on a small plate: big enough to
    # see, and drawn in front of the mesh
    ob.empty_display_size = max((0.15 if anchor in ANCHORS_THREE else 0.05) * max(dims), 1e-3)
    ob.show_in_front = anchor in ANCHORS_THREE
    ob["ws_type"] = anchor
    ob["tiow_anchor"] = kind
    # the points themselves, in the part's own coordinates, so the anchor can
    # be copied onto other parts with the same shape
    inv = part.matrix_world.inverted_safe()
    ob["tiow_points"] = json.dumps([list(inv @ p) for p in pts])
    ob.parent = part
    ob.matrix_parent_inverse = part.matrix_world.inverted_safe()
    ob.matrix_world = M
    ps = _part_sockets()
    if ps:
        ps[0].ensure_type(bpy.context.scene, anchor)
    return ob


def _sidecar_for_write(part):
    """(path, the whole sockets file, the dict this part's own data is in) -
    the variant's entry for a part brought in as a variant - or None."""
    src = part.get("tiow_src")
    if not src or not os.path.isfile(str(src)):
        return None
    path = os.path.splitext(str(src))[0] + SIDECAR
    try:
        with open(path, encoding="utf-8") as f:
            whole = json.load(f)
        if not isinstance(whole, dict):
            whole = {}
    except (OSError, ValueError):
        whole = {}
    whole.setdefault("schemaVersion", 1)
    whole.setdefault("part", os.path.splitext(os.path.basename(str(src)))[0])
    vi = part.get("tiow_variant")
    if vi is None:
        return path, whole, whole
    vs = whole.get("variants")
    try:
        vi = int(vi)
    except (TypeError, ValueError):
        return None
    if not isinstance(vs, list) or not 0 <= vi < len(vs) or not isinstance(vs[vi], dict):
        return None                       # a mirror made on the spot that couldn't be saved
    sub = vs[vi].get("sidecar")
    if not isinstance(sub, dict):
        sub = vs[vi]["sidecar"] = {}
    return path, whole, sub


def _write_sidecar(path, whole):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(whole, f, indent=1)
    os.replace(tmp, path)


def remember_anchor(part, sock):
    """Write an anchor into the part's <part>.sockets.json beside its STL, so
    the part brings it along every time it is sent from TIOW (and other parts
    with the same shape can copy it)."""
    got = _sidecar_for_write(part)
    if got is None:
        return None
    path, whole, data = got
    unit = float(part.get("tiow_unit", 1.0)) or 1.0
    loc, rot, _s = part.matrix_world.decompose()
    frame = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))
    L = frame.inverted_safe() @ sock.matrix_world
    L.translation = L.translation / unit
    entry = {"type": sock["ws_type"], "name": sock.name, "matrix": [x for row in L for x in row],
             "display_type": "ARROWS", "display_size": float(sock.empty_display_size) / unit,
             "props": {"tiow_anchor": str(sock.get("tiow_anchor", "clicked"))}}
    try:
        pts = json.loads(sock.get("tiow_points", "[]"))
        # stored in file units, in the STL's own coordinates
        if pts:
            entry["points"] = [list((frame.inverted_safe() @ (part.matrix_world @ Vector(p))) / unit) for p in pts]
    except (TypeError, ValueError):
        pass
    socks = [s for s in data.get("sockets", []) if isinstance(s, dict) and s.get("type") != sock["ws_type"]]
    data["sockets"] = socks + [entry]
    _write_sidecar(path, whole)
    return path


def forget_anchors(part, types):
    """Take anchors of these types out of the part's <part>.sockets.json.
    Returns how many were removed."""
    if not part.get("tiow_src") or not os.path.isfile(os.path.splitext(str(part["tiow_src"]))[0] + SIDECAR):
        return 0
    got = _sidecar_for_write(part)
    if got is None:
        return 0
    path, whole, data = got
    socks = data.get("sockets")
    if not isinstance(socks, list):
        return 0
    keep = [s for s in socks if not (isinstance(s, dict) and s.get("type") in types)]
    if len(keep) == len(socks):
        return 0
    data["sockets"] = keep
    try:
        _write_sidecar(path, whole)
    except OSError:
        return 0
    return len(socks) - len(keep)

