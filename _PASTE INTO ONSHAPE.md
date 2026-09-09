# Paste queue

Rewritten 2026-08-31, after the reference-sheet audit. **Eleven of the twelve tabs changed.** Only
READ ME is untouched.

**Paste in this order.** It has not mattered before; it does now. FRC Core gained
new exported enums and functions that nine other tabs call, and FRC Toolkit calls
all of them. A tab pasted before Core shows an unresolved symbol until Core lands.
Onshape recompiles as you go, so those errors clear as you work down the list.

| Order | Tab in Onshape | File | Lines | Last line |
| --- | --- | --- | --- | --- |
| 1 | FRC Core | `FRC Core.txt` | 2403 | `    };` |
| 2 | FRC Plate Geometry | `FRC Plate Geometry.txt` | 3802 | `}` |
| 3 | FRC Motion Geometry | `FRC Motion Geomtery.txt` | 1166 | `}` |
| 4 | FRC Structure Geometry | `FRC Structure Geometry.txt` | 1703 | `}` |
| 5 | FRC Mechanism Geometry | `FRC Mechanism Geometry.txt` | 2916 | `}` |
| 6 | FRC Hardware Geometry | `FRC Hardware Geometry.txt` | 1307 | `}` |
| 7 | FRC Electrical Geometry | `FRC Electrical Geometry.txt` | 1281 | `}` |
| 8 | FRC Fabrication Geometry | `FRC Fabrication Geometry.txt` | 1418 | `}` |
| 9 | FRC Manufacturing Geometry | `FRC Manufacturing Geometry.txt` | 1229 | `}` |
| 10 | FRC Shop Geometry | `FRC Shop Geometry.txt` | 1112 | `}` |
| 11 | FRC Toolkit | `FRC ToolKit.txt` | 3228 | `  });` |

READ ME is unchanged at 311 lines, last line
`//     its own robot against the current game manual.`

Core's last line really is an indented `};`. It is the close of
`FRC_BORE_DEFAULTS`, the last declaration in the file, not a truncation.

## The five features that did not build what they promised

Every one is fixed. These are the reason for the pass.

| Feature | What was wrong |
| --- | --- |
| **Shooter** | The wheel bore was never cut. The extrude used a region query that included the inner loop, so every wheel came out a solid disc while the panel reported its inertia with the annulus formula. Wrong geometry and wrong flywheel numbers. |
| **Sprocket** | "Lighten the web" drew each spoke bar as a full diameter and extruded an unfiltered region query, so the subtraction tool was the whole disc. It removed the hub, the spokes and the web and left a bare rim, and because the boolean succeeded the panel reported success. Odd spoke counts also came out doubled. |
| **Finger Joint** | Two parts that did not overlap threw inside a silent try, both copies survived, the first was read as the overlap, and the feature cut finger slots along the whole length of both parts with nothing said. |
| **Frame** | The shell ran after the holes were punched. Shell offsets every remaining face inward, hole cylinders included, so every hole got a solid collar bridging both walls and the cut list overstated the mass. |
| **Pulley, T5 and T10** | The groove flank ran over twice the depth it should, so the flank angle came out 10.3 degrees instead of 20 and the groove measured 2.213 mm wide against the 2.65 mm the table carries. A T5 belt tooth could not enter it. |

## The three library-wide defects

| Defect | Effect |
| --- | --- |
| **frcDelaunay broke on cocircular points** | The cavity fragmented and new points were fanned to edges on the far side of the mesh, laying triangles across existing ones. A ring of 37 points gave 125 triangles where 35 were due, at 22 times the true area, and 45 to 50 per cent of mixed layouts were wrong. A round plate outline IS a cocircular point set, so the Lighten truss hit this every time. Now exact on 2800 test sets and byte-identical on 600 of 600 generic clouds. |
| **frcConvexHull sorted on x only** | Monotone chain needs a full lexicographic sort. A plate with three holes up one edge produced a hull at half its true area, so HULL gussets came out undersized. 1255 wrong hulls in 3910 column-shaped layouts; zero in 11817 after the fix. |
| **Every bearing seat got half its fit** | frcBoreAllowance is radial and four callers added it to a diameter. A press fit gave half a thousandth of interference where the fit class asks for one, which is a bearing that spins. Fixed at Bearing Block, Arm Pivot, Gearbox and COTS Pattern. |

