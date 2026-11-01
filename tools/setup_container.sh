#!/bin/bash
# Recreate the build container for the Kitbash work in a fresh Claude session.
# Run after cloning this repo to /home/claude/kitbash, and after staging Josh's
# Part Sockets zip from his PC (Desktop\part_sockets_6.2.0.zip ->
# /mnt/user-data/uploads/Desktop/part_sockets_6.2.0.zip).
#   bash /home/claude/kitbash/tools/setup_container.sh
set -e
R=/home/claude/kitbash

# 1. Blender as a Python module (bpy 5.1.2 needs Python 3.13), plus numpy / scipy / pillow
if [ ! -x /home/claude/bpyenv/bin/python ]; then
  python3 -m venv /home/claude/bpyenv
  /home/claude/bpyenv/bin/pip install -q bpy==5.1.2 numpy scipy pillow
fi

# 2. Add-ons in that Blender's user scripts: Part Sockets (Josh's zip), TIOW Inbox and Finalise (this repo)
A=/root/.config/blender/5.1/scripts/addons
mkdir -p "$A"
Z=/mnt/user-data/uploads/Desktop/part_sockets_6.2.0.zip
if [ -f "$Z" ] && [ ! -d "$A/part_sockets" ]; then
  T=$(mktemp -d); (cd "$T" && unzip -q "$Z"); P=$(dirname "$(find "$T" -name blender_manifest.toml | head -1)")
  cp -r "$P" "$A/part_sockets"
fi
[ -d "$A/part_sockets" ] || echo "!! Part Sockets missing: stage Desktop\\part_sockets_6.2.0.zip from Josh's PC first"
cp "$R/addons/tiow_inbox.py" "$R/addons/kitbash_finalise.py" "$A/"

# 3. The old working paths the scripts in kits/ and tests/ import from
#    (they were written against /home/claude/kits, /home/claude/real, /home/claude/test ...)
[ -e /home/claude/kits ] || ln -s "$R/kits" /home/claude/kits
mkdir -p /home/claude/real /home/claude/test /home/claude/blend/forclaude /home/claude/tiow_117x /home/claude/tiow_blender
cp "$R/kits/lib/fitlib.py" /home/claude/real/
cp "$R/kits/lib/stl_io.py" /home/claude/blend/forclaude/
cp "$R/tests/rend.py" /home/claude/test/
cp "$R/addons/tiow_inbox.py" /home/claude/tiow_117x/       # tests that install "the current TIOW" read it here
cp "$R/addons/tiow_inbox.py" /home/claude/tiow_blender/

# 4. Page tests: playwright is pre-installed (require('playwright') works); serve a test library with
#      cd <folder with "Squad Builder.html" linked and a lib folder holding _builder/index.json, previews/, _hidden.txt>
#      python3 -m http.server 8777
#    then: node $R/squad-builder/test/t_wings_step.js "http://localhost:8777/Squad%20Builder.html?lib=/<lib>/"
echo "ready: /home/claude/bpyenv/bin/python $R/tests/wings/t_wings.py -- <worklib> $R/addons/tiow_inbox.py <josh_points.npz>"
