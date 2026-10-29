"""helpers to write quick-render jobs and run them"""
import json, subprocess, numpy as np, os, tempfile
PY = "/home/claude/bpyenv/bin/python"
GREY, BLUE, ORANGE, GREEN, PURPLE, RED = (0.8, 0.8, 0.76, 1), (0.45, 0.65, 0.88, 1), (0.9, 0.58, 0.35, 1), (0.55, 0.8, 0.5, 1), (0.75, 0.55, 0.85, 1), (0.9, 0.35, 0.35, 1)
def run(name, items, views=None, out="/home/claude/kits/renders", res=600, pad=1.05, centre=None, size=None):
    job = {"out": out, "name": name, "items": [[r, np.asarray(m, float).ravel().tolist(), list(c)] for r, m, c in items],
           "views": views or {"front": (0, 1, 0), "right": (1, 0, 0)}, "res": res, "pad": pad, "centre": None if centre is None else list(map(float, centre)), "size": size}
    f = tempfile.mktemp(suffix=".json"); json.dump(job, open(f, "w"))
    r = subprocess.run([PY, "/home/claude/kits/qrender.py", f], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-2000:])
    return {v: f"{out}/{name}_{v}.png" for v in job["views"]}
