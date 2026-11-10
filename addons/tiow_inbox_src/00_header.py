# TIOW Inbox - import STLs sent from TIOW-FTRP into the open Blender scene.
#
# TIOW-FTRP's "Send to Blender" writes one small JSON file per item into
# %LOCALAPPDATA%\TIOW-FTRP\local-data\blender-inbox. This add-on checks that
# folder twice a second. For each request it imports the STL into the scene
# that is open, puts it in a collection named after the TIOW category, places
# it at the 3D cursor, and leaves it selected and active, so Part Sockets can
# work on it straight away.
#
# A part lifted out of a kitbash file (lift_parts_to_library.py) has a
# <part>.sockets.json beside its STL: its sockets and per-part fits are
# rebuilt on import, and any fit types they use that the scene lacks are
# added.
#
# Auto-snap: select the model you are building before you send a part. The
# part goes onto the free socket of its joint in that model (an arm onto
# Shoulder R, a pistol onto Hand R...), using Part Sockets' own snap. If that
# joint is taken, the part already there is swapped out, and anything it was
# holding (a pistol in its hand) moves across to the new part. Which joint
# each part type uses is the "joints" table in your library's _library.json.
#
# A folder is the whole interface: no ports, no threads. If Blender is closed,
# requests wait for a few minutes and are then dropped, so an old click does
# not appear in a file you open days later.
#
# One file, both sides (1.16): a part's mirror copy can live inside its
# .sockets.json as a "variant" instead of as a second STL. Sent from TIOW, the
# part arrives as the variant when it goes on that side (the side you picked,
# or the free one), exactly as the old copy did. Mirror (TIOW panel) flips the
# selected part: an arm or a hand-held part moves to the other side (swapping
# with what is there), legs or a torso flip where they stand.
#
# Squads (1.17): a request from the Squad Builder page names its model (and
# the socket the part goes on), so a whole squad arrives in one send and each
# part goes on its own model whatever is selected. A model's first part (its
# torso) is placed where the builder showed it.
#
# 1.17.1: browsers won't let a page write into AppData, so the Squad Builder
# writes its requests into the library's own _builder\inbox folder; this add-on
# watches that folder as well as TIOW's (pref "Squad Builder Inbox").
#
# 1.17.3: a socket moved by hand (Save Correction > Fix the Socket, marked
# tiow_corrected) is trusted as it is: belt bits on it aren't rocked to a new
# tilt, only settled into contact, so the bit you placed lands where you put it.
#
# 1.17.4: loincloths are their own type ("Loincloths") and the only thing that
# goes on the belt's front anchor (Belt Front); pouches, grenades and other
# belt bits go on the hips and the back of the belt.
#
# 1.17.5: blade wings (Wings) come with their connector. A wing's sockets file
# names the connector ("adaptor", a path in the library); sent onto a pack that
# has no Wing R / Wing L socket yet, the connector (Wing Mounts) goes on the
# pack's Wing Mount R / L first and the wing hangs from the connector's own
# Wing R / L socket. A request for a socket the model hasn't got yet keeps its
# side, so a left wing arrives as the left one.
#
# 1.17.6: hip plates and the belt buckle are parts that others hang from. Legs
# with plate spots (Plate R / L) take a hip plate (the left as its file, the
# right its mirror image); holsters and sheaths ("Plate Accessories") hang from
# the plate's Plate Hang socket and bring their plate when the legs have none
# yet. A buckle ("Buckles") sits on the legs' Buckle; tabards hang from the
# buckle's Tabard socket and bring the buckle. Trophies go on the trophy spots
# either side of the buckle (Trophy R / L) before the hips and back.
#
# 1.17.7: torsos with chest equipment and neck guard spots (the Old Style Space
# Knight MK8 torsos): "Chest Equipment" goes on Chest Equip R / L (the left as
# its file, the right its mirror image), "Neck Guards" on Neck Guard. Both are
# placed exactly as the maker's builder has them (no rock or settle).
#
# 1.17.8: chest inserts ("Chest Inserts") go on a torso's Chest Insert socket;
# for now only Josh's cut of Mar Fil Assault Torso 2 has one (Torso 2 Insert).

bl_info = {
    "name": "TIOW Inbox",
    "author": "Josh",
    "version": (1, 17, 8),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Sockets > TIOW Inbox",
    "description": "Imports STLs sent from TIOW-FTRP (Send to Blender) into "
                   "the open scene",
    "category": "Import-Export",
}

import json
import math
import os
import re
import sys
import time

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from mathutils import Matrix, Vector

HEARTBEAT = ".listening"     # TIOW reads its age to say "sent" vs "queued"
POLL_SECONDS = 0.5
HEARTBEAT_SECONDS = 3.0

_state = {"last": "", "beat": {}}


def default_inbox():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "TIOW-FTRP", "local-data", "blender-inbox")


def get_prefs():
    addon = bpy.context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


def inbox_dir(prefs):
    return bpy.path.abspath(prefs.inbox_path) if prefs.inbox_path \
        else default_inbox()


def inbox_dirs(prefs):
    """TIOW's inbox, then the Squad Builder's (in the library's _builder folder,
    used only when that _builder folder exists: Prepare made it)."""
    dirs = [inbox_dir(prefs)]
    sb = bpy.path.abspath(prefs.builder_inbox) if getattr(prefs, "builder_inbox", "") else ""
    if sb and os.path.isdir(os.path.dirname(os.path.normpath(sb))) \
            and os.path.normcase(os.path.normpath(sb)) != os.path.normcase(os.path.normpath(dirs[0])):
        dirs.append(sb)
    return dirs

