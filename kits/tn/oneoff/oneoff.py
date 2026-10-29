"""Turtle Ninja one-off kits exported in one assembly frame: sidecars that put every kit part back where Turtle Ninja
designed it on the kit's own body, through the same joints (and conventions) every other kit uses."""
import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import numpy as np, json, os, subprocess, stlcache, flats
from flatface import frame
from topface import merge_flats, top_face
import conv
from tn_torso import torso_faces
from tn_sockets import face_frames
TN = "/mnt/user-data/uploads/new cults/Turtle Ninja/"
OUT = "/home/claude/kits/out112/stage_oneoff/Turtle Ninja/"
def ortho(M):
    M = np.array(M, float); U_, _, Vt = np.linalg.svd(M[:3, :3]); M[:3, :3] = U_ @ Vt; return M
def flat(M): return [round(float(x), 6) for x in ortho(M).reshape(-1)]
def inv(M): return np.linalg.inv(M)
def sock(stem, t, M, note, size=3.0, holds=None, suffix=''):
    p = {'tiow_from': note}
    if holds: p['tiow_holds'] = holds
    return {'type': t, 'name': f'{stem}_socket_{t}{suffix}', 'matrix': flat(M), 'display_type': 'ARROWS', 'display_size': size, 'props': p}
def surf(V, T, n=200000):
    tri = V[T]; a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(0); i = rng.choice(len(T), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n); m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]
    t = tri[i]; P = t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
    N = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); N /= np.linalg.norm(N, axis=1)[:, None]; return P, N
BELT_DIRS = {'Hip R': (1, 0, 0), 'Hip L': (-1, 0, 0), 'Belt Front': (0, 1, 0), 'Belt Back': (0, -1, 0)}
def belt_anchors(V, T, FW, depth=1.0):
    """the flat-legs belt rule in the waist frame FW (Z up, Y front, X right): outermost surface 1 mm under the top"""
    P, N = surf(V, T); Q = (P - FW[:3, 3]) @ FW[:3, :3]; NQ = N @ FW[:3, :3]; out = {}
    for name, d in BELT_DIRS.items():
        d = np.array(d, float); D = Q - np.array([0, 0, -depth]); t = D @ d; lat = np.linalg.norm(D - t[:, None] * d, axis=1)
        k = (t > 0) & (lat < 0.35)
        if k.sum() < 3: continue
        hit = Q[k][np.argmax(t[k])]; near = (np.linalg.norm(Q - hit, axis=1) < 0.6) & (NQ @ d > 0)
        z = NQ[near].mean(0) if near.any() else d; y = np.array([0, 0, 1.]); z = z - y * (z @ y); z /= np.linalg.norm(z)
        K = np.eye(4); K[:3, 0], K[:3, 1], K[:3, 2], K[:3, 3] = np.cross(y, z), y, z, hit; out[name] = FW @ K
    return out
def held_belt(FW, c, up):
    """an anchor at an accessory's spot: type by direction from the waist axis, Z out (level), Y up"""
    d = inv(FW) @ np.append(c, 1); x, y = d[0], d[1]
    t = ('Hip R' if x > 0 else 'Hip L') if abs(x) > abs(y) else ('Belt Front' if y > 0 else 'Belt Back')
    o = FW[:3, :3] @ np.array([x, y, 0]); o /= np.linalg.norm(o)
    return t, frame(c, o, up)
def write(rel, sc):
    p = OUT + os.path.splitext(rel)[0] + '.sockets.json'; os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(sc, open(p, 'w'), indent=1)
