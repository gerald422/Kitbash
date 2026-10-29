"""Add the other creators' parts to the test library (kitlib): STLs linked from the staged uploads, sidecars from the build."""
import os, glob, shutil
LIB = '/home/claude/test/kitlib/'; UP = '/mnt/user-data/uploads/new cults/'; ST = '/home/claude/kits/out112/stage/'
n = s = 0
for sub in ('Turtle Ninja', 'body adaptor', 'Marta'):
    for f in glob.glob(UP + sub + '/**/*.stl', recursive=True):
        rel = f[len(UP):]; dst = LIB + rel
        if not os.path.exists(dst): os.makedirs(os.path.dirname(dst), exist_ok=True); os.symlink(f, dst); n += 1
    for f in glob.glob(UP + sub + '/**/*.sockets.json', recursive=True):      # sidecars already on Josh's drive
        rel = f[len(UP):]; os.makedirs(os.path.dirname(LIB + rel), exist_ok=True); shutil.copy(f, LIB + rel); s += 1
for f in glob.glob(ST + '**/*.sockets.json', recursive=True):
    rel = f[len(ST):]; os.makedirs(os.path.dirname(LIB + rel), exist_ok=True); shutil.copy(f, LIB + rel); s += 1
print('linked', n, 'sidecars', s)
