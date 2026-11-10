# ---------------------------------------------------------------- standing on the base

def base_socket_of(ob):
    """The Base socket of the model around `ob` (one with a base on it first)."""
    if ob is None:
        return None
    root = ob
    while root.parent is not None:
        root = root.parent
    socks = [o for o in [root] + list(_descendants(root)) if o.get("ws_type") == "Base"]
    if not socks:
        return None
    ps = _part_sockets()
    if ps is not None:
        on = [s for s in socks if _snapped_to(s, ps[1], bpy.context.view_layer.objects)]
        if on:
            return on[0]
    return socks[0]


def stand_on_base(sock):
    """Turn the whole model about its Base socket so the ground under its feet
    is flat on the grid: the socket's Z straight up (the smallest turn, so the
    model keeps facing the way it did), and the base's underside (or, with no
    base on it, the socket) dropped onto the grid where it stands. Only the
    model's root moves - every joint stays as it is - plus any part snapped in
    without being parented. Returns the tilt it took out, in degrees."""
    import numpy as np
    vl = bpy.context.view_layer
    root = sock
    while root.parent is not None:
        root = root.parent
    members = {root} | set(_descendants(root))
    ps = _part_sockets()
    loose = []
    if ps is not None:
        loose = [o for o in vl.objects if o not in members and ps[1].snap_socket_of(o) in members]
    before = root.matrix_world.copy()
    S = sock.matrix_world
    up = Vector(S.col[2][:3]).normalized()
    tilt = math.degrees(up.angle(Vector((0.0, 0.0, 1.0)))) if up.length > 1e-9 else 0.0
    p = S.translation.copy()
    turn = up.rotation_difference(Vector((0.0, 0.0, 1.0))).to_matrix().to_4x4()
    root.matrix_world = Matrix.Translation(p) @ turn @ Matrix.Translation(-p) @ before
    vl.update()
    low = sock.matrix_world.translation.z
    bases = _snapped_to(sock, ps[1], vl.objects) if ps is not None else []
    for b in bases:
        n = len(b.data.vertices)
        if n:
            co = np.empty(n * 3)
            b.data.vertices.foreach_get("co", co)
            M = np.array(b.matrix_world)
            low = min(low, float((co.reshape(-1, 3) @ M[2, :3] + M[2, 3]).min()))
    root.matrix_world = Matrix.Translation((0.0, 0.0, -low)) @ root.matrix_world
    vl.update()
    delta = root.matrix_world @ before.inverted_safe()
    for o in loose:
        o.matrix_world = delta @ o.matrix_world
    return tilt

