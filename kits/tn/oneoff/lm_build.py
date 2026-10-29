import sys, os, json; sys.path.insert(0,'/home/claude/kits/tn/oneoff')
from oneoff import *
vf = '/home/claude/kits/tn/lm/volkite_fits.json'
extra = {}
if os.path.exists(vf):
    v = json.load(open(vf)); extra = {'LM_Volkite_Pistol_R_Arm': np.array(v['R']), 'LM_Volkite_Pistol_L_Arm': np.array(v['L'])}
roles = {'LM_Body': ('body',), 'LM_R_Arm': ('arm', 'R'), 'LM_L_Arm': ('arm', 'L'), 'LM_Helmet': ('head',), 'LM_Powerpack': ('pack',), 'LM_Terrain': ('terrain',),
         'LM_Pauldron_1': ('pad', 'R', 'LM_R_Arm'), 'LM_Pauldron_2': ('pad', 'L', 'LM_L_Arm'),
         'LM_Plasma_Pistol_R_Arm': ('hand', 'R', 'Pistols', 'LM_R_Arm'), 'LM_Plasma_Pistol_L_Arm': ('hand', 'L', 'Pistols', 'LM_L_Arm'),
         'LM_Volkite_Pistol_R_Arm': ('hand', 'R', 'Pistols', None), 'LM_Volkite_Pistol_L_Arm': ('hand', 'L', 'Pistols', None)}
S, side = build_body("TurtleNinja's Legion Moritat", roles, extra)
for s, sc in side.items(): print('%-26s %-14s fits %s sockets %s' % (s, sc['category'], list(sc['fits']), [x['type'] for x in sc['sockets']]))