Also fixed: the involute spline tooth angle had the wrong sign, so a broached bore
came out about 2.3 thou narrower than the shaft it had to accept; plywood is 680
kg/m^3, not 600; ThunderHex corner circles are stored in millimetres; and the
Inspection Envelope, which carried no material, was being weighed as solid
aluminium at 4214 lb against a 150 lb budget without anyone putting it in a group.

## Pocket sizing and the buckling model

*Pocket sizing follows the load case, and the buckling model was corrected.*
`frcAutoSizing` now takes `definition.loading`. Across the face it keeps the
span-to-thickness beam rule it always used. Edge on, which is the default, it
sizes from the rib's slenderness against its material, which is the number that
governs a plate working as a web. The beam rule used to be applied to every
plate whatever the dialog said it was carrying, so the commonest plate in the
library was sized by the rule for the load case it was not in.

Two corrections went in on top of that, and both make the bound smaller:

* **The ratio is applied to the least section dimension, not the rib width.**
  `frcSlendernessLimit` returns a span over a DEPTH, and the depth is the side
  that sets the radius of gyration. A bar buckles about its weakest axis, and a
  rib routed into a plate is a bar of rib width by plate thickness, so on any
  normal FRC plate the thickness is the smaller of the two. Multiplying by the
  rib width alone was optimistic by exactly the ratio between them, a factor of
  two on 0.125 in stock with a 0.25 in rib. Core now exports `frcBuckleSpan`,
  which takes the minimum internally so no caller can pick the wrong one.
* **The effective length factor went from K = 0.65 to K = 0.8.** The published
  limits were derived at the fixed-fixed value, which is fair for a rib buckling
  IN the plane of the plate but too generous for the out-of-plane mode that
  actually governs: the ribs meeting one at a node lie in the same plane and
  resist out-of-plane end rotation only weakly. Every limit was rescaled by
  0.65 / 0.8 = 0.8125. 6061 went from 20.1 to 16.3.

The aggression multipliers were then raised, because with an honest bound the
old ones were holding it back twice: conservative 0.60 to 0.75, balanced 0.80 to
0.90, aggressive unchanged at 1.00. Conservative at 0.60 was incoherent, giving
a smaller pocket edge-on than the beam rule allows across the face.

**Measured in the Python raster model**, not estimated. 0.125 in 6061, CNC,
1/4 in end mill, 0.250 in rib, edge-on. Each cell is per cent removed and the
pocket count. The 1.50 in column is what the library did before any of this:

| plate | old, 1.50 in | conservative, 1.53 in | balanced, 1.83 in | aggressive, 2.04 in |
| --- | --- | --- | --- | --- |
| 10 x 11 in, 8 holes | 56.2 %, 48 | 55.4 %, 50 | 60.0 %, 36 | 62.5 %, 30 |
| 9.5 x 13 in, 5 holes | 57.1 %, 52 | 57.1 %, 52 | 59.8 %, 42 | 64.3 %, 32 |
| 12 x 8 in, 6 holes | 53.3 %, 50 | 53.4 %, 50 | 63.3 %, 26 | 60.3 %, 32 |
| 10 x 8 in, no holes | 56.4 %, 38 | 56.5 %, 38 | 62.7 %, 26 | 62.6 %, 26 |
| **mean** | **55.8 %** | **55.6 %** | **61.5 %** | **62.4 %** |

So the shipped default takes about 13 per cent off the weight of a lightened
plate against what the library did before, and aggressive about 15 per cent.
Conservative deliberately lands where the old behavior was: it is the anchor,
not a regression.

