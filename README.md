# FRC Toolkit

An Onshape custom feature library for FIRST Robotics Competition. Forty-six features that already
carry the vendor dimension, the bearing fit, the hole pattern the tube comes drilled on, and the
rule the part has to pass, so a build season does not start by rebuilding the same reference
geometry.

**Written:** 2026-09-04, against the source in this directory. **Status:** the source is public as
of 2026-09-09 and carries no license yet, so it is readable and not yet safely reusable. Read
[Status](#status-read-this-before-adopting-it) before adopting it.

---

## What this is

Eleven Onshape Feature Studio tabs plus a read me tab, held here as one `.txt` file per tab. All
forty-six feature dialogs are declared in `FRC ToolKit.txt`; the geometry that builds them lives in
nine tabs beside it; the standards, math and vendor profiles they share live in `FRC Core.txt`.

It is aimed at teams who cut parts on a CNC router, a waterjet or laser, a 3D printer, or by hand.
Hole, Lighten and Fillet Edges each ask which of those you use and change their allowances
accordingly, which is the difference between a feature that knows a process and a feature that
knows a number.

Every feature prints a report into its own dialog when it regenerates: what it built, the numbers
behind it, the checks that passed or failed, and where a figure came from. Those reports are where
the library explains itself, and they are worth reading rather than dismissing.

The `.txt` extension is a local convention only. Every one of these files is FeatureScript.

---

## Status: read this before adopting it

Stated plainly, because a team choosing tooling needs the real picture rather than the flattering
one.

| | |
|---|---|
| **Source complete** | 46 features, 21,565 lines across 11 code tabs, summed from the table below. Verified by counting the source: 46 `"Feature Type Name"` annotations, 46 `defineFeature` calls, 46 `frc*Build` functions, each with at least one `reportFeatureInfo` panel |
| **Not compiled since 2026-08-30** | The Onshape API allocation ran out at 2,608 of 2,500 and does not reset until 2026-10-13. No FeatureScript compiler has seen the current state of any tab |
| **Published as source, not as a feature** | These files are public as of 2026-09-09. Onshape still holds whatever was pasted before the allocation ran out, which is behind on every code tab, so there is no importable Onshape document. The deliverable is these files, pasted by hand |
| **Statically clean** | `python "_renders/_tools/verify.py"` reports `0 tab(s) with a problem` as of 2026-09-04: CRLF throughout, pure ASCII, no tabs, balanced brackets, no raw newline inside a string literal. Dialog labels are all 30 characters or fewer and tooltips 110 or fewer |
| **No license** | The read me tab's license section is a placeholder awaiting a decision from the owner. Publishing the repository did not change that: with no license, default copyright applies and nobody else can safely copy or redistribute this. Reading it is fine; adopting it is not, until a license is chosen |
| **No named maintainer** | Nothing in the source or the notes names a person, an address for reporting a wrong number, or a route for a fix from another team |

A static checker is not a compiler and says so itself. Treat every geometric claim below as checked
against the source and against the reference sheets in `_renders/`, and not against a regenerated
Part Studio.

**What that means for a team.** The library is not adoptable today, and the blockers are the last
three rows rather than the code. `_CONTINUE HERE.md` is the live account of what is fixed, what is
open, and why each open item is still open.

---

## What is in this directory

### The twelve tabs

Paste order matters, because `FRC Core.txt` exports symbols the other ten call. The full procedure
and the current line counts are in `_PASTE INTO ONSHAPE.md`.

| Order | Tab | File | Lines | What is in it |
|---|---|---|---|---|
| 1 | FRC Core | `FRC Core.txt` | 2403 | Materials, processes, fits, bearings, ties, structural limits, math and every shaft and bore profile. Imports nothing from the library |
| 2 | FRC Plate Geometry | `FRC Plate Geometry.txt` | 3802 | Lighten, Hole, Tube, Gusset |
| 3 | FRC Motion Geometry | `FRC Motion Geomtery.txt` | 1166 | Gear, Pulley, Sprocket, Shaft, Spacer |
| 4 | FRC Structure Geometry | `FRC Structure Geometry.txt` | 1703 | Slot, Bumper, Wheel, Frame, Gearbox |
| 5 | FRC Mechanism Geometry | `FRC Mechanism Geometry.txt` | 2916 | Elevator, Roller, Swerve Chassis, Shooter, Turret, Arm Pivot, Climber, Pneumatic Cylinder, Drivetrain |
| 6 | FRC Hardware Geometry | `FRC Hardware Geometry.txt` | 1307 | Bearing Block, Weight Budget, Center of Gravity, Battery Mount, Inspection |
| 7 | FRC Electrical Geometry | `FRC Electrical Geometry.txt` | 1281 | Electronics, Wire Path |
| 8 | FRC Fabrication Geometry | `FRC Fabrication Geometry.txt` | 1418 | Finger Joint, Insert Pocket, Sheet Layout, Teardrop Hole |
| 9 | FRC Manufacturing Geometry | `FRC Manufacturing Geometry.txt` | 1229 | Belt and Chain, Belt Path, Fillet Edges, Dogbone Corners, Measure |
| 10 | FRC Shop Geometry | `FRC Shop Geometry.txt` | 1112 | Parts, Bolt Pattern, COTS Pattern, Extrude Individual, Origin Cube, Design Constants, Mate Connectors |
| 11 | FRC Toolkit | `FRC ToolKit.txt` | 3228 | All 46 dialogs: parameters, defaults, bounds, preconditions. The only tab a Part Studio links to |
| - | READ ME | `READ ME.txt` | 311 | The read me as it appears inside Onshape, for a student who never sees this directory |

The dependency graph is shallow on purpose. `FRC Core.txt` imports only `onshape/std/common.fs`.
The nine geometry tabs each import Core and pass it along; `FRC Manufacturing Geometry.txt` and
`FRC Mechanism Geometry.txt` also import Motion for the belt, chain and involute tables;
`FRC Plate Geometry.txt` additionally imports `onshape/std/modifyFillet.fs`. `FRC ToolKit.txt`
imports Core and all nine. A defect in Core is a defect in many features at once, which is the
reason it is audited separately.

**The filename `FRC Motion Geomtery.txt` is misspelled.** The Onshape tab it holds is spelled
correctly, `FRC Motion Geometry`; only the local file is wrong. It is left as is because
`_PASTE INTO ONSHAPE.md`, `_AUDIT.md`, `_RENDER FINDINGS.md` and `_REMAINING IDEAS.md` all cite
source lines by that path, and renaming the file without them turns every one of those citations
into a dead reference.

### Working notes

These are the project's own records, not user documentation. They are honest about what is unproven
and should stay that way.

| File | What it is |
|---|---|
| `_CONTINUE HERE.md` | The live handoff. What is fixed, what is open, what a claim rests on. Read first when picking the work back up |
| `_STATUS.md` | Feature-by-feature state, snapshotted 2026-08-28. Its own header warns that the files moved under it |
| `_AUDIT.md` | Static audit, 2026-08-28: 0 blocking, 0 serious, 7 minor. All seven minor items are now closed, re-checked 2026-09-04 |
| `_PASTE INTO ONSHAPE.md` | The paste queue: order, files, line counts, last line of each |
| `_REMAINING IDEAS.md` | The backlog from a 52-source review, with each item's confidence stated |
| `_RENDER FINDINGS.md` | The findings the reference sheets produced |
| `_renders/` | 198 reference sheets and `index.html`. The sheets are the substitute for regenerating in Onshape: a builder is transliterated into Python, drawn, and the drawing is checked against what the feature claims |
| `_renders/_tools/` | The harness that makes them. `verify.py` is the byte-level source check to run after every edit; `README.md` there explains the method and the house style |

### Backups: which are superseded

Every `.bak*` file in this directory is older than the file it shadows and differs from it. All of
them are superseded as sources. Verified by comparing modification times and contents on
2026-09-04.

| Superseded | Current file it shadows |
|---|---|
| `FRC Core.txt.bak3`, `.bak4` | `FRC Core.txt` |
| `FRC Plate Geometry.txt.bak2`, `.bak3`, `.bak5`, `.coverage-verified` | `FRC Plate Geometry.txt` |
| `FRC Shop Geometry.txt.bak3`, `.bak5` | `FRC Shop Geometry.txt` |
| `FRC ToolKit.txt.bak3`, `.bak4`, `.bak5` | `FRC ToolKit.txt` |
| `FRC Structure Geometry.txt.bak2` | `FRC Structure Geometry.txt` |
| `FRC Fabrication Geometry.txt.bak2` | `FRC Fabrication Geometry.txt` |
| `READ ME.txt.bak` | `READ ME.txt` |
| `_PASTE INTO ONSHAPE.md.bak`, `.bak2`, `.bak4` | `_PASTE INTO ONSHAPE.md` |

**Nothing here is deleted, and nothing should be.** A backup someone kept on purpose is theirs to
remove. What matters is that none of them is a source to paste from or to merge from.

Two specifics worth knowing before anyone is tempted:

- **The four Plate backups still carry a fixed defect.** `FRC Plate Geometry.txt.bak2`, `.bak3`,
  `.bak5` and `.coverage-verified` each still contain the isogrid tether expression `L + s.rib`,
  which put a bar corner into the neighboring pocket. The current file contains zero occurrences.
  Restoring or merging from any of the four reinstates it silently. Counted directly, 2026-09-04.
- **`.coverage-verified` is not a numbered backup.** The name records a state that was checked, not
  a step in a sequence. It is 3279 lines against the current file's 3802, and is superseded in
  exactly the same way.

The numbering has gaps: Plate has no `.bak4`, Shop has no `.bak2` or `.bak4`. Nothing depends on
the sequence being complete.

---

## Installing it in Onshape

There are two paths, and which one a team uses depends on whether the library has been published to
an Onshape document they can reach.

### If a published document exists

This is the ordinary case for a team consuming the library, and it is the path the read me tab
describes for a student inside Onshape.

1. **Nothing to install.** A custom feature library is an Onshape document that other documents
   link to, and you do not have to own it to link to it. To hold a copy nobody else can change,
   copy the document first and link to your copy.
2. **Add it to your Part Studio.** At the right-hand end of the feature toolbar, past the standard
   features, is the custom features button. Open its menu and choose the entry that adds custom
   features from another document. The exact wording moves between Onshape releases. Find the
   document, then choose the **FRC Toolkit** tab from its list of Feature Studios. That one tab
   brings all forty-six.
3. **Link a released version, not the workspace.** Onshape will let you do either. Link the
   workspace and your robot can change shape overnight because somebody edited a feature you were
   using. Link a version and your models stay as you left them; when you want a newer one, change
   the linked version, regenerate, and see what moved.
4. **Where the features appear.** In that same custom features menu, listed under the library.
   Onshape lets you pin the ones you use most onto the toolbar.

### If it does not, which is the case today

The library has to be pasted in by hand, one tab at a time, in the order in the table above.
`_PASTE INTO ONSHAPE.md` is the procedure: it names each tab, its file, its line count and its last
line, so a truncated paste is caught rather than compiled. Paste Core first. A tab pasted before
Core shows unresolved symbols until Core lands, and Onshape clears those as you work down the list.

### A reasonable first hour, once it is in

- Put **Design Constants** at the top of a new Part Studio. It publishes the handful of numbers a
  whole robot is dimensioned from as Part Studio variables, so a sketch below it is dimensioned to
  `#frcHoleSpacing` rather than to a typed `0.5 in`.
- Sketch the frame outline, run **Frame** on it, then **Bumper** on the result.
- Extrude a plate, run **Hole** on it, then **Lighten**.
- Run **Weight Budget** on everything you have and see where you stand.

---

## The forty-six features

Grouped by what you are doing when you reach for one. The tab each is built in is given above.

**Plates, tube and frame.** Tube, Frame, Lighten, Hole, Gusset, Slot, Bolt Pattern, COTS Pattern,
Bearing Block, Finger Joint, Insert Pocket, Teardrop Hole, Bumper.

**Power transmission.** Gear, Pulley, Sprocket, Shaft, Spacer, Belt and Chain, Belt Path, Gearbox,
Wheel.

**Drivetrain and mechanisms.** Drivetrain, Swerve Chassis, Elevator, Arm Pivot, Turret, Climber,
Roller, Shooter, Pneumatic Cylinder.

**Electrical.** Electronics, Battery Mount, Wire Path.

**Shop and manufacturing.** Parts, Sheet Layout, Extrude Individual, Fillet Edges, Dogbone Corners,
Design Constants, Measure, Mate Connectors, Origin Cube.

**Checking the robot.** Weight Budget, Center of Gravity, Inspection.

The one-line description of each is in the read me tab, `READ ME.txt`, under "The features". It is
not repeated here, because two copies of forty-six descriptions drift apart and the tab is the copy
a student actually sees.

---

## The rules this library follows

These are stated in `READ ME.txt` and hold in the current source.

**Vendor data, and the source is named.** Dimensions come from the vendor's published drawing or
catalog, and where a vendor does not publish something the library does not guess it. Most swerve
module makers give an envelope and a fastener list but never locate the chassis holes, so those
modules are absent from the drilled patterns rather than approximated. The exception is the motor
and gearbox faces in COTS Pattern, taken from a community library, and the report says so at the
point of use.

**A rule of thumb is labeled as one.** Holding torque at two to three times an arm's gravity
torque, a quarter inch to an inch of roller compression, a fifth of the stage length as elevator
overlap, 85 to 90 percent drivetrain efficiency. All community practice, all used, all declared as
folklore in the field and in the report.

**Season limits are input fields, not constants.** Weight, frame perimeter, height, extension and
working pressure move with the game manual, so each is a field with the current season's number as
its default and the rule cited in its description. A feature that hard-codes this year's limit is
worth one build season.

**Fits are a choice, not a guess.** Arm Pivot, Bearing Block, COTS Pattern, Gearbox and Hole each
take a press, slip or clearance fit. Hole sets the allowance behind that choice from the process
cutting the part; the other four set it from the bore family.

**A patterned or mirrored feature lands where the pattern puts it.** Every feature that builds a
body of its own reads the pattern transform and moves what it made to the instance position. Tube
is the exception to watch, because it converts bodies you already have rather than building its
own, so pattern the extrude with it.

**Every panel is prose.** Onshape does not render newlines in `reportFeatureInfo`; it collapses the
panel into one wrapped paragraph. All forty-six panels are written as punctuated prose for that
reason. A new one must be written the same way.

---

## What it deliberately does not do

**It is not stress analysis.** Nothing here is FEA. The sizing help in Lighten, Arm Pivot, Gearbox
and the rest is arithmetic and rules of thumb, meant to get a first design close enough to build
and test. It will not tell you a part survives.

**The sizing models are first passes.** The drivetrain model is a point mass on a linear motor
curve. It leaves out battery sag, wheel scrub in turns, drivetrain windup and the driver. Use it to
get a gear ratio close enough to order gears, not to predict a match.

**It does not guess hole coordinates a vendor keeps in CAD.** Where a vendor publishes only a STEP
file, the feature asks you to type the pattern and says so in the report. Where a shape is needed
for the model but nobody publishes it, the report calls it a stand-in.

**It does not track the game manual for you.** The rule figures are the 2026 values, cited by rule
number where they appear. Check them against the current manual and change the fields. The manual
is the authority, not this library.

**It does not read or write any file.** A FeatureScript custom feature has no file access. Nothing
here consumes a bill of materials, a season definition or a team configuration, and nothing here
emits one. Reports are text in a dialog.

**It does not yet keep stable sub-ids.** No site calls `setExternalDisambiguation`, so deleting one
pocket renames every later one and a downstream sketch that referenced it drops. The fix is a
deliberate migration across roughly ten tabs rather than a defect patch, and it is recorded as
outstanding in `_CONTINUE HERE.md` rather than half done. Linking a released version rather than
the workspace is what makes such a change survivable when it lands.

---

## Relationship to Trellis

Trellis is a team-agnostic FRC tooling suite kept alongside this project. Its companion register,
`docs/05-COMPANIONS.md` section 4.4, carries a "CAD Feature Library" entry describing Onshape custom
features that already know vendor dimensions, bearing fits, process-dependent hole allowances and
rule compliance. **This toolkit is that entry.** The register was updated on 2026-09-04 to name it
and to state where it stands.

**Nothing crosses between them, in either direction.** This is not a gap waiting to be closed; it
is what the integration is. A FeatureScript custom feature cannot read a file, so it cannot consume
`season.json` or `team.json`, and Trellis reads nothing this library produces. Searched both sides
on 2026-09-04: no reference to Trellis, `season.json`, `team.json` or any JSON in these eleven tabs,
and no code in Trellis that names this project. It appears there only in its companion register and
in the screen that renders it, which is a register naming a project rather than a coupling. The relationship is the same shape Trellis already
records for MKCad, which it lists with a seam that carries nothing and is used inside Onshape.

**The one thing the two share is a discipline, not a data path.** Both treat this season's rule
figures as parameters rather than constants, for the same reason: a tool that hard-codes a limit is
worth one season. That agreement is a convention held by two projects, and nothing enforces it. If
one of them changes a default, the other will not know.

**Trellis does not require this and this does not require Trellis.** Both hold today, and both are
tests a companion has to pass.

---

## License, maintainer, contact

**Undecided, and it is the thing blocking everything else.** The read me tab has carried a
placeholder here since the tab was written, and the placeholder is still accurate. Four decisions
are open, all the owner's:

- **License.** What another team may do: use it, copy the document, modify it, redistribute a
  modified copy, use it in something they sell. Trellis is BSD-3-Clause and its companion contract
  asks a companion for a permissive license, on the ground that a copyleft one obliges a forking
  team to publish work they will not publish.
- **Attribution.** Whether use or a derivative should credit the original, and how.
- **Contributions and contact.** Whether fixes and new features from other teams are accepted, and
  where to report a wrong number. A wrong vendor dimension is the report worth encouraging above
  all others, because it is the one thing that would undermine everything the library claims.
- **Warranty.** That the library is provided as is, and that a team is responsible for checking its
  own robot against the current game manual.

Until the first and third are answered, this is a private working library rather than something
another team can adopt, whatever the code says.

---

## How this document was checked

Following the convention of the Trellis documents: what was measured, and what was carried across.

**Verified against the source on 2026-09-04.**

- The feature count and the tab each feature is built in. Counted three independent ways in the
  files: 46 `"Feature Type Name"` annotations and 46 `defineFeature` calls in `FRC ToolKit.txt`, and
  46 `frc*Build` functions across the nine geometry tabs, named and matched one to one against the
  feature list.
- That every one of the 46 builders contains at least one `reportFeatureInfo` call, by attributing
  each call site to its enclosing function. Gearbox has two, one per branch. None has zero.
- The import graph, read from the header of each file.
- The line counts and last lines in the tab table, measured rather than copied from the paste queue.
- That `verify.py` reports `0 tab(s) with a problem`, by running it.
- That no dialog label exceeds 30 characters and no tooltip exceeds 110, which closes the last of
  the seven minor items in `_AUDIT.md`.
- That every `.bak*` file is older than the file it shadows and differs from it, and that the four
  Plate backups still contain `L + s.rib` where the current file contains none.
- That no code in either project references the other, by searching both directories. Trellis names
  the toolkit in its companion register and nowhere else.
- The API allocation, read from Onshape rather than from `_CONTINUE HERE.md`: 2,608 requests
  against a limit of 2,500, in a cycle that ends 2026-10-13. Both figures in the status table are
  the live ones.

**Carried across from the project's own notes, and not independently re-derived.**

- The one-line description of each feature, which lives in `READ ME.txt`. Spot-checked against the
  source for the features whose behavior changed most recently, not re-derived for all forty-six.
- The history in the "rules this library follows" section, which restates `READ ME.txt`.
- The account of what is fixed and what is open, which is `_CONTINUE HERE.md`. That document is
  careful about the difference between a mechanically established finding and a reading, and this
  one does not try to relitigate it.
- Everything about the state of the Onshape document itself: what is published there, and how far
  behind it is. Nothing here can reach it.

**Not checked by anyone, and worth saying twice.** None of this has been compiled or regenerated
since 2026-08-30. The reference sheets in `_renders/` are a transliteration of the builders into
Python, which is a real check and is not the same check as Onshape building the geometry. The first
regeneration after the allocation resets is the first real test, and `_CONTINUE HERE.md` names the
features to put in front of it.
