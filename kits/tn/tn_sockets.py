import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache
from flatface import frame
import conv
from tn_torso import torso_faces, TN
def face_frames(f):
    up, front = f['up'], f['front']
    B = frame(f['bottom'][2], up, front)
    out = {'Bottom': B,
           'Shoulder R': frame(f['shR'][2], f['shR'][1], up), 'Shoulder L': frame(f['shL'][2], f['shL'][1], up),
           'Back': frame(f['back'][2], f['back'][1], up), 'Neck': frame(f['neck'][2], f['neck'][1], front)}
    return out
def sockets_for(rel):
    V, T = stlcache.load(TN + rel); f = torso_faces(V, T)
    return conv.torso_sockets(face_frames(f)), f
if __name__ == '__main__':
    S, f = sockets_for("TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl")
    for k, M in S.items(): print(k, M[:3, 3].round(2), 'Z', M[:3, 2].round(2), 'Y', M[:3, 1].round(2))
