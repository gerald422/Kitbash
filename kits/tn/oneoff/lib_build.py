import sys; sys.path.insert(0,'/home/claude/kits/tn/oneoff')
from oneoff import *
roles = {'Full_Model_Decimated': ('torso',), 'Legs': ('legs',), 'Arm_Right': ('arm', 'R'), 'Arm_Left': ('arm', 'L'),
         'Head_Hat_Neutral': ('head',), 'Head_Hat_Yell': ('head',), 'Head_Standard_Neutral': ('head',), 'Head_Standard_Yell': ('head',),
         'Powerpack': ('pack',), 'Base_40mm': ('base',),
         'Hand_Left': ('hand', 'L', 'Hands', 'Arm_Left'), 'Hand_Right_Staff_1': ('hand', 'R', 'Melee', 'Arm_Right'),
         'Hand_Right_Staff_2': ('hand', 'R', 'Melee', 'Arm_Right'), 'Hand_Right_Staff_Standard': ('hand', 'R', 'Melee', 'Arm_Right'),
         'Pauldron': ('pad', 'L', 'Arm_Left'),
         'Accessories_Book_Satchel': ('belt',), 'Accessories_Bottle': ('belt',), 'Accessories_Scroll': ('belt',), 'Buckle': ('belt',)}
S, side = build("TurtleNinja's Librarian Custom", roles)
for s, sc in side.items(): print('%-28s %-14s fits %s sockets %s' % (s, sc['category'], list(sc['fits']), [x['type'] for x in sc['sockets']]))
