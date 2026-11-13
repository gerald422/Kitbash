"""Shared code for kit scripts, so a task doesn't re-write (or re-copy) its helpers.

  kb.geo       STL reading, frames, Kabsch / ICP, flat faces, spheres (numpy; scipy for ICP)
  kb.sidecar   load / save a .sockets.json exactly as the library keeps it; merge without losing Josh's work; checks
  kb.fit       heads and pads from Josh's reference helmet / pad (the Nov 9 rules)
  kb.carry     arms, legs, torsos from the fitted parts in the same library folder (gated; notes 091)
  kb.index     the page's _builder/index.json: read, change parts in place, write back byte-compatible
  kb.deliver   build a delivery folder + manifest for tools/kb.py apply (on the PC)

Use from any script:   import sys, os; sys.path.insert(0, <repo>); from kb import geo, sidecar
"""
import os
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