def build(kit, roles, notes=''):
    """roles: file stem -> (role, extra). roles: torso, legs, arm R/L, head, pack, base, hand R/L (category), pad R/L (arm stem), belt, terrain"""
    D = TN + kit + '/'; L = lambda s: stlcache.load(D + s + '.stl')
    side = {}
    tor = [s for s, r in roles.items() if r[0] == 'torso'][0]
    V, T = L(tor); f = torso_faces(V, T); S = conv.torso_sockets(face_frames(f)); up = f['up']
    side[tor] = dict(schemaVersion=1, part=tor, category='Chests', fits={}, upright=flat(conv.KB @ inv(S['Flat Waist'])),
                     sockets=[sock(tor, t, S[t], f'flat torso rule ({kit})') for t in ('Shoulder R', 'Shoulder L', 'Neck', 'Back', 'Waist', 'Flat Waist')],
                     notes={'kit': f'{kit}: every part of the kit was exported in one assembly frame; its fits put it back there on this body'})
    legs = [s for s, r in roles.items() if r[0] == 'legs']
    FWl = {}
    for lg in legs:
        V, T = L(lg); FW = S['Flat Waist']; FWl[lg] = FW
        socks = [sock(lg, t, M, 'belt rule (flat legs): 1 mm under the top, Z out, Y up', 1.5) for t, M in belt_anchors(V, T, FW).items()]
        ymin_dir = -up; P = V[(V - V.mean(0)) @ up < ((V - V.mean(0)) @ up).min() + 0.6]
        base = frame(P.mean(0), up, f['front']); socks.append(sock(lg, 'Base', base, 'under the feet, Z up, Y front'))
        side[lg] = dict(schemaVersion=1, part=lg, category='Legs', sockets=socks, fits={'Flat Waist': flat(inv(FW))}, notes={'Flat Waist': 'as Turtle Ninja assembled it on the kit body'})
        FWl[lg] = (FW, base)
    arms = {s: r for s, r in roles.items() if r[0] == 'arm'}
    # wrists by the add-on's rule (bpyenv)
    args = []
    for a, (_, sd) in arms.items():
        J = S['Shoulder ' + sd][:3, 3]; args.append(f"{stlcache.path_of(D + a + '.stl') if hasattr(stlcache, 'path_of') else D + a + '.stl'}:{sd}:{J[0]},{J[1]},{J[2]}")
        stlcache.npz(D + a + '.stl')
    W = {}
    if args:
        subprocess.run(['/home/claude/bpyenv/bin/python', '/home/claude/kits/tn/oneoff/wrists.py', '/tmp/claude-0/wr.json'] + args, check=True, capture_output=True)
        W = {os.path.splitext(os.path.basename(p))[0]: (None if M is None else np.array(M)) for p, M in json.load(open('/tmp/claude-0/wr.json')).items()}
    for a, (_, sd) in arms.items():
        socks = []
        if W.get(a) is not None: socks.append(sock(a, 'Hand ' + sd, W[a], 'wrist rule (round wrist face at the far end)'))
        side[a] = dict(schemaVersion=1, part=a, category='Arms', sockets=socks, fits={'Shoulder ' + sd: flat(inv(S['Shoulder ' + sd]))}, notes={'Shoulder': 'as Turtle Ninja assembled it on the kit body'})
    for s, r in roles.items():
        role = r[0]
        if role == 'head': side[s] = dict(schemaVersion=1, part=s, category='Heads', sockets=[], fits={'Neck': flat(inv(S['Neck']))})
        elif role == 'pack': side[s] = dict(schemaVersion=1, part=s, category='Backpacks', sockets=[], fits={'Back': flat(inv(S['Back']))})
        elif role in ('base', 'terrain'):
            lg = r[1] if len(r) > 1 and r[1] else legs[0]; side[s] = dict(schemaVersion=1, part=s, category='Bases', sockets=[], fits={'Base': flat(inv(FWl[lg][1]))})
        elif role == 'hand':
            sd, cat, arm = r[1], r[2], r[3]
            if W.get(arm) is not None: side[s] = dict(schemaVersion=1, part=s, category=cat, sockets=[], fits={'Hand ' + sd: flat(inv(W[arm]))}, notes={'Hand': 'as Turtle Ninja assembled it on the kit arm'})
            else: side[s] = dict(schemaVersion=1, part=s, category=cat, sockets=[], fits={})
        elif role == 'pad':
            sd, arm = r[1], r[2]; V, T = L(s); c = V.mean(0)
            P = frame(c, S['Shoulder ' + sd][:3, 2] * 0 + up, f['front'])
            side[arm]['sockets'].append(sock(arm, 'Pad ' + sd, P, 'where Turtle Ninja put the kit pauldron', 2.0, holds=s, suffix='~kit'))
            side[s] = dict(schemaVersion=1, part=s, category='Shoulder Pads', sockets=[], fits={'Pad ' + sd: flat(inv(P))})
        elif role == 'belt':
            lg = r[1] if len(r) > 1 and r[1] else legs[0]; V, T = L(s); c = V.mean(0)
            t, Aa = held_belt(FWl[lg][0], c, up)
            side[lg]['sockets'].append(sock(lg, t, Aa, 'where Turtle Ninja put ' + s, 1.5, holds=s, suffix='~' + s))
            side[s] = dict(schemaVersion=1, part=s, category=r[2] if len(r) > 2 else 'Accessories', sockets=[], fits={t: flat(inv(Aa))})
    for s, sc in side.items(): write(kit + '/' + s + '.stl', sc)
    return S, side

QI = {s: inv(conv.Q['Shoulder ' + s]) for s in 'RL'}
def arm_disc_fit(V, T, side):
    """the Turtle Ninja arm rule (Y up files): shoulder disc centre on the socket, face flat on the chest"""
    M = merge_flats([(a, n, c) for a, n, c, o, s in flats.flats(V, T, min_area=1.0)])
    a, n, c = max([m for m in M if abs(m[1][0]) > 0.98 and m[0] > 6], key=lambda m: m[0])
    return QI[side] @ inv(frame(c, -n, [0, 1, 0]))
def pack_plate_fit(V, T):
    M = merge_flats([(A, n, c) for A, n, c, o, s in flats.flats(V, T, min_area=0.5)])
    big = max([m for m in M if abs(m[1][2]) > 0.95], key=lambda m: m[0])
    return inv(conv.Q['Back']) @ inv(frame(big[2], -big[1], [0, 1, 0])), big
