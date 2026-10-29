"""CyberBrush Space Bug Hunters backpacks: exported facing out (-Y) = the marine's own axes turned round, so they sit
unturned in Mar Fil axes; the big flat inner face (r ~4.5-4.9) centred on the Mar Fil back plate."""
import numpy as np, json, glob, os
from geo import *; from bbrules import *
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
BACKPLATE_MF = np.array([0.0, -5.35, 33.46])
side = {}
for f in sorted(glob.glob('/home/claude/kits/nc/npz/CyberBrush__Space Bugs Hunters__Space Bug hunters Backpacks__*.npz')):
    V, F = load(f); A, c, nn, g = flats(V, F, [0, 1, 0], cos=0.97, min_area=20)[0]
    W = T(BACKPLATE_MF - c)
    rel = os.path.basename(f)[:-4].replace('__', '/') + '.stl'
    side[rel] = dict(schemaVersion=1, part=os.path.basename(rel)[:-4], category="Backpacks", sockets=[], fits={"Back": R(np.linalg.inv(S_BACK) @ W)},
                     notes={"Back": "CyberBrush pack (exported facing out): its flat inner face (A %.0f) centred on the Mar Fil back plate, unturned" % A})
json.dump(side, open('/home/claude/kits/nc/cb_side_packs.json', 'w')); print(len(side))
