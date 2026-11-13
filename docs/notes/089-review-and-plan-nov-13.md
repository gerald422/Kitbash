**Review of the whole project against Josh's aim, his answers, and the order agreed (Nov 13).**

Aim, in his words: a repeatable, quick way to add several makers' Space Marine STLs for a custom renegade chapter,
kitbash them fast (quick snap), make them manifold, allow sub-assemblies, resin print.

- **Findings.** (1) Adding a maker is not quick: `kits/creator/add_creator.py` fits heads and pads only, every kit of
  torsos / arms / legs / packs has needed its own script, and it is written for the container (staging archives,
  `/home/claude`), which a session on the PC does not need. (2) Coverage: 2,547 of 6,887 parts without a fit, 703 of
  877 torsos without sockets; one reference helmet and one reference pad decide every head / pad fit. (3) No
  placement baseline (since recorded, notes 088). (4) Bad snaps are fixed one at a time; the Nov 6 shared causes are
  open; `corrections.jsonl` has 7 lines. (5) Mesh faults are only met in Finalise (since: Caliper Repair, 088). (6)
  Finalise stops in Blender: no export, one model at a time, pegs never printed. (7) Origins at the joint still open.
- **His answers.** Time goes on adding a maker and on fixing bad snaps. New makers are rare; new parts from the makers
  already in the library are frequent, kits and bits about equally; `D:\new cults` (2,500 downloads) is not coming in
  wholesale. Fit everything up front (not on first use). Either he or Claude adds a maker. Prints solid, supports in
  Lychee; has printed finalised models but never the pegs; the split depends on the pose. Hiding aquila / seal /
  scroll parts is enough. Worst snaps: **pauldrons, necks, accessories**. **TIOW-FTRP is no longer used**: the Squad
  Builder replaced it. Sharing the page is for testing and limited printing only, not a goal. The STLs on D: have
  **no backup** (one external exFAT drive). Old folders may be archived.
- **Order agreed.** 1 add-a-maker native on the PC with a saved recipe per maker (a monthly drop is one command);
  2 automatic fits for arms, legs, torsos; 3 fit the parts that have none, matching each against the same maker's
  fitted parts instead of one reference; 4 the shared causes of bad snaps, starting with pauldrons, necks and
  accessories, plus a standing audit; 5 origins at the joint; 6 Finalise export and a peg test piece; 7 housekeeping.
- **Done the same day.** `old-*` (17), `sidecars-*` (4) and `library build` moved out of the bridge folder to
  `~\Desktop\TIOW Blender bridge archive\` (1.1 GB; nothing current referred to them, `kb.py verify` 20 of 20 after).
  `docs/reference.md` gained the section for a session running on the PC.
- **Not decided**: the 3 Turtle Ninja files Caliper kept back, the swap's 5% triangle rule, where a backup of the
  STLs should go. **Not done**: retiring the TIOW-FTRP bridge from the repo (`bridge/`, the bridge template in
  `tools/gen_joints.py`, three installed bridge files, four loose bridge files in the bridge folder).
