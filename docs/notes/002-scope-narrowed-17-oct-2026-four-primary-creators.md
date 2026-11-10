**Scope narrowed (17 Oct 2026): four primary creators** — Mar Fil, Marta PunkGirl, Springles, Turtle Ninja.

**Mar Fil, measured on 4 kits in `Desktop\All Mar All the time`:** parts are exported in assembly position. Within a kit, every arm's shoulder plane sits at the same coordinate:

| Kit | Right-arm shoulder plane | Mirrored arms |
|---|---|---|
| Intercessor | max Y = −5.7 | min Y = +5.7 |
| Terminator | max X = −6.0 | — |
| Aggressor | min X = +5.5 | — |
| Veteran | min X ≈ 5.2–5.5 | max X ≈ −5.3 |

So within a kit, one hand-set origin is the exact origin for every sibling: copy the frame, with no geometry search and no roll problem. Templates are per **kit + slot**, not per creator, because the left–right axis differs between kits (Y for Intercessors, X for the others). The left side should be derivable by reflecting across the kit's mirror plane. `Scaling.txt` gives per-kit rescales (e.g. Intercessors 95%).

**Offsets:** with one shared origin convention (joint-face centre, +Z out of the joint, +Y forward), one offset per joint type serves every creator. Creator-specific fit types are only needed where the joint is physically different. Store those as Joint Library sets with distinct type names, because loading two sets unions them.
