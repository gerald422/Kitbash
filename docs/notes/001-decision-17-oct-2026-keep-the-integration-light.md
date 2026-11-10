**Decision (17 Oct 2026): keep the integration light.** TIOW only works as a browser that sends a file into Blender. Part Sockets does all the work before and after. Built and tested: `Desktop\TIOW Blender bridge\`.
- **`tiow_inbox.py`**: a Blender add-on. It checks `%LOCALAPPDATA%\TIOW-FTRP\local-data\blender-inbox` every 0.5 s and imports each requested STL into the open scene. Each part goes into a collection named after its TIOW category, centred on the 3D cursor at mm scale, and is left selected and active.
- **`apply-blender-bridge.mjs`**: patches TIOW with anchored edits and keeps backups; `--undo` restores the originals. It adds *Send to Blender* (double-click a card, right-click menu, or the details button) and a `/api/local/blender` server route. The route resolves the file through the server's own `safe()` check and writes one request JSON.
- A `.listening` heartbeat tells TIOW whether to say "Sent" or "Queued".

The batch-origin and manifest designs below are parked. They are reference if a batch step is wanted later.
