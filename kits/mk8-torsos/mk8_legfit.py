import numpy as np, json
L="/home/claude/kitbash/library/Mar Fil - Tacticus/AssaultMarines-V2/"
d=json.load(open(L+"Legs/MarFil Assault - Legs 1.sockets.json")); F=np.array(d['fits']['Waist']['matrix'] if isinstance(d['fits']['Waist'],dict) else d['fits']['Waist']).reshape(4,4)
t=json.load(open(L+"Chests/MarFil Assault - Torso 1.sockets.json"))['sockets']; W=[np.array(s['matrix']).reshape(4,4) for s in t if s['type']=='Waist'][0]
np.set_printoptions(precision=3,suppress=True)
print("fit\n",F); print("W@F\n",W@F); print("W@inv(F)\n",W@np.linalg.inv(F))
print(json.dumps(d['fits']['Waist'])[:300] if isinstance(d['fits']['Waist'],dict) else '')
