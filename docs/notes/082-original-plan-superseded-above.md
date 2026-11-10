**Original plan, superseded above:** (they don't export in place). Their files are being tidied into four creator folders, each holding that creator's kits.

**Making a master, by hand, once per creator × armour mark × part type:**
1. Set a correct origin on one example part.
2. Run Add Socket at Origin.
3. Edit-select only the joint faces, then Capture Shape, named by key (e.g. `springles/grav/arms`).

The template stores the joint cloud, the origin socket and the fit type, including its snap offset, in the shared `shape_templates.json`.

**Applying it** (glue still to build): Match Shape → bake the origin to the matched socket → delete the socket. This runs for each part on import, or over a whole selection for bulk.

**Looking up the template:**
- creator comes from the path;
- armour mark comes from the TIOW tags the bridge already sends;
- part type comes from the TIOW category.

Fall back from creator/mark/type → creator/type → no template. A WEAK match is flagged, not applied.

**Notes:**
- No centring step is needed first: the match works at any position or rotation.
- The match is rigid, so do rescales after the origin step.
- `_shape_ensure_types` never overwrites an existing type. Use mark-specific type names only where the joints really differ.

**Resolved:** the other three creators don't export in place, hence the Shape Match approach above. Once the files are in one folder per creator, the creator can be read from the path the bridge already sends.