Two things in that table are worth knowing before you read too much into it.
Removal is **not monotonic in pocket size**: on the 12 x 8 in plate the balanced
setting removes more than the aggressive one, 63.3 against 60.3 per cent, and on
the 10 x 11 in plate conservative removes slightly less than the old smaller
pocket. This is real, not noise. The triangulation reorganizes when the size
bound moves, and a coarser target can produce a mesh that fits fewer pockets and
leaves more wall. Do not assume a bigger pocket always means a lighter plate on
a particular outline; check the panel.

**Where the safety actually lives**, since several dials moved: the protection is
the K and the least-dimension correction, both of which are physics, plus the
0.85 margin inside `frcSlendernessLimit`. Balanced sits at 0.85 x 0.90 = 0.765 of
the Euler-at-yield span computed at K = 0.8. The aggression multiplier is a
preference dial on top of that and was never what kept a rib from buckling.

## The new part color system

FRC Design Constants gained **Custom part colors**: a master toggle with a color
per part class beneath it. A team that wants every plate in its own color says so
once, at the top of the Part Studio, and every feature below obeys.

It is a named palette rather than three sliders per class, because FeatureScript
has no color picker parameter and thirteen classes of red, green and blue would
be thirty nine boxes in one dialog.

The thirteen classes: plates and gussets, tube and structure, gears and sprockets
and pulleys, shafts and spacers, wheels and rollers, bearing blocks, bumpers,
pneumatics, electronics and wiring, game piece contact, envelopes and reference,
layout copies, everything else. There is deliberately no printed class, because
printedness is a property of the material and every part already carries one.

**It fails safe.** The scheme travels as a Part Studio variable, and no feature in
this library has ever read a variable before. The read is guarded, so with no
Design Constants feature, or the toggle off, or a class left at "Leave it the
material", every part keeps exactly the color it has today. Existing documents do
not move until you switch it on.

Translucency survives a team color. Envelopes, keep-outs, bumper padding, the
shooter hood and any polycarbonate part keep their alpha, because the color is
rebuilt at the caller's own alpha rather than replaced.

On the bumper, only the cover and the whole-bumper envelope take the team color.
The plywood backing and the pool noodle keep their own, because that is what a
real bumper looks like, and because three colors are what let you tell the layers
apart in an exploded view.

FRC Parts no longer carries three red, green and blue reals of its own. They
were the library's only color override before there was a studio-wide one, and
two ways to set a color, one of them reaching a single feature, is worse than
one that reaches all of them. Parts now colors from exactly what every other
feature colors from: the class scheme if there is one, the material if there is
not. `FRC_COLOR_BOUNDS` went with them, and is the only export removed in this
pass. An existing Parts feature in a saved document simply drops the three
values; nothing else about it changes.

FRC Lighten also gained a **Part type** dropdown, so lightening a tube colors it
as structure rather than as a plate. FRC Extrude Individual, which until now gave
its parts no name, no material and no color at all, gained a Material field and
now finishes them like every other feature.

### What to look at after pasting

1. An L-shaped or notched plate, truss pattern. The outline walk is new and this
   never worked before.
2. A truss plate, balanced, edge-on. Expect about half the pockets it used to cut,
   visibly bigger, and no overlapping triangles.
3. FRC Shooter. The wheels should have a bore through them.
4. FRC Sprocket with "Lighten the web" on. It should have a hub, spokes and a web.
5. FRC Frame with holes punched. No collar around any hole.
6. A T5 pulley. Measure the groove at the outside diameter: 2.65 mm.
7. FRC Design Constants, Custom part colors on, one class set. Regenerate a plate
   and confirm only that class moved.
8. Cable tie nubs on, any lattice pattern. Every rib long enough gets one bump pair
   at its middle, and they should read as smooth lobes rather than a saw tooth.

### Known, not fixed

