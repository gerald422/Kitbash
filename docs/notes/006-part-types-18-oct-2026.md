**Part types, 18 Oct 2026** (bridge v2, `apply-blender-bridge.mjs`; TIOW changes are a patch Josh applies):
- **Weapons are split into** Melee, Pistols, Heavy Weapons, Two-Handed Guns, Two-Handed Melee and Shields, matching Josh's Blender selections.
- **Where the type comes from:** TIOW's category for a file is the nearest folder named after a part type, falling back to TIOW's own rules. Aliases and stripped suffixes (RawStl, Mirrored, Sergeant, Support) come from `_library.json`'s `partTypes`; `--library` bakes them in.
- **What it affects:** the TIOW Item type filter, and the Blender collection a part lands in.
- **Bits** moved to a single `Library\Bits\<Type>` folder.
- **Patch before connecting the library:** TIOW sets a file's category only when it first adds the file to a catalogue.
- **Joints differ by weapon type:** one-handed weapons attach at the wrist (`Wrist_socket_r`), two-handed at the shoulders (the example file has a Combi weapon snapped to `arm__Torso_r`).
