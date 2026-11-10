**Proposed file layout (17 Oct 2026):**
- **Top-level folders** are named `<Creator> - <Mark>` from fixed lists. Each is connected in TIOW as its own folder, so TIOW's Source filter becomes the creator + mark filter. Blender reads creator and mark from the same folder name.
- **Slot** comes from the kit's own subfolders through an alias list (Helmets → Heads, Chests/Bodies → Torsos, …). Side comes from the direction the disc faces.
- **Raw files only;** paths containing "support" are skipped.
- **Misc bits** go in `Bits - <Type>` folders. A bit family with a repeatable mount gets one socket type and one master, with no creator correction. Bits with no mount are free placement: imported at the cursor and positioned with Settle / Conform Detail.
- **Creator-specific adapters** (e.g. the Mar Fil waist filler) live with that creator.
- **Don't run TIOW's Organise on this tree:** it moves everything into `Master Pieces/<Category>/<Variant>`. Duplicate cleanup is fine.