* Crescent slivers survive beside boss rings on isogrid, honeycomb and circles.
* The large-boss truss plate still leaves some solid regions.
* Sheet Layout copies DOUBLE COUNT in FRC Weight Budget. Each copy is a second body
  with the same volume as a part already in the studio, and the weigh's fallback
  group is every solid body in the Part Studio. It cannot be excluded in code:
  getProperty returns undefined inside a custom feature, so the weigh can read
  neither the copies' names nor their materials. Delete a layout before weighing;
  the Sheet Layout panel now says so.

---

## What this document is now

There is no API publish any more. The Onshape allocation ran out, the FeatureScript MCP server
has since disconnected, and nothing can be published, compiled or test-regenerated from here.

So the twelve .txt files in this directory are the deliverable. Each one is the
full text of one Onshape Feature Studio tab, and the way it gets into Onshape is that the owner
opens the tab in a browser, selects all, and pastes the file over it. This document is the order
to do that in, and what to look at after each one.

Two consequences of the change worth stating plainly.

- **The element ids do not matter any more.** The old queue spent a section on which tab was
  `d81c97cbe5f982298dc3afc8` and which was a guess. Pasting picks the tab by name in the browser,
  so nothing here needs an id. They are still recoverable from the ten `export import` lines at
  the top of FRC ToolKit.txt if a tool ever needs them again, though the mapping from id to tab
  name is no longer derivable from any file, because the Toolkit's header comment naming the tabs
  was removed in the recovery trim.
- **The staged `.fs` artifacts are dead.** `hardware_WITH_PRINTED_DENSITY_unpublished.fs`,
  `frc-structure-geometry.PENDING-PUBLISH.fs`, `electrical_WITH_FIXES_unpublished.fs`,
  `work/plate_STAGED.fs` and `work/toolkit_STAGED.fs` were the previous queue's payloads. Every
  change in them, and a day's work on top, is in the .txt files. Do not paste from them. Keep
  them as history or delete them.

## Read these two warnings before pasting anything

Both were paid for once already today, and both survive the change of workflow. The manual
workflow makes the first one more dangerous, not less.

### Warning one. Do not paste a stale import version line over a live one

Every tab except FRC Core carries lines of this shape near the top:

```
export import(path : "cb38778324c9d1cffc601ee7", version : "578eb867bbdba7daf29ca549");
```

The `path` is the element id of another tab. The `version` is written as `""` when a tab is
authored and **Onshape rewrites it to a concrete version id when the tab is saved**. A file on
disk therefore records the version that was current the last time that file was pulled or
written, and nothing on disk can tell you whether Onshape has moved on since.

This bit once already. A mirror of the Plate tab was byte-exact to live in every respect except
that one line: it carried `1abf028b893418613cf377fe` where a live pull returned
`578eb867bbdba7daf29ca549`. Every check short of reading the import line said the file was
current. Publishing it would have rolled the Core import back one version, silently, with no
error and no visible difference in the tab.

Under the paste workflow the same accident is one keystroke away, because selecting all and
pasting replaces those lines along with everything else.

**What to do, on every tab that has import lines:**

1. Before you paste, select the import lines in the Onshape editor and copy them somewhere.
   There are one to ten of them; they are all in the first dozen lines.
2. Paste the file.
3. Paste the lines you saved back over the ones that arrived with the file.
4. Compare. If the two sets are identical, nothing was at risk on this tab. If a `version`
   differs, the one that was already in Onshape is the right one, every time.

Every file on disk currently pins Core at `578eb867bbdba7daf29ca549`. That is what was current
when these files were last written. It is not evidence about what Onshape holds now.

FRC Core and READ ME have no `export import` lines, so this warning does not apply to them.

### Warning two. A truncated paste compiles and drops every feature after the cut

A payload that is cut short is still syntactically valid FeatureScript if the cut lands on a
declaration boundary. So it compiles. So nothing reports an error. Every declaration after the
cut is gone and nothing says so.

This bit the Toolkit tab today. The file was 154311 bytes, the publish was truncated, and the
last three declarations in the file, which alphabetically are Weight Budget, Wheel and Wire Path,
were lost. All three features vanished from every Part Studio linked to the workspace, and the
tab compiled the whole time.

