"""Any legs (or a legs file's mirror variant) in torso coordinates, the shared frame the hip-plate seat works in.
A key is a library path without .stl; "<path>#v<i>" is that file's variant i (its own sockets / fits in its sidecar).
Mar Fil-style legs (a Waist fit) sit under Mar Fil Assault Torso 1's Waist; flat-topped legs (a Flat Waist fit: TN,
Marta) under TN Mk8 Torso A1's Flat Waist, stood up by its upright (both = the Mar Fil kit frame)."""
import json, numpy as np
from hol_common import stl, tf, M16, LIB, AM
T1 = json.load(open(LIB + AM + "Chests/MarFil Assault - Torso 1.sockets.json", encoding="utf-8-sig"))
S_WAIST = M16([s for s in T1["sockets"] if s["type"] == "Waist"][0]["matrix"])
TT = json.load(open(LIB + "Turtle Ninja - Heresy/Mk7-8 Builder/Mk7-8/Chests/TN Mk7-8 - Mk8 Torso A1.sockets.json", encoding="utf-8-sig"))
UP, FW = M16(TT["upright"]), M16([s for s in TT["sockets"] if s["type"] == "Flat Waist"][0]["matrix"])


def split(key):
    return (key.split("#v")[0], int(key.split("#v")[1])) if "#v" in key else (key, None)


def sidecar(rel):
    return json.load(open(LIB + rel + ".sockets.json", encoding="utf-8-sig"))


def legs(key, root):
    """-> (data, V, T, M): the sidecar part the sockets go in (the variant's own for #v), the mesh in that file's
    coordinates (scaled), and M = that file -> torso coordinates"""
    rel, vi = split(key); d = sidecar(rel); V, T = stl(root + rel + ".stl")
    if vi is not None:
        v = d["variants"][vi]; Al = M16(v["align"]); V = tf(Al, V)
        if np.linalg.det(Al[:3, :3]) < 0: T = T[:, ::-1]          # a mirror: keep the faces pointing out
        d = v["sidecar"]
    V = V * float(d.get("scale") or 1.0)
    f = d["fits"]
    M = S_WAIST @ M16(f["Waist"]) if "Waist" in f else UP @ FW @ M16(f["Flat Waist"])
    return d, V, T, M
