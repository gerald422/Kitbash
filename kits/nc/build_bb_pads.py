import numpy as np, json, os
from pads import *
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
side = {}
PADS = ['Medusas Mortals__Medusas Mortals__Stuff__ShoulderPad_Bolts', 'Medusas Mortals__Medusas Mortals__Stuff__ShoulderPad_Studs', 'Medusas Mortals__Medusas Mortals__Stuff__ShoulderPad_Logo_Bolts',
        'Medusas Mortals__Medusas Mortals__Stuff__ShoulderPad_Logo_Studs', 'Praetor with Paragon Blade__Praetor with Paragon Blade__ShoulderPad_Bolts',
        'Praetor with Paragon Blade__Praetor with Paragon Blade__ShoulderPad_Logo_Bolts', 'Consul__ShoulderPad', 'Consul__ShoulderPad_Studs', 'Chaplain__ChaplainShoulderPad',
        'IronFather__Shoulderpad', 'IronFather__IHShoulderpad'] + ['IH_Shoulderpads__' + x for x in ['IH_Shoulderpad_ALTBlank', 'IH_Shoulderpad_ALTSign', 'IH_Shoulderpad_Blank', 'IH_Shoulderpad_BlankChains',
        'IH_Shoulderpad_BlankChainsAndTriangles', 'IH_Shoulderpad_Dots', 'IH_Shoulderpad_Sign', 'IH_Shoulderpad_SignChains', 'IH_Shoulderpad_SignChainsAndTriangles']]
for k in PADS:
    f = '/home/claude/kits/nc/npz/BBoosty__' + k + '.npz'; V, F = load(f)
    inn = pad_inner(V, F); fit, sc = pad_fit_R2(inn)
    rel = 'BBoosty/' + k.replace('__', '/') + '.stl'
    side[rel] = dict(schemaVersion=1, part=os.path.basename(rel)[:-4], category="Shoulder Pads", sockets=[], fits={"Pad R": R(fit)},
                     notes={"Pad R": "inner shell (r %.2f) centred where Josh's 62 sits on the heresy arm, turned square so it opens inward and down (match %.2f); lefts are mirrored" % (inn['r'], sc)})
    print('%-60s r %.2f match %.2f' % (k[-60:], inn['r'], sc))
json.dump(side, open('/home/claude/kits/nc/bb_side_pads.json', 'w'))