A browser paste can truncate for its own reasons: a select-all that did not reach the end, a
clipboard limit, an editor that was still loading. The failure looks exactly the same.

**What to do, on every tab:**

1. Before you paste, note the file's last line and its line count. They are in the table below,
   and you can re-measure them from the file, which is the safer habit because these files are
   being edited.
2. After you paste, scroll to the bottom of the editor. The last line must be the file's last
   line, at the file's line number. Nine of the twelve tabs end with a bare `}`, so the line
   number is the check that matters.
3. **On FRC ToolKit, count the features as well.** Open the custom feature list in any Part
   Studio linked to the document. There must be 46, alphabetically Arm Pivot first and Wire Path
   last. Features are declared alphabetically, so a truncation always eats the end of the
   alphabet first: if **Weight Budget, Wheel and Wire Path** are all present, the file is whole.
   This is the tab it already happened to, and the only tab whose loss takes features away from
   every team linked to the workspace rather than breaking a build.

Do not treat "the tab compiled" as evidence of anything. It compiled last time too.

## The order, and the older table it used to carry

**Paste from the table at the top of this document.** The table in this section was measured on
2026-08-28, before the reference-sheet pass rewrote eleven tabs, so every line count in it is low
by hundreds of lines, it counts 45 features rather than 46, and it lists READ ME as item 11. Both
orders satisfy the dependencies, but only the top table's counts match the files on disk, and a
count that matches is the only thing standing between a truncated paste and features quietly
disappearing. This one is kept because its last column records why each tab sits where it does,
which the top table does not repeat.

Paste in this order. The ordering is a dependency order: a tab that defines a name must be in
Onshape before a tab that uses it, or the second one will not compile while you are working.
Every tab will end up right regardless of order once all twelve are in, but working in this order
means you never see a spurious error.

FRC Core imports nothing from the library. Nine geometry tabs each import Core. FRC Manufacturing
Geometry and FRC Mechanism Geometry also import FRC Motion Geometry. FRC Toolkit imports all ten.
Nothing else crosses tabs, and no name is exported by two tabs.

| Order | Tab in Onshape | File to paste | Lines | Last line | Why here |
| --- | --- | --- | --- | --- | --- |
| 1 | FRC Core | `FRC Core.txt` | 1621 | `    };` | Imports nothing. Nine tabs depend on it. No import line to protect. |
| 2 | FRC Motion Geometry | `FRC Motion Geomtery.txt` | 1044 | `}` | Two other geometry tabs read its belt, chain and gear tables. |
| 3 | FRC Plate Geometry | `FRC Plate Geometry.txt` | 2160 | `}` | Core only. Carries the Lighten truss fix, so get it in early and leave time to look at it. |
| 4 | FRC Structure Geometry | `FRC Structure Geometry.txt` | 1485 | `}` | Core only. Bumper reads `definition.perimeterLimit` with a fallback to its own constant, so this tab is correct whether or not the Toolkit has landed yet. |
| 5 | FRC Hardware Geometry | `FRC Hardware Geometry.txt` | 1155 | `}` | Core only. Must be in before the Toolkit: it defines `FRC_INFILL_BOUNDS` and `FRC_WALLS_BOUNDS`, which the Toolkit's two new printed-density fields are bound by. |
| 6 | FRC Electrical Geometry | `FRC Electrical Geometry.txt` | 1128 | `}` | Core only. Adds `FRCComponent.NEO_550`, which the Toolkit needs no change to show. |
| 7 | FRC Shop Geometry | `FRC Shop Geometry.txt` | 984 | `}` | Core only. Defines `FRCCotsPattern.GEARBOX_SPORT`, which the Toolkit branches on. |
| 8 | FRC Fabrication Geometry | `FRC Fabrication Geometry.txt` | 866 | `}` | Core only. |
| 9 | FRC Manufacturing Geometry | `FRC Manufacturing Geometry.txt` | 1022 | `}` | Reads `frcBeltData` and `frcChainData` out of FRC Motion Geometry, so it goes after item 2. |
| 10 | FRC Mechanism Geometry | `FRC Mechanism Geometry.txt` | 2767 | `}` | Reads `frcGearOutline` out of FRC Motion Geometry, so it goes after item 2. Defines `FRC_PERIMETER_BOUNDS`, which the Toolkit's new Bumper field is bound by, so it goes before item 12. |
| 11 | READ ME | `READ ME.txt` | 311 | `*/` | Nothing depends on it and it depends on nothing. It is one block comment after a `FeatureScript 3044;` line. Placed here so it is not forgotten behind the Toolkit. |
| 12 | FRC Toolkit | `FRC ToolKit.txt` | 3071 | `  });` | Last, always. It imports all ten supporting tabs and uses names from every one of them. It is also the largest file and the one truncation has already eaten. |