SH_AM = conv.shoulder_frame(conv.S_AM['Shoulder R'], conv.S_AM['Shoulder L'])
KB_IN_SH = inv(SH_AM) @ conv.KB
def build_body(kit, roles, extra_fits=None):
    """a full body (torso and legs in one piece) with arms, head, pack in one assembly frame (Y up)"""
    D = TN + kit + '/'; L = lambda s: stlcache.load(D + s + '.stl'); side = {}
    body = [s for s, r in roles.items() if r[0] == 'body'][0]
    arms = {s: r for s, r in roles.items() if r[0] == 'arm'}
    S = {}
    for a, (_, sd) in arms.items():
        V, T = L(a); F = arm_disc_fit(V, T, sd); S['Shoulder ' + sd] = inv(F)
        side[a] = dict(schemaVersion=1, part=a, category='Arms', sockets=[], fits={'Shoulder ' + sd: flat(F)}, notes={'Shoulder': 'shoulder disc rule; the kit body has its socket where this arm sits'})
    pk = [s for s, r in roles.items() if r[0] == 'pack'][0]
    V, T = L(pk); Fp, plate = pack_plate_fit(V, T); S['Back'] = inv(Fp)
    side[pk] = dict(schemaVersion=1, part=pk, category='Backpacks', sockets=[], fits={'Back': flat(Fp)})
    up = np.array([0, 1., 0]); front = -plate[1].copy(); front[1] = 0; front /= np.linalg.norm(front)
    front = -front if (S['Shoulder R'][:3, 3] - S['Shoulder L'][:3, 3]) @ np.cross(front, up) < 0 else front
    SHF = conv.shoulder_frame(S['Shoulder R'], S['Shoulder L']); S['Neck'] = SHF @ conv.NECK_IN_SH
    FW = SHF @ KB_IN_SH
    V, T = L(body)
    P = V[(V @ up) < (V @ up).min() + 0.6]; base = frame(P.mean(0), up, front)
    socks = [sock(body, t, S[t], f'{kit}: where the kit part sits (shoulder disc / pack plate rules; neck by the shoulder joints)') for t in ('Shoulder R', 'Shoulder L', 'Neck', 'Back')]
    socks.append(sock(body, 'Base', base, 'under the feet, Z up, Y front'))
    socks += [sock(body, t, M, 'belt rule: 1 mm under the waist line, Z out, Y up', 1.5) for t, M in belt_anchors(V, T, FW).items()]
    side[body] = dict(schemaVersion=1, part=body, category='Chests', fits={}, upright=flat(conv.KB @ inv(FW)), sockets=socks,
                      notes={'kit': f'{kit}: torso and legs in one piece; its arms, head and pack were exported in place and go back there'})
    W = {}
    args = []
    for a, (_, sd) in arms.items():
        J = S['Shoulder ' + sd][:3, 3]; stlcache.npz(D + a + '.stl'); args.append(f"{D + a + '.stl'}:{sd}:{J[0]},{J[1]},{J[2]}")
    if args:
        subprocess.run(['/home/claude/bpyenv/bin/python', '/home/claude/kits/tn/oneoff/wrists.py', '/tmp/claude-0/wr.json'] + args, check=True, capture_output=True)
        W = {os.path.splitext(os.path.basename(p))[0]: (None if M is None else np.array(M)) for p, M in json.load(open('/tmp/claude-0/wr.json')).items()}
    for a, (_, sd) in arms.items():
        if W.get(a) is not None: side[a]['sockets'].append(sock(a, 'Hand ' + sd, W[a], 'wrist rule (round wrist face at the far end)'))
    for s, r in roles.items():
        role = r[0]
        if role == 'head': side[s] = dict(schemaVersion=1, part=s, category='Heads', sockets=[], fits={'Neck': flat(inv(S['Neck']))})
        elif role in ('base', 'terrain'): side[s] = dict(schemaVersion=1, part=s, category='Bases', sockets=[], fits={'Base': flat(inv(base))})
        elif role == 'hand':
            sd, cat, arm = r[1], r[2], r[3]
            fit = (extra_fits or {}).get(s)
            if fit is None and W.get(arm) is not None: fit = inv(W[arm])
            side[s] = dict(schemaVersion=1, part=s, category=cat, sockets=[], fits={} if fit is None else {'Hand ' + sd: flat(fit)})
        elif role == 'pad':
            sd, arm = r[1], r[2]; Vp, Tp = L(s); c = Vp.mean(0); Pf = frame(c, up, front)
            side[arm]['sockets'].append(sock(arm, 'Pad ' + sd, Pf, 'where Turtle Ninja put the kit pauldron', 2.0, holds=s, suffix='~kit'))
            side[s] = dict(schemaVersion=1, part=s, category='Shoulder Pads', sockets=[], fits={'Pad ' + sd: flat(inv(Pf))})
        elif role == 'belt':
            Vb, Tb = L(s); t, Aa = held_belt(FW, Vb.mean(0), up)
            side[body]['sockets'].append(sock(body, t, Aa, 'where Turtle Ninja put ' + s, 1.5, holds=s, suffix='~' + s))
            side[s] = dict(schemaVersion=1, part=s, category=r[2] if len(r) > 2 else 'Accessories', sockets=[], fits={t: flat(inv(Aa))})
    for s, sc in side.items(): write(kit + '/' + s + '.stl', sc)
    return S, side
