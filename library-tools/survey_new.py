#!/usr/bin/env python3
"""List the set-up parts (sidecars, _fits.json folders) under some top folders of D:\\new cults, for plan_library.py --survey.
    survey_new.py <top>[,<top>...] <out.json>"""
import os, sys, json
SRC = os.path.expanduser('~/mnt/new cults')
out = {'side': [], 'fits': []}
for t in sys.argv[1].split(','):
    for dp, dn, fn in os.walk(os.path.join(SRC, t)):
        for f in fn:
            if f.endswith('.sockets.json'):
                out['side'].append(os.path.relpath(os.path.join(dp, f), SRC).replace(os.sep, '/'))
            elif f == '_fits.json':
                out['fits'].append(os.path.relpath(dp, SRC).replace(os.sep, '/'))
json.dump(out, open(os.path.expanduser(sys.argv[2]), 'w'), indent=1)
print(len(out['side']), 'sidecars,', len(out['fits']), 'fits folders')