Line counts and last lines were measured at 15:13 UTC. Three of these files were rewritten by
other agents within the fifteen minutes before that, so re-measure before you paste rather than
trusting the number in this table.

## What to check after each paste

Three checks apply to every tab, and then some tabs have one of their own.

**On every tab, in this order:**

1. The import lines match what was in Onshape before the paste. Warning one.
2. The last line and the line number match the file. Warning two.
3. The tab shows no compile error. Nothing in this library has been through a FeatureScript
   compiler since the connection dropped, so this is the first real compile of a full day's work,
   and it is the first thing that can fail.

**Then, per tab:**

| Tab | What to look at, beyond the three checks |
| --- | --- |
| FRC Core | Nothing specific. Core was not changed structurally today; its exports are unchanged. If it compiles, the other ten have their foundation. |
| FRC Motion Geometry | Build a rack: FRC Gear, Rack, 20 DP, 12 teeth. The panel must print a rack length of 1.8386 in, not 1.8850 in. Build FRC Pulley, HTD 5 mm, 24 teeth, 0.375 in belt: the rim must measure 0.4488 in, belt width plus 2 mm, flanges on or off. |
| FRC Plate Geometry | The big one. Run FRC Lighten with the truss pattern on the same three plates that produced the original defect photographs and compare the results against those photographs. Then re-run `work/harness_full.fs` across its five cases: free rib ends should go to zero or as close as the extension cap allows, and the mirror counts should reach the segment count on the symmetric case. The photographs are the check; the counts are a proxy. Then regen FRC Hole, FRC Tube and FRC Gusset once each, because they share this tab and it stopped compiling once already today. |
| FRC Structure Geometry | Run FRC Bumper on a 27 by 27 in frame with a 0.75 in backing. Expect `Bare frame : 108 in outline, no bumpers` and `R104 bare frame outline at most 110 in : yes`, followed by two lines pointing at FRC Inspection. Expect the reported bumper mass to be roughly a fifth lower than the last run, from the foam correction. Then run FRC Frame on two members of different lengths and read the parts list: names must read like `Tube 2x1x0.0625 - 27 in`, not `Frame Member 1`. |
| FRC Hardware Geometry | Run FRC Weight Budget with a group material set to **Pool noodle** and again with **Wire bundle**. Until about 14:37 UTC today both threw a return-type failure on those two materials, and the fix has never been compiled. This is the single most important check in the round after Lighten. Then weigh a printed bracket at 20 percent infill and 3 walls and compare with the slicer: expect roughly 35 to 45 percent of solid. Then run FRC Inspection with the bodies field empty and a height limit below everything in the model: the panel must say the measured height is not checked and no warning may name it. |
| FRC Electrical Geometry | Place FRC Electronics with **NEO 550** selected and measure the bolt circle: 25.0 mm, not 2.000 in. Place it with **NEO** selected and confirm the six-hole pattern is unchanged and the UNRESOLVED note prints. Run FRC Wire Path with the bundle body on, then FRC Weight Budget over it, and confirm the harness now carries a non-zero mass. |
| FRC Shop Geometry | Place FRC COTS Pattern on the Sport gearbox face and confirm the hole count and start angle fields appear, and that the bore checkbox reads "Cut the bore as well". Confirm the report names its source and says which figures are community data. |
| FRC Fabrication Geometry | Build FRC Finger Joint on two 0.125 in plates at a right angle with T-bone relief and a 0.125 in cutter. Measure an interior finger across the joint line: it must be the full `L / n` with no scallop at the root. |
| FRC Manufacturing Geometry | Cut a square pocket, run FRC Dogbone Corners on it, then linear-pattern the dogbone feature to 3. Relief must appear in all three pockets; before today all three landed in the first. Run FRC Belt and Chain on round cord and confirm the loop length appears once, not twice. |
| FRC Mechanism Geometry | Insert FRC Swerve Chassis at defaults and note the Mass line. Change Mount style to "Bottom, plate on rails" and regenerate: the panel must gain two lines reading `NOTE  Bottom mount picked; top mount was built.` and `Set the corner cut, pattern and height by hand.`, and the Mass line and part list must be identical. Change it back and the two lines must disappear. Any geometry change there is a failure of the fix, not a success. |
| READ ME | It is a comment, so the only failure mode is a broken comment. Confirm the tab compiles and that the text renders from `FRC Toolkit` through the license placeholder at the end. |
| FRC Toolkit | Count the features: 46, Arm Pivot first, Wire Path last. Confirm Weight Budget, Wheel and Wire Path are all present. Open FRC Weight Budget and confirm the two new fields, Printed infill and Printed wall count, render and accept values; a missing bound shows as a dialog that will not open. Open FRC Bumper and confirm the new Frame perimeter limit field renders at 110 in, in every output mode, not just in All. |

