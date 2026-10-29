"""Springles into the test library: STLs linked from the uploads, sidecars from the stage dir."""
import os, glob, shutil
LIB = '/home/claude/test/kitlib/'; UP = '/mnt/user-data/uploads/new cults/'; ST = '/home/claude/kits/out113/stage_spr/'
n = s = 0
for f in glob.glob(UP + 'Springles/**/*.stl', recursive=True):
    rel = f[len(UP):]; dst = LIB + rel
    if not os.path.exists(dst): os.makedirs(os.path.dirname(dst), exist_ok=True); os.symlink(f, dst); n += 1
for f in glob.glob(ST + '**/*.sockets.json', recursive=True):
    rel = f[len(ST):]; os.makedirs(os.path.dirname(LIB + rel), exist_ok=True); shutil.copy(f, LIB + rel); s += 1
print('linked', n, 'sidecars', s)