## After all twelve are in

Regenerate something patterned. Thirty features gained pattern and mirror support today, each
with a hand-placed transform, and not one of them has been executed. A wrong placement raises no
error: the seed comes back and the instances do not, or nothing moves at all.

Five that between them cover every placement convention used:

| Feature | Convention it tests |
| --- | --- |
| FRC Slot | The move sits before the boolean, because a subtraction consumes the cutters. |
| FRC Frame | The move sits after the cut lengths are measured, because each length is read along that member's own axis from its own start point. |
| FRC Wheel | The move sits after `frcApplyPart`, so material and color go on the body that gets moved. |
| FRC Gearbox | The move is guarded by a `moved` flag, so the layout sketch still moves when no bores are cut. Regen twice, bores off and bores on. |
| FRC Belt and Chain | The move is guarded by `made`, because nothing is built when the path is not drawn. Regen twice, path on and path off. |

Then work down the priority list in STATUS.md, which starts with Lighten.

## What is not known about this queue

- **Whether any of it compiles.** No FeatureScript compiler has seen a line of today's work. The
  static audit at `_AUDIT.md` expects it to: 2,810 identifier uses resolved with zero
  unresolved, zero cross-tab reference violations, zero references to a non-existent enum member,
  balanced delimiters in all eleven files, no duplicate export, and 45 of 45 features resolving to
  an exported builder. That audit predates Teardrop Hole, so the count is 46 of 46 today. A text scan cannot typecheck. It cannot see a `ValueWithUnits` passed where
  a number is wanted, or a map field read off a record that does not carry it.
- **How far behind Onshape is.** Every tab on disk is ahead of what is published by an unknown
  amount, and nothing available here can compare them. Assume all twelve need pasting.
- **What the live import versions are.** Every file on disk pins Core at
  `578eb867bbdba7daf29ca549`. That records what was current when the files were written, not what
  Onshape holds now. Warning one is the whole procedure for this and there is no substitute for
  reading the live line.
- **Whether the files have changed since 15:13 UTC.** Other agents were editing the library
  throughout the afternoon: Plate, Structure and the Toolkit at 15:00 UTC, Hardware again at
  about 15:10 UTC. Re-measure line counts before pasting, and prefer the file to this table
  wherever they disagree.
- **Paste size limits.** Plate Geometry is now the largest tab at 189154 bytes, ahead of
  Mechanism at 152863 and the Toolkit at 147845. The API truncated at 154311 bytes and
  carried 125444 successfully, so Plate Geometry and Mechanism are both above the size that
  is known to have failed once. Nothing is known about where a browser paste truncates,
  which is exactly why warning two ends in a count rather than a byte figure. Check the line
  count and the last line against the table above on every paste, and check Plate Geometry
  and Mechanism twice.


---

# What the 2026-08-31 pass changed, and what to look at first

Every feature now has reference sheets in `_renders/`, one per configuration,
each carrying its own checks: a value the drawing measured against what the
feature claims. 198 sheets, 1,377 checks, none failing. Open `_renders/index.html`.
Anything that disagreed is either fixed below or stated on the sheet.

## Regenerate these first, because the geometry moved

| Feature | What changed | What you should see |
| --- | --- | --- |
| **Shooter, dual opposed** | The second wheel's inertia was missing from the shot. It is referred through the gearing as G squared. | Exit speed rises and the wheel-speed drop falls. On the shipped dual defaults, 36.4 to 47.8 ft/s and 47.9 to 31.5 per cent. |
| **Wire Path** | The bundle diameter used an asymptotic packing law that returned a circle SMALLER than the wires in it. Two 0.170 in wires needed 0.340 in and it gave 0.269. | Bundles get bigger, tie slots and clearance follow. This is the one most likely to change a route you already drew. |
| **Belt Path, chain** | A sprocket picked at its outside edge got no pitch-circle correction at all, 0.0627 in oversize on a 16 tooth #25. | Chain runs get shorter by about 1.6 links on a two-sprocket drive. |
| **Lighten, honeycomb** | Cells were drawn on the circumradius and grown back on the inradius, finishing (2 - sqrt 3) toolRad oversize with thin webs. | Webs come back to the rib you asked for. A 2.417 in claimed cell now builds at 2.417. |
| **Tube, centered pattern** | It reserved no end margin and bought an extra hole by cutting into the end of the part. | One fewer column on some lengths, end holes now on the vendor 0.5 in index. |
| **Bumper, ENVELOPE output** | Built without the cover, so the body meant to mark the outermost extent was 0.03 in undersize. | The envelope grows to the full 3.28 in. |

## Panels that now say more

Hole RESIZE says when it drove a bore SMALLER, which adds material. The sprocket
prints its root diameter and the pulley its groove root, which is what says
whether a bore breaks into the grooves. The turret prints the plate diameter you
typed. The swerve says "Bounding perimeter", because that is what the figure is,
warns when a typed pattern mostly misses the rails, warns when an MK4i stands
proud of the frame face at the inset you set, and says when a module with no
vendor data fell through to the typed pattern. Lighten reports the island count
and merged bosses, which is the diagnostic for the 16-versus-7 divergence.

## Two things left for you to decide

* **Gusset, skeleton with lighten on.** Pocket edges inset from the arm
  CENTERLINES, so a 0.5 in arm finishes 0.326 in beside one pocket and 0.15 in
  between two, and the Arm width value stops meaning anything. On the hull that
  is intended. On the skeleton the fix is to inset from the arm EDGE or to
  default lighten off, and both change what existing models build. Measured on
  `plate_gusset_skeleton`.
* **Electronics, the VH-109 radio.** Its own fastener line calls for 1/4 in
  cable ties; the dialog default cuts a 0.210 in slot, which a 0.250 in strap
  will not pass. The geometry is right for whichever tie is selected, so this is
  a question of which of the two should move.

## Two numbers that need a page nobody here has

The 3/4 in NITRA piston area is published as 0.40 sq in where the bore geometry
gives 0.4418, a 9.5 per cent gap; every other bore sits within 2.2 per cent, and
the table is internally coherent, so check the entry against the catalog rather
than recomputing it. Force scales directly with it. And the retaining ring
groove is cut at 0.460 in on a 1/2 in shaft where one source says 0.458 and
another 0.468; settle it against a Rotor Clip or Smalley drawing.
