# Render findings, ranked

Five agents transliterated every builder's geometry math into Python, computed it at the shipped
defaults, drew the result, and compared the drawing against what each feature's own report text and
doc comments claim. They produced 179 drawings and five reports. This file merges those reports into
one ranked list. Every finding below was checked against the source before it was ranked: the named
file was opened, the named function was read, and the finding was confirmed, marked unconfirmable, or
marked stale. Nothing was found stale. There are 8 findings in tier 1, 22 in tier 2, 28 in tier 3 and
21 in tier 4, which is 79 in total, because several of the roughly sixty findings in the five reports
were two defects reported as one and are separated here, and several duplicates across reports were
merged. The single most urgent one is the Wheel feature's lighten option, which builds a cutter that
removes the whole disc out to the rim rather than an annulus, so the hub web and all six bolt holes
sit inside removed material, and the report says only "Spokes : 5 at 0.2 in" while ten arms are drawn.

Four findings in tier 2 are small geometry errors rather than refusals. They are placed at the foot of
that tier and labelled, because tier 3 is reserved for cases where the geometry is right and only the
report is wrong.

The library was last modified at 09:06 today. The five reports were written between 10:23 and 10:35.
No fix landed between the reports and this file, which is why nothing is stale.

---

## Tier 1. The feature builds wrong geometry

### 1.1 Wheel, the lighten option removes the hub web and the bolt circle

File `FRC Structure Geometry.txt`, function `frcWheelBuild`, lines 622 to 651.
Two defects compound in the same block.

The cutter bar is `frcBar(center - u * (rOuter + 0.1 in), u, 2 * (rOuter + 0.1 in), spokeWidth)`.
That runs a full diameter, not a radius, so five bars at 72 degrees produce ten radial arms at
36 degrees. The report prints `Spokes : 5 at 0.2 in`.

The cutter is then `qSketchRegion(id + "l", false)`. The `false` does not filter inner loops, so the
query returns every bounded face of that sketch. Because the bars cross the inner circle, the disc
inside `rInner` is partitioned into sectors and those sectors are regions too. The cutter is
therefore the whole disc out to `rOuter = 1.537 in`, not the annulus between `rInner = 1.1855 in` and
`rOuter`. At the shipped defaults the six bolt holes and the entire hub web sit inside removed
material, and because the arms are 0.2 in wide while the hex bore reaches 0.2898 in, the arms do not
even meet each other at the centre. Nothing in the report mentions any of it.

Fix: trim the bars to the `rInner` to `rOuter` band, and change the region query to
`qSketchRegion(id + "l", true)`.

Confirmation: confirmed in the code. The reading of the `filterInnerLoops` flag is corroborated by
the library's own contrasting use at line 561, where the main wheel sketch (outer circle plus bore)
is extruded with `qSketchRegion(id + "s", true)` to get a disc with a hole. It was not verified
against a run of Onshape.

### 1.2 Swerve Chassis, the mitered corner builds the tube wall at 0.0884 in when 0.125 in was typed

File `FRC Mechanism Geometry.txt`, function `frcChassisRail`, lines 759 to 789.

`frcChassisRail` takes `n = normalize(pts[3] - pts[0])` as the inward normal and offsets the cavity
by `wall` along it. On a rectangular planform that vector is perpendicular to the long faces and the
offset is correct. On a mitered planform `pts[3] - pts[0]` is the 45 degree miter diagonal, so the
perpendicular wall comes out at `wall / sqrt(2)` = 0.0884 in and the cavity is 0.8232 in across
instead of 0.7500 in. The same line makes `across = norm(pts[3] - pts[0])` read 1.4142 in instead of
the 1.000 in rail width, which weakens the `across > 2 * wall` guard.

This fires on all four rails at the shipped defaults. The default module is SDS MK4i, whose module
data carries `cut : 0 * inch`, so `trims` is zero at every corner, so `endStation` returns the miter
case `{ endOuter : along, endInner : along - t }` for all four corners and every quad has a diagonal
from `pts[0]` to `pts[3]`. Isolating it by recomputing the same planforms with a true perpendicular
offset gives rails of 71.50 cubic inches against the 58.17 the code builds, and a chassis mass of
13.366 lb against the 12.066 lb the panel prints, so the panel is 1.300 lb, 9.7 percent, light.
`BUTT_SIDES`, `BUTT_ENDS`, `MODULE_CORNER` and any vendor rail print all give rectangular planforms
and the correct 0.125 in.

Fix: derive the inward normal from the rail's own centreline direction rather than from
`pts[3] - pts[0]`, and take `across` from the rail width parameter rather than from the same
diagonal.

Confirmation: confirmed in the code, including the shipped default path through `endStation` and the
`FRCSwerveModule.SDS_MK4I` module data at `FRC Mechanism Geometry.txt` line 627.

### 1.3 Lighten, "Single pocket (no ribs)" draws 24 ribs

File `FRC Plate Geometry.txt`, function `frcLightenOneFace`, lines 1059 to 1126.

The guard on the untouched-boss spoke pass is
`if (frcHasRibs(definition.pattern) || definition.pattern == FRCLightenPattern.NONE)`, so the pass
runs for NONE. `frcRibAngles(NONE, ...)` returns `[]` (line 52), so the `for (var a in angles)` loop
that sets `touched` never executes and every boss further than its own radius from the pocket box
edge becomes needy. In the spoke loop `var L = 2 * reach` and the `for (var ra in angles)` loop that
shortens the spoke also never executes, so `L` stays at its initialiser. On a 12 by 8 in reference
plate with eight holes that is 8 needy bosses times 3 spokes, so 24 bars, each 18.4671 in long, on a
plate 12 in across. The plate comes out criss-crossed. Meanwhile `ribCount` stays 0, so the panel
says nothing about ribs and the feature names itself "Lighten - 0 ribs". The enum label, the dialog
label and the comment at lines 549 to 551 all say a single pocket draws no bars.

Fix: drop `|| definition.pattern == FRCLightenPattern.NONE` from the guard at line 1059.

Confirmation: confirmed in the code.

### 1.4 Shaft, the retaining ring groove on a hex shaft cuts six corner scallops, so no ring can seat

File `FRC Motion Geomtery.txt`, function `frcShaftBuild`, RING branch lines 866 to 895, and function
`frcRingGroove`, lines 793 to 803.

Two defects compound, and the shipped default bore is the hex that triggers both.

`frcRingGroove` is called with `2 * reach`. On a hex that is the across-corners size, 0.577350 in for
a 1/2 in hex, not the 0.500 in shaft the ring is made for. It lands in the 0.40 to 0.80 in band and
returns depth 0.0250 in and width 0.0460 in. A 5100-series ring for a 0.500 in shaft belongs in the
0.55 in band, depth 0.0200 in and width 0.0390 in, so the cut is 5.0 thou too deep and 7.0 thou too
wide. The source's own NOTE at lines 867 to 869 describes exactly this, and the guard
`grooveInset * 2 + g.width * 2 > length` passes at 0.5920 against 6.000, so the wrong groove is cut
silently.

Independent of that, the groove is a revolved rectangle whose floor is at `reach - depth`. With the
code's depth that floor is 0.263675 in; with the corrected 0.020 in depth it is 0.268675 in. The hex
flats sit at 0.250000 in. Both floors lie outside the flats, so the revolve reaches only the six
corners. Material stands above the floor only within 11.47 degrees of each corner, so what is cut is
six scallops of 22.93 degrees, 38.2 percent of the circumference, and the other 61.8 percent is left
at full height. A retaining ring has nothing continuous to seat against. This second half is not
mentioned anywhere in the source.

Fix: call `frcRingGroove` with the round shaft size the ring is made for (across flats on a hex, not
across corners), and refuse a ring groove on a non-round profile, or cut it on a turned-down round
land.

Confirmation: both halves confirmed in the code.

### 1.5 Swerve Chassis, the SDS MK4 pattern places all 32 holes outside the frame and reports four corners drilled by print

File `FRC Mechanism Geometry.txt`, function `frcSwerveChassisBuild`, lines 1128 to 1147, with
`frcSwerveMk4Points` at line 748 and the report line at 1399.

`frcSwerveMk4Points` is right. It returns 8 holes in an L, both legs 2.75 in from the steering axis,
4 per leg at 1.000 in pitch symmetric about it, which is what the doc says. The mirror into each
corner's hand is `const p = axes[i] + vector(-cx * p0[0], -cy * p0[1])`, and the two sign flips throw
the legs outboard instead of inboard. With the default 2.500 in axis inset on a 27 in frame the L
lands at 11 + 2.75 = 13.75 in, which is 0.25 in outside the 13.5 in frame face. Every one of the 32
points fails `frcChassisInQuad`, so `drilled` stays 0.

`vendorCorners += 1` runs before the containment test, so the panel prints
`Mount holes : 0 of 32, 32 missed, 4 of 4 by print`. It claims four corners were drilled from the
vendor print while drilling nothing.

Fix: drop the two negations in the mirror so the legs fall inboard, and move the `vendorCorners`
increment behind a test that at least one hole in that corner landed.

Confirmation: confirmed in the code. Whether the SDS layout drawing itself puts the L where
`frcSwerveMk4Points` puts it could not be checked, because the drawing is not in the repository. The
sign error in the mirror is independent of that question.

### 1.6 Frame, the butt joint cuts nothing where two equal-length rails meet

File `FRC Structure Geometry.txt`, function `frcFrameBuild`, line 908.

At a corner the branch is
`through = (norm(B[m] - A[m]) >= norm(B[best] - A[best])) ? [] : [best];`.
With four equal 28 in rails each member is "the longest" from the other's point of view, so the
comparison is true for both, both get `through = []`, no butt is recorded and neither member is
trimmed. The four bodies then share a 1 by 1 by 1 in lump at each corner. The report prints
`Joints : 0 mitered, 2 butted`, which is literally true because only the cross member butts, and
`Total mass` sums `evVolume` per body, so those four lumps are weighed twice. SQUARE does the same
on purpose and adds two more overlaps where the cross member crosses the rails. Giving one rail a
different length makes the shorter end butt as intended.

Fix: break the tie deterministically, for instance by member index, so exactly one of the two equal
members is trimmed.

Confirmation: confirmed in the code. The default joint is MITER, so this needs the user to pick
BUTT; it is not the out-of-the-box state.

### 1.7 Gusset, "Bosses and arms only" is not an open frame

File `FRC Plate Geometry.txt`, function `frcGussetBuild`, lines 2010 to 2075.

Every boss circle and every arm bar goes into one sketch, `id + "s"`, and the extrude uses
`qSketchRegion(id + "s", false)`, which returns the regions the bars enclose as well as the bars
themselves. The Lighten builder states this behaviour explicitly at its own lines 932 to 934, which
is why each truss bar there gets its own sketch. Since the Delaunay arms triangulate the whole hull,
every triangle between them is extruded solid. Computed plan areas on the same six bolt picks are
2.7945 square inches for HULL and 2.8165 for SKELETON, a difference of 0.79 percent, and all of that
comes from arm width (0.5 in against 2 times `bossR` = 0.496 in). The two shapes are the same part.

Fix: give each arm bar its own sketch as the Lighten builder does, or union the bar bodies rather
than relying on one sketch's regions.

Confirmation: confirmed in the code. The behaviour of `qSketchRegion(id, false)` is taken from the
library's own comment and from the contrasting use of `true` elsewhere, not from a run of Onshape. If
that reading is wrong, both gusset shapes are open frames and this finding is void.

### 1.8 Belt Path, the "Belt Envelope" body is the whole interior of the loop

File `FRC Manufacturing Geometry.txt`, function `frcBeltPathBuild`, lines 496 to 522.

The sketch holds one closed curve made of the tangent chords and the wrap arcs.
`qSketchRegion(id + "s", false)` on that returns the region the curve bounds, so the extruded body
named "Belt Envelope" is a solid slab `width` thick filling the entire loop, overlapping every pulley
it is drawn around. FRC Belt and Chain, doing the same job in the same tab, extrudes two pitch discs
and two tangent bars of belt width and leaves the middle open. The two features disagree about what
an envelope is.

Fix: build the envelope the way FRC Belt and Chain does, or subtract the pulley discs from the slab.

Confirmation: confirmed in the code. This is the mildest item in the tier. The body is a reference
for clearance checking rather than a part anyone cuts, and it errs oversize, so if you are working
by cost rather than by tier, fix it after the tier 2 refusals.

---

## Tier 2. The feature throws or refuses at its own shipped defaults, or a preset does not fit

The last four entries in this tier are small geometry errors rather than refusals. They are here
because they are real geometry and tier 3 is for reports.

### 2.1 Swerve Chassis, the default typed pattern cannot reach the rails

File `FRC Mechanism Geometry.txt`, function `frcSwerveChassisBuild`, the else branch at line 1168,
with `frcChassisPatternPoints` and the defaults map at `FRC ToolKit.txt` line 2678.

The typed pattern is centred on the steering axis at (11, 11) on a 27 in frame, while the rails
occupy only 12.5 to 13.5 in from the centreline. Of the 6 points per corner produced by the shipped
GRID 2 across at 2 in by 3 along at 2 in, only the two at the +2 in row land on an end rail, so the
panel reads `Mount holes : 8 of 24, 16 missed, 0 of 4 by print`. This is the out-of-the-box report
for every module with no `railEnd` and no `plateDatum`, which is SDS MK4i (the shipped default), all
six WCP X2 variants, both REV modules, ThriftyBot and Custom: 10 of the 16 enum entries.

Fix: default the typed pattern to something anchored to the rail rather than to the axis, for
instance two rows at the rail centreline pitch, or drive the default pattern from `axisInset` and the
rail width so it lands on material.

Confirmation: confirmed in the code, including that SDS MK4i is the shipped default module and has
neither a `railEnd` list nor `plateDatum`. The report is honest about the miss, which is why this is
tier 2 and not tier 1.

### 2.2 Swerve Chassis, the 2.500 in axis inset puts the module past the frame face

File `FRC Mechanism Geometry.txt`, `frcSwerveModuleData` and `frcSwerveChassisBuild`. The inset is
never checked against any module envelope, and the report never mentions it.

SDS MK4i is the only module that publishes an axis-to-edge dimension, 2.625 in from both outer edges,
stated in its own `height` string at line 633. The shipped inset of 2.500 in is 0.125 in short of it,
so the default module overhangs the frame face. SDS MK4 is the second provable case: its 2.75 in
pattern legs put the axis 2.75 in from the plate edge, so it overhangs by 0.250 in, and that overhang
is exactly why finding 1.5 lands outside the frame. The other thirteen entries also overhang on the
render agent's reading, but that reading assumes the axis is central in each published square, which
no vendor states.

Fix: read the axis-to-edge figure into the module data as a number rather than leaving it in prose,
and refuse or warn when `axisInset` is less than it.

Confirmation: confirmed in the code for SDS MK4i and SDS MK4. Not confirmable for the other
thirteen, because the module data carries the envelope only as prose and the axis position is not
published.

### 2.3 Spacer, the Standoff type throws at its own shipped defaults

File `FRC Motion Geomtery.txt`, function `frcSpacerBuild`, line 979. Defaults at
`FRC ToolKit.txt` in the `frcSpacer` defaults map.

The defaults are `partLength : 0.5 * inch`, `threadDepth : 0.25 * inch`, `tapThrough : false`, and
`frcDefinition` maps `partLength` to `length`. The guard is
`if (2 * definition.threadDepth > definition.length - 0.06 * inch)`, which is 0.500 > 0.440, so it is
true. Switching Type to "Standoff (tapped ends)" and changing nothing else is a regen error reading
"The two tapped holes would meet in the middle."

Fix: default `threadDepth` to about 0.20 in, or raise `partLength` when the type is STANDOFF.

Confirmation: confirmed in the code, including the `partLength` to `length` rename in
`frcDefinition` at `FRC ToolKit.txt` line 23.

### 2.4 Turret, changing only the diametral pitch to 20 DP refuses to build

File `FRC Mechanism Geometry.txt`, function `frcTurretBuild`, lines 1865 to 1876. Defaults at
`FRC ToolKit.txt` lines 2934 to 2940.

At the shipped 140 ring teeth and 20 DP the ring root is `(140 - 2.5) / (2 * 20)` = 3.4375 in, so the
guard `2 * ringRoot <= bod + 0.5 * inch` becomes 6.875 <= 8.0 and the feature refuses. The dialog
default of 140 teeth is the WCP 10 DP number. The doc comment's own 20 DP example is AndyMark's 200
teeth on a 20 tooth pinion, which does build with a root of 9.875 in diameter. The 20 DP enum is
unusable until the tooth count is changed as well, and nothing in the dialog says so.

Fix: default `ringTeeth` from the pitch enum, or add the tooth count to the error message so the
user knows what to change.

Confirmation: confirmed in the code.

### 2.5 Pneumatic Cylinder, changing only the bore from the default throws

File `FRC Mechanism Geometry.txt`, the NITRA table at lines 2455 to 2492 and the sentinel handling at
lines 2564 and 2574.

The default mount is rear pivot and the pivot column is empty (`adderPivot : -1`) for the 1-1/4 in
and 2 in bores, so those two bores refuse with "The captured NITRA tables have no overall length for
that bore and mount" until a length adder is typed. Six of the fifteen bore and mount combinations
refuse for missing data, and one, the 1-1/2 in double end, refuses because the vendor says it does
not exist (`adderDE : -2`). The two sentinels make that distinction correctly and the two error
messages say the right thing for each. CUSTOM refuses under every mount, because the custom branch
never reaches the published-adder path.

Fix: this is a data gap rather than a logic error. Either capture the missing lengths, or have the
dialog grey out the mounts that have no captured length for the chosen bore.

Confirmation: confirmed in the code.

### 2.6 COTS Pattern, the Sport gearbox entry has two dead fields and two hidden live ones

File `FRC ToolKit.txt` precondition at lines 761 to 779, and `FRC Shop Geometry.txt`
`frcCotsPatternData` lines 642 to 663 and `frcCotsBuild` line 725.

The precondition routes `GEARBOX_SPORT` into the same branch as `CIM_FACE`, so the dialog shows
"Number of holes" and "First hole at". `frcCotsPatternData` ignores both, because Sport is in the
`motors` map with `count : 2` and the loop hard-codes a 0 degree start. At the same time "Cut the
bore as well" and "Fit" are not shown for Sport, because the `else if` excludes it, yet
`frcCotsBuild` reads `definition.cutBore` and `definition.fit` at their defaults of `true` and PRESS.
A 1.505 in bore is therefore always cut and the user has no way to turn it off or change the fit. The
entry's own note calls this "the weakest entry here" and warns that "a 1.500 in bore cut wrong is a
scrapped plate."

Fix: move `GEARBOX_SPORT` out of the `CIM_FACE` branch and into the branch that shows the bore
controls.

Confirmation: confirmed in the code.

### 2.7 Bearing Block, the "Bolt circle" preset places holes past the part edge

File `FRC Hardware Geometry.txt`, function `frcBearingBlockBuild`, lines 65 and 144 to 148. Bound at
`FRC Structure Geometry.txt` line 28, defaults at `FRC ToolKit.txt` lines 353 to 361.

With `autoSize` on, a 1.125 in bearing and a 0.375 in wall give a 1.875 in outline, radius 0.9375 in.
`FRCBlockHoles.CIRCLE` uses `definition.boltCircle`, whose defaults map value is 2 in, with 4 holes
starting at 0 degrees. The holes sit at radius 1.000 and their outer edges reach 1.098, which is
0.1605 in past the edge of the part, for both the round and the square style. `FRC_BOLTCIRCLE_BOUNDS`
declares its own default as 1.875 in, which would fit; the feature's defaults map overrides it with
2 in. Only the AM_PLATE preset fits, because its 45 degree start puts the holes at plus or minus
0.7071 with 0.132 in of edge left, which is what the doc comment claims.

Fix: change `boltCircle : 2 * inch` in the `frcBearingBlock` defaults map to 1.875 in so it agrees
with the bound, or size the outline from the bolt circle when `autoSize` is on.

Confirmation: confirmed in the code. AM_PLATE is the shipped default `holes` value, so this bites
only when the user picks CIRCLE.

### 2.8 Teardrop Hole, the default keyhole clears its own guard by 63 millionths of an inch

File `FRC Fabrication Geometry.txt`, `frcTeardropHoleBuild` NEW branch, line 1181. Defaults at
`FRC ToolKit.txt` lines 2775 to 2782.

In NEW mode `dia = 0.196 + 0.008 = 0.204 in`, so `dia / 2 - 1e-4 * meter = 0.0980630 in`, and
`slotHalf = slotWidth / 2 = 0.0980000 in`. The guard `if (slotHalf > dia / 2 - 1e-4 * meter)` passes
by 0.000063 in. The default `slotWidth` of 0.196 in is exactly the default `holeSize` of #10 clear,
and the only thing keeping the feature off its own error is the 0.008 in `printerComp` added to the
hole. Changing `holeSize` to #8 clear, or setting `printerComp` to 0, makes the default keyhole
throw.

Fix: default `slotWidth` to something well inside the bore, for instance 0.150 in, so the margin does
not depend on the print compensation.

Confirmation: confirmed in the code. The shipped `mode` is CONVERT, where the guard at line 1053 uses
the measured cylinder radius instead, so this margin is the NEW-mode case.

### 2.9 Teardrop Hole, the default keyhole is not a keyhole

Same file and function as 2.8.

The retaining shoulder is `r - slotHalf` = 0.004 in per side. The slot is 96 percent of the bore
diameter, so no screw head is captured. Someone accepting the defaults gets a 0.204 by 0.7 in stadium
slot rather than a keyhole.

Fix: the same default change as 2.8 fixes both.

Confirmation: confirmed in the code.

### 2.10 Insert Pocket, the printed defaults do not fit quarter inch stock

File `FRC Fabrication Geometry.txt`, function `frcInsertPocketBuild`, line 521.

At the shipped M3 printed defaults with `autoDepth` on, the depth comes out at 6.7 mm, and the guard
is `if (!through && depth >= stock - 0.2 * millimeter)`. The thinnest stock that passes is therefore
6.9 mm, or 0.2717 in, so 1/4 in stock fails.

Fix: either cap `autoDepth` at the available stock and print a note, or say in the dialog description
that the printed family needs more than 1/4 in.

Confirmation: confirmed in the code.

### 2.11 Sheet Layout, a part that is only too wide is dropped instead of turned

File `FRC Fabrication Geometry.txt`, function `frcShelfPack`, line 696.

The turn test is `if (allowTurn && (h > sheetH || (h > w && w <= sheetH)))`. A 30 by 3 in plate has
`h = 3`, so neither clause fires: 3 is not taller than the 47 in usable height, and 3 is not greater
than 30. It is not turned, then `w = 30 > sheetW = 23` and it is dropped with
`NOTE 1 part is too big; use a larger sheet.` Turned it is 3 by 30 and fits with 20 in of width to
spare. This is reachable in ordinary use, because `frcPlateExtents` picks its in-plane x from
whichever world axis is furthest from the plate normal rather than from which side is longer, so a
long thin plate landing wide and short is the common outcome. On a 48 by 96 sheet the same part fits
unturned, which is the tell that the drop is a packer limitation rather than a property of the part.

Fix: add `|| w > sheetW` to the turn test.

Confirmation: confirmed in the code.

### 2.12 Bearing Block, the GRID preset leaves half the library's own minimum wall

File `FRC Hardware Geometry.txt`, function `frcBearingBlockBuild`, the drop filter at line 154.

The filter is `norm(p) > bearing / 2 + holeD / 2 + 0.01 * inch`, which stops a hole breaking into the
seat but guarantees nothing more than a 0.010 in web. The GRID preset at 2 by 2 on a 1 in pitch keeps
all four holes, because 0.7071 > 0.6703, and leaves 0.0469 in between the seat and the hole, about
half this library's own `frcMinWall` of 0.090 in for CNC.

Fix: raise the constant in the filter to `frcMinWall(process, tool)`, or warn when the web falls
below it.

Confirmation: confirmed in the code.

### 2.13 COTS Pattern, two vendor bearing plates sit under the library's own minimum wall

File `FRC Shop Geometry.txt`, `frcCotsPatternData` bearing plate branch, lines 666 to 686.

BP 1.125 / 1.500 and BP 0.875 / 1.250 both leave 0.08975 in of web between the seat and the mounting
hole, which is 0.00025 in under this library's `frcMinWall(CNC, tool)` floor of 0.090 in. These are
catalogued WCP parts, so the number is presumably real and the geometry is buildable, but they are
the two tightest patterns in the set.

Fix: no geometry change. Add a note to those two entries saying not to thin the plate further or
open the holes up.

Confirmation: confirmed in the code and in the arithmetic. Whether WCP's own drawing agrees could not
be checked.

### 2.14 Wheel, the hub bolt circle guard leaves 0.0595 in of rim

File `FRC Structure Geometry.txt`, function `frcWheelBuild`, lines 594 to 597.

The guard is `if (bcDia / 2 + boltDia / 2 >= outerR) throw`, which only asks that the hole fall inside
the disc, not that any usable land be left round it. In HUB mode `outerR = hubDiameter / 2` = 1.095 in
and the default 1.875 in circle with 0.196 in holes reaches 1.0355, so the guard passes with 0.0595 in
of rim outside each hole.

Fix: require a margin, for instance `frcMinWall`, outside the hole rather than zero.

Confirmation: confirmed in the code.

### 2.15 Bumper, the ENVELOPE output silently drops the cover thickness

File `FRC Structure Geometry.txt`, function `frcBumperBuild`, lines 305 to 313.

`wantCover = definition.output == FRCBumperOutput.ALL`, and the single-band branch grows by
`backing + pad + (wantCover ? cover : 0 * inch)`. At `output = ENVELOPE` that is
`backing + pad + 0`, so the envelope stands out 3.25 in where ALL stands out 3.28 in. An envelope
that is meant to be the outermost thing on the robot is the one output that leaves the cover out.

Fix: include `cover` in the ENVELOPE grow.

Confirmation: confirmed in the code.

### 2.16 Arm Pivot, the default arm is three times its default extension limit

File `FRC Mechanism Geometry.txt`, function `frcArmPivotBuild`, lines 2216 to 2240.

At the shipped defaults `reachH = pivotSetback + L` is 36 in against an `extensionLimit` of 12 in,
and the panel prints `Reach : 36 in of your 12 in, OVER it`. The panel is honest, but this is the
out-of-the-box state.

Fix: raise the default `extensionLimit` to a figure the default arm meets, or shorten the default
arm.

Confirmation: confirmed in the code.

### 2.17 Elevator, the defaults sit one percentage point above the code's own overlap floor

File `FRC Mechanism Geometry.txt`, function `frcElevatorBuild`, lines 206 to 219 and 288.

The rule is `if (overlap < stageLen * 0.2)` giving "NOTE Overlap under a fifth of the stage; add
more.", and the dialog says a fifth is the usual floor. At the defaults the overlap is 21.05 percent,
so the note is not printed. Because the default sizing derives the stage length from the travel,
raising the total travel with the overlap held at 6 in pushes the ratio down through 20 percent, and
the note switches on above 48 in of total travel. Nothing warns that the default margin is that thin.

Fix: raise the default overlap, or print the ratio to one decimal so 21.05 does not read as 21.

Confirmation: confirmed in the code.

### 2.18 Climber, the defaults clear both of their own guards by less than an inch

File `FRC Mechanism Geometry.txt`, function `frcClimberBuild`, lines 2313 to 2316. Defaults at
`FRC ToolKit.txt`.

`travel > len - 3 * inch` is 24.5 against 25.0, so the defaults clear the travel guard by 0.5 in, and
the extended height of 77 in clears the 78 in limit by 1.0 in. Both defaults sit right on their own
limits.

Fix: no code change needed; consider a note in the dialog description that the defaults are at the
limit.

Confirmation: confirmed in the code.

### 2.19 Gear, the root of every tooth is drawn 2.8 thou proud of where the code intends

Small geometry error. File `FRC Motion Geomtery.txt`, function `frcGearOutline`, lines 64 and 100.

Two sampling loops each stop one point short of their endpoint.
`for (var i = 2; i >= 0; i -= 1)` emits the leading fillet at t = 2/3, 1/3, 0, so `P2` at t = 1 is
never emitted. `for (var i = 1; i <= 2; i += 1)` emits the root arc at 1/3 and 2/3 of its span, so
the endpoint is never emitted. The root arc's endpoint and the next tooth's `P2` are the same point,
and neither is drawn, so the polyline jumps from 2/3 of the way along the root arc straight to
`B(2/3)` of the next fillet, which sits 5.28 thou above the root circle and cuts the corner at P2 by
2.76 thou. Material is added at the root, so the clearance under a mating tooth tip is 2.8 thou less
than intended, out of a standard 12.5 thou at 20 DP. Every other loop in the outline is sampled to
its endpoints; the trailing fillet loop at line 93 correctly runs `i <= 3`.

Fix: run the root arc loop `i <= 3`, or make the leading fillet loop start at i = 3.

Confirmation: confirmed in the code. The gear still meshes; this is a geometry error, not a failure.

### 2.20 Sprocket, the lightening rim uses a root radius that ignores the roller clearance

Small geometry error. File `FRC Motion Geomtery.txt`, `frcSprocketSegments` line 579 and
`frcSprocketBuild` line 707.

The tooth form uses `R = 0.5025 * Dr + 0.0015 * inch + clearance`. The lightening pocket uses
`rRoot = PD / 2 - (0.5025 * Dr + 0.0015 * inch)`, with `definition.rollerClearance` omitted. At the
default 0.002 in clearance the lightening rim is measured from 0.573904 in while the real root is at
0.571904 in, so the rim is 2.0 thou thinner than the setting asks for. It is the same constant
written twice, and only one copy carries the clearance.

Fix: add `+ definition.rollerClearance` at line 707, or factor the root radius into one helper both
call.

Confirmation: confirmed in the code.

### 2.21 Tube, "Center the pattern" puts the end hole closer to the end than the vendor does

Small geometry error. File `FRC Plate Geometry.txt`, function `frcTubeBuild`, lines 1842 to 1847, with
`frcTubeStandardData` at 1589.

`nLen = max(1, floor((L - pitchL) / pitchL) + 1)` is 32 on a 16 in tube, spanning 15.5 in, so
`x0 = (16 - 15.5) / 2` = 0.25 in from the end. That is half the 0.5 in the same feature uses when
indexing, which comes from `std.start = 0.500 * inch` for every standard in the table, and half what
the vendor drawings the comment cites use.

Fix: centre on a span that leaves at least `start` at each end, for instance
`nLen = max(1, floor((L - 2 * startL) / pitchL) + 1)` with the centred `x0`.

Confirmation: confirmed in the code.

### 2.22 Electronics, the tie slots run under the component they tie down

Small geometry error. File `FRC Electrical Geometry.txt`, `frcElectronicsBuild` line 419 to 423 and
`frcTieSlotPoints` line 299.

`reach` is `d.size[1] / 2 + 0.10 * inch`, which puts the slot centre 0.10 in outside the footprint,
but the slot is `tieW * 2.2` long along the same axis, so half of it extends inboard. The inner edge
sits inside the footprint by `slotL / 2 - 0.10 in`: 0.032 in with a 6 in tie, 0.076 with a 10 in,
0.131 in with the default 14 in tie (`FRCTieSize.TIE_190`, 0.190 in wide), and 0.252 with a heavy
duty one. The part sits on top of the inner end of both its own slots.

Fix: set `reach` to `d.size[1] / 2 + 0.10 * inch + slotL / 2` so the whole slot clears the footprint.

Confirmation: confirmed in the code, including the default tie width in `frcTieWidth` at
`FRC Core.txt` line 219.

---

## Tier 3. The geometry is right but the feature reports something false about it

### 3.1 Wire Path judges clearance against a hexagon inscribed in a round pocket

File `FRC Electrical Geometry.txt`, `frcWirePathBuild` lines 986 and 1059, with `frcFaceSegments2d` at
line 515.

`frcFaceSegments2d` samples each edge at `perEdge + 1` points and chords between them, and it is
called with `perEdge = 6`, so a full circular edge becomes six chords. `frcPointInside` therefore
reports solid material up to `r (1 - cos 30 deg)` = 0.134 r inside the real pocket, which is 0.067 in
on a 0.5 in radius pocket and 0.2546 in on the 1.9 in pocket drawn. Both the route search and the
`frcPathClear` verification use the same segment list, so an unsafe route passes its own check. This
is the most dangerous item in this tier, because the report says the route is clear when it is not.

Fix: raise `perEdge` for circular edges, or inset the segment list by the sagitta
`r (1 - cos(180 / perEdge))` before testing.

Confirmation: confirmed in the code. The magnitude depends on whether Onshape represents a full
circle as one closed edge or two half-circle edges; if it is two, the count doubles and the error
halves. The direction of the error is the same either way.

### 3.2 Swerve Chassis, THROUGH_FACE counts every point as drilled without testing containment

File `FRC Mechanism Geometry.txt`, `frcSwerveChassisBuild` lines 1150 to 1167.

The branch does `wanted += size(pts); drilled += size(pts);` with no `frcChassisInQuad` test, while
both down-through branches do test containment. The panel therefore always reads `24 of 24` whatever
the pattern, so the line cannot fail even when the face pattern missed entirely.

Fix: apply the same containment test the other two branches use.

Confirmation: confirmed in the code.

### 3.3 Slot, the report is wrong twice for square ends

File `FRC Structure Geometry.txt`, `frcSlotSegments` lines 59 to 82 and `frcSlotBuild` lines 183 and
190.

`frcSlotSegments` returns only pA, pB, pC, pD for SQUARE, and those four points sit at plus or minus
`travel / 2`, so a square slot is 1 in end to end at the defaults, not 1.196 in. Line 183 prints
`Overall : 1.196 in end to end` regardless of the ends setting. It is wrong twice over, because a
0.196 in bolt in a 1 in square slot slides only 0.804 in, so line 190's
`Travel is bolt movement, not cut length.` is also wrong for square ends. Both lines are correct for
the rounded default.

Fix: branch both lines on `definition.ends`.

Confirmation: confirmed in the code.

### 3.4 Dogbone Corners, the reported overcut constant is the ninety degree value printed for every angle

File `FRC Manufacturing Geometry.txt`, `frcDogboneBuild` line 802, and the same constant again in
`FRC Fabrication Geometry.txt` Finger Joint report line 348.

The report prints `Overcut per wall : r * 0.2929` unconditionally. The true overcut is
`r (1 - sin(theta / 2))` for a pocket interior angle theta: 0.0366 in at 90 degrees, 0.0625 at 60
(understated 1.71 times), 0.0167 at 120 (overstated 2.19 times), 0.0095 at 135 (overstated 3.85
times). The feature finds every concave vertical edge whatever its angle, because the only guard is
`if (walls < 2 || norm(away) < 0.05) continue;` at line 764, which for a two-wall corner excludes
only corners sharper than 2.87 degrees. Non-ninety-degree corners are routinely cut and mis-reported,
and understating the overcut on a sharp corner is the dangerous direction.

Fix: compute the overcut per corner from `norm(away)`, which is `2 sin(theta / 2)`, and report a
range or a maximum rather than one number.

Confirmation: confirmed in both files.

### 3.5 Shooter, the closing line is wrong for one of the two arrangements

File `FRC Mechanism Geometry.txt`, `frcShooterBuild` lines 1690 and 1778.

The panel always ends with `Exit tops out at half the surface speed.` For the hooded case that is
right, 26.41 against 34.91 ft/s. For two opposed wheels `perRad = sum / 2`, which at the default 1x
speed ratio is the full wheel radius, so the ceiling is the whole surface speed, and the computed
exit of 36.37 ft/s already exceeds the stated half-ceiling of 34.91. The doc comment above the
function gets this right; the printed footer does not, and it is printed unconditionally.

Fix: branch the footer on `dual`.

Confirmation: confirmed in the code.

### 3.6 COTS Pattern, the 550 motor face cuts two holes where the same library's vendor-cited data says four

File `FRC Shop Geometry.txt`, `frcCotsPatternData` lines 591 to 600, against
`FRC Electrical Geometry.txt` `FRCComponent.NEO_550` at lines 258 to 270.

`MOTOR_550` carries `count : 2` and a note reading "Nothing else here carries a 550 face, so the
25 mm circle and the 13 mm boss rest on that one source." `FRCComponent.NEO_550` does carry a 550
face, cited to REV-21-1651-DR and REV-21-1651-DS, and it agrees exactly on circle (25.0 mm both),
hole (M3 clear both) and boss (the COTS 13 mm plus the library's 0.005 in clearance is 0.5168 in
against the Electronics pilot of 0.517 in). What does not agree is the count: REV-21-1651-DS states
four M3, `NEO_550` cuts four, `MOTOR_550` cuts two. The note's own warning is that "a count is the
last thing to take on one source."

Fix: change `count : 2` to 4, and rewrite the note to say the entry is corroborated by the NEO 550
entry in FRC Electrical Geometry rather than single source.

Confirmation: confirmed in both files.

### 3.7 Bumper, the 110 in default lets an over-bumper footprint six inches past the rule pass as "yes"

File `FRC Structure Geometry.txt`, `FRC_ROBOT_PERIM_MAX` at line 226 and the report at lines 432 to
437.

The check runs against the bare frame outline. With the shipped 3.25 in stand-out on the 28 by 28 in
octagon drawn, the bare outline is 104.9706 in and the footprint over the bumpers is 126.5097 in,
6.51 in past the 120 in R104 figure, and the feature still prints
`R104 bare frame outline at most 110 in : yes`. A frame sitting exactly on the 110 in default would
measure 131.5 in over the bumpers on that octagon, or 136 in on a plain rectangle. To keep R104 on
that outline the bare limit would have to be about 98.46 in. The code does hand the real check to FRC
Inspection and says so on the next two lines, so this is a default-value problem rather than a wrong
calculation, but a team reading "yes" will be 16 in illegal.

Fix: default `perimeterLimit` to a bare figure that keeps R104 given the stand-out, or compute the
over-bumper perimeter from the grown band the feature already builds and check that instead.

Confirmation: confirmed in the code. All four other rule lines agree with the drawing.

### 3.8 Lighten, honeycomb and circles report every cell generated, on the part or not

File `FRC Plate Geometry.txt`, `frcLightenOneFace` line 969.

`detail` is `size(cellPolys) + size(cellCircles)`, and `frcIslandCenters` lays cells over a square of
half-diagonal `reach` centred on the pocket box. On a 12 by 8 in reference plate that is 121 cells,
of which 13 land on the plate, and the panel says "121 cells". This is the same defect the rib branch
was fixed for; the comment at lines 979 to 983 explains that the outer lattice bars miss the part
altogether and were being counted anyway, but the fix was never applied to the cell branch.

Fix: filter the cell centres against the pocket box the way the rib branch filters bars with
`vHalf`, and count only the cells that survive.

Confirmation: confirmed in the code.

### 3.9 Belt Path, the "idler" label depends on the order the circles were picked

File `FRC Manufacturing Geometry.txt`, `frcBeltLoop` lines 362 to 378, report at line 556.

`orient` comes from the signed area of the centre polygon, and every `sides[i]` is derived from
`turn * orient`. Picking the same pulleys in the reverse order flips the polygon's orientation and
therefore every sign. On the three-pulley case the length, wraps, tangents and turn magnitude are
identical either way, but one pick order gives no idler labels and the other labels all three
", idler". A team reading "idler" against a driven pulley will mis-plan the drive.

Fix: decide the side from the actual convexity of the hull rather than from the polygon orientation,
or normalise `orient` to +1 by reversing the input when the area is negative.

Confirmation: confirmed in the code.

### 3.10 Belt Path, teeth in mesh are reported for idlers too

Same file, report lines 557 to 563.

`mesh = 2 PI r (w / 360) / pitch` is printed for every pulley, idlers included, with a ", low" warning
under 6. An idler runs on the back of a timing belt and has no teeth engaged at all, so neither the
figure nor the warning applies to it. In the four-pulley render the idler is reported as
"2.1 teeth, low".

Fix: suppress the mesh figure and the warning when `loop.sides[i] > 0`.

Confirmation: confirmed in the code.

### 3.11 Tube reports the small cross dimension as "the section"

File `FRC Plate Geometry.txt`, `frcTubeBuild` lines 1674 to 1677 and 1918.

Both `secMin` and `secMax` are set from `crossMin`. `crossMax` is computed and never used. A 2 by 1
tube therefore reports `1 in section` and never mentions the 2 in dimension, while the part name set
on the same body is the correct `Tube 2x1x0.0625 - 16 in`. Worse, a batch containing a 2 by 1 and a
1 by 1 reports `1 in section` as if they agreed, because "mixed sections" can only fire when the
small dimensions differ.

Fix: report the section as `crossMax by crossMin`, and track both for the mixed test.

Confirmation: confirmed in the code.

### 3.12 Tube, "Holes punched" is half the holes in the part

Same file, `frcTubeBuild` lines 1853 to 1861, 1902 and 1924.

`cnt += nLen` accumulates once per face pair, and each cut is extruded `dims[0] + dims[1] + dims[2]`
deep, so it goes through both walls of the pair. The 2 by 1 by 16 in tube at defaults reports
`Holes punched : 128` and physically has 256 holes. The closing line "Holes go through both walls,
the way punched tube is made." is the only hint. The number is a cut count labelled as holes.

Fix: double the count, or relabel the line as cuts.

Confirmation: confirmed in the code.

### 3.13 Arm Pivot, the reported reach ignores the arm angle

File `FRC Mechanism Geometry.txt`, `frcArmPivotBuild` lines 2212 and 2216.

`reachH = definition.pivotSetback + L` ignores `armAngle`, while `atPose = nmH * cos(armAngle)`
applies it. At the 45 degree case the drawn tip is 21.2132 in ahead of the pivot, 27.21 in past the
frame reference, but the panel still reports 36 in, and the reach dimension in the render runs past
the drawn arm.

Fix: use `pivotSetback + L * cos(armAngle)`, or label the line as the reach at full extension.

Confirmation: confirmed in the code.

### 3.14 Roller, the mass line weighs the compliant wheels at the picked material density

File `FRC Mechanism Geometry.txt`, `frcRollerBuild` lines 447 and 499.

The mass line is `frcFormatMass(vol * frcDensity(definition.material))` over every body, tube and
wheels, but the wheels were given the named material "Compliant wheel" at 1200 kg/m3 by
`frcApplyNamed`. At the default material, polycarbonate, also 1200, the two agree by coincidence.
Pick 6061 and the panel reports the compliant wheels as aluminium while the parts list calls them
compliant wheels. The panel's own qualifier, ", wheels solid", describes the annulus modelling, not
this.

Fix: accumulate the mass per body with each body's own density.

Confirmation: confirmed in the code.

### 3.15 Lighten, small pockets are silently left solid and the panel never says so

File `FRC Plate Geometry.txt`, `frcDropSlivers` at line 215 and its call at line 1268.

`frcDropSlivers` deletes any cutter body whose plan area is below
`minArea = (2 * rib)^2` = 0.25 square inches at the defaults, so that region stays solid. Its return
value is the count deleted, and the call at line 1268 discards it. On one test plate a genuine pocket
of 0.144 square inches was deleted, on another two were. Nothing in the report mentions it, and the
feature's rib count still includes the ribs that bound the pocket that never got cut.

Fix: capture the return value and print it, for instance "2 small pockets left solid".

Confirmation: confirmed in the code.

### 3.16 Lighten, the truss report prints a "pocket capped" note without ever printing the pocket

File `FRC Plate Geometry.txt`, `frcLightenOneFace` lines 538 to 542, 1346 and 1351.

Line 1347 suppresses the `", pocket ..."` clause for TRUSS, but the `note` computed at 538 to 542 is
still appended at 1351, so a truss on a plate that caps its pocket reports
`28 ribs, wall 0.25 in, rib 0.25 in / NOTE Pocket capped by part size`, a note about a number the
same line refuses to show. `pocketUsed` is a real input to the truss, since it sets the station step
and the minimum spanning chord length, so it is worth printing.

Fix: print the pocket for TRUSS as well, or suppress the note when the pocket is not printed.

Confirmation: confirmed in the code.

### 3.17 Gearbox, the report says "even only" but the first stage pinion steps by one

File `FRC Structure Geometry.txt`, `frcRatioSearch` lines 1234, 1238 and 1265, report at 1337 to 1339.

`const step = evenOnly ? 2 : 1;` is applied to every gear loop and to the second stage pinion loop,
but both first stage pinion loops are `for (var p = pMin; p <= pMax; p += 1)`. Odd motor pinions are
in the search whatever the box says, and the single stage table shows 11:74, 9:60 and 9:62 returned
under "even only". It is defensible as a deliberate choice, since WCP does sell 9 and 11 tooth motor
pinions, but the report line does not say so.

Fix: say so in the report line, for instance "pinion 8-16 all, gear 18-84 even".

Confirmation: confirmed in the code.

### 3.18 Belt and Chain, the chain branch says "Nearest" but always rounds up

File `FRC Manufacturing Geometry.txt`, `frcDriveBuild` lines 190 to 195 and 282.

`counted = ceil(exactTeeth)`, then plus one if odd. That is next-even-up, never nearest. On #25 chain,
16 and 16 teeth at 5.000 in centres, the exact requirement is 56.1033 links and the report says
`Nearest : 58 chain links`, which pushes the centres from 5.000 to 5.2371 in. Rounding up is the
right behaviour, because a short chain cannot be fitted, but "Nearest" is the wrong word for it, and
the belt branch says "Stock size" for the same operation.

Fix: change the chain label to "Next even up" or "Stock size".

Confirmation: confirmed in the code.

### 3.19 Shooter, the inertia is taken from the driven set only while the doc claims it covers what is drawn

File `FRC Mechanism Geometry.txt`, `frcShooterBuild`.

`mw` and `iw` come from the driven wheels only. In the dual case the opposing wheels are built, and
in the single case the hood is built, and neither appears in any number. The doc says the inertia is
"the inertia of the wheels this feature draws", which over-claims for the dual case.

Fix: include the opposing set in `mw` and `iw` when `dual`, or narrow the doc wording.

Confirmation: confirmed in the code.

### 3.20 Sprocket, the root diameter is drawn but never reported

File `FRC Motion Geomtery.txt`, `frcSprocketBuild` report lines 751 to 753.

The report prints pitch, outside and clearance diameters. The root diameter, 1.143808 in at the
defaults, is what a team needs to check chain clearance against a hub or a bearing, and it is not
printed.

Fix: add a root diameter line.

Confirmation: confirmed in the code.

### 3.21 Pulley, the groove root is reported only for a round cord

File `FRC Motion Geomtery.txt`, `frcPulleyBuild` line 493.

The `Groove root` line sits inside the `if (isCord)` branch. A toothed pulley reports pitch and
outside diameter and no root, even though the root, 1.295047 in at the defaults, is the number that
decides whether a bore or a lightening pocket will break through.

Fix: print `OD - 2 * bd.depth` for the toothed branch as well.

Confirmation: confirmed in the code.

### 3.22 Turret, CUSTOM is identical to XCONTACT at the dialog defaults, and the plate diameter goes unreported

File `FRC Mechanism Geometry.txt`, `frcTurretBuild` lines 1844 to 1861 and the report at 2007 onward.

The X-contact ladder from a 7 in bore gives `bod = bid + 0.5 in` = 7.5 and `bw = 0.25 in`, which are
exactly the `bearingOuter` and `bearingWidth` defaults, so picking CUSTOM and changing nothing gives
identical geometry and only a different `Bearing :` string. Separately, with `makeRing` off the plate
outside diameter never appears in the panel, so the one number the user typed for that mode is not
reported back.

Fix: report the plate outside diameter whenever `makeRing` is off.

Confirmation: confirmed in the code.

### 3.23 Climber, the vendor kit toggle changes nothing at the defaults

File `FRC Mechanism Geometry.txt`, `frcClimberBuild` lines 2305 to 2312.

The kit branch substitutes `baseSize = 2.0 in`, `step = 0.5 in`, `wall = 0.0625 in`, which are
exactly the typed defaults, so turning the kit off produces identical geometry and identical numbers.
Only the words "kit tubes" against "tubes" and the `n > 2` guard differ.

Fix: no code change needed; consider different typed defaults so the toggle is visible.

Confirmation: confirmed in the code.

### 3.24 Hole, "Resize existing holes" quietly adds material and the report does not distinguish it

File `FRC Plate Geometry.txt`, `frcHoleBuild` lines 1470 to 1485.

`opOffsetFace(-delta)` with `delta = finalDia / 2 - r` grows a hole when the target is larger and
fills one in when the existing bore is larger, because `delta` is then negative and the wall moves
inward. A 1.375 in bore picked with the default bearing setting is driven down to 1.124 in, so the
feature adds 0.1255 in of material on the radius. The report says only `Applied to : 6 holes`, with
nothing distinguishing a hole that grew from one that shrank.

Fix: count the two directions separately and print both.

Confirmation: confirmed in the code. The behaviour itself is documented in the comment at line 1474
and is not a bug; the silence in the report is the finding.

### 3.25 Swerve Chassis, the printed perimeter is the bounding rectangle and the panel does not say which it is

File `FRC Mechanism Geometry.txt`, `frcSwerveChassisBuild` report line 1393.

`perimeter = 2 * (w + l)` is the bounding rectangle, which is what the FRC rule measures, and the
drawn frame outline matches it on an uncut chassis. On a corner-cut chassis the drawn rails do not
form that rectangle: for SDS MK4c the four rails are 18.5 in each, 74 in of drawn outer edge, with
four 5.25 in open corners. The printed 108 in and the drawn 74 in are 34 in apart and the panel does
not say which it is.

Fix: label the line as the bounding perimeter.

Confirmation: confirmed in the code. Not wrong, only unlabelled.

### 3.26 Swerve Chassis, THROUGH_TOP and MODULE without vendor data are indistinguishable in the output

File `FRC Mechanism Geometry.txt`, `frcSwerveChassisBuild` line 1168.

Both fall to the same typed-pattern branch and produce identical geometry and identical report text
including `0 of 4 by print`. That is what the doc intends, but nothing in the output tells the user
which enum entry produced it.

Fix: name the mode in the report line.

Confirmation: confirmed in the code.

### 3.27 Finger Joint, the cutter warning never fires at the shipped defaults

File `FRC Fabrication Geometry.txt`, `frcFingerJointBuild` line 332.

The note is gated on `if (r > 0 * inch && definition.toolDiameter > tTab)`. At the shipped defaults
the relief is NONE so `r` is zero, and the 0.25 in cutter in 0.25 in stock is exactly at the limit
rather than over it, so the note fails both tests. A user picking the two defaults together gets no
warning that the cutter is the full slot width.

Fix: use `>=` and drop the `r > 0` requirement, since a full-width slot is worth flagging with any
relief setting.

Confirmation: confirmed in the code.

### 3.28 Electronics, the CANdle holes are exactly tangent to the envelope

File `FRC Electrical Geometry.txt`, `frcComponentData` CANDLE entry at line 179.

Holes at plus and minus 1.250 in with a 0.200 in diameter reach 1.350, and the envelope half-length is
1.350. There is zero material outboard. That is consistent with the entry's own fastener note ("10-32
through the two open slots"), because open-ended slots are what the part has, but the feature cuts
closed 0.200 in circles, so the modelled result is a hole that just breaks the end of the part if the
plate is trimmed to the envelope.

Fix: cut open slots rather than circles for this entry, or note the tangency in the report.

Confirmation: confirmed in the code.

---

## Tier 4. Cosmetic and house rule

The house rule under test is ten lines per report panel, each at most sixty characters.

### 4.1 Weight Budget exceeds its own ten line budget on the likely path

File `FRC Hardware Geometry.txt`, `frcWeightBudgetBuild`. Title plus two limit lines plus the counts
heading plus `topN` rows plus the closing is exactly 10 at the shipped `topN : 5`. Every optional line
pushes past it: printed adds one, the printFailed NOTE one, the fallback NOTE one, the print caveat
one, giving 14 in the worst case. The most likely real path is worse than the ordinary case, because
`frcGroupList` always emits group 1 even when its query is empty, so a user who leaves Group 1 parts
empty and sets only the ungrouped material gets `fallback > 0` and the NOTE line, which is 11 lines.
`FRC_TOPN_BOUNDS` allows `topN` up to 60, which would give 69 lines.

### 4.2 Parts is not compressed at all

File `FRC Shop Geometry.txt`, `frcPartsBuild` lines 111 to 127. Twelve lines for six parts, with a
widest line of 101 characters under stock naming and 77 under the shipped default naming. No budget
is stated for this feature anywhere in the code, but it sits beside three panels that were compressed
hard to sixty. The row is label plus long by wide by thick plus stock plus `frcFormatMass`, and
`frcFormatMass` alone costs 22 characters where the weight panels dropped it for exactly that reason.
At the 40 row cap the panel is 47 lines.

### 4.3 Design Constants is twelve lines

File `FRC Shop Geometry.txt`, `frcConstantsBuild` lines 438 to 461. Nine variables plus a title plus a
two line closing. Again no budget is stated, but it exceeds the one the three weight panels hold.

### 4.4 The Inspection R104 line reaches sixty one characters

File `FRC Hardware Geometry.txt`, `frcInspectionBuild` lines 1073 to 1080. The code comment
anticipates this and shortens "frame perimeter" to "R104 perimeter" to buy three characters. That is
not enough: a 33.1875 by 31.9375 in frame against a 119.9375 in limit produces
`  R104 perimeter 130.25 in of 119.9375 in, OVER by 10.3125 in` at 61 characters. The fixed part of
the line is 31 characters, so any combination of perimeter, limit and overrun strings totalling more
than 29 characters overruns, and `frcInches` emits up to 11 characters per value.

### 4.5 `frcFit(what, 18)` truncates the ", printed" marker off most materials

File `FRC Hardware Geometry.txt`, `frcFit` at line 323 and its use at line 624. `frcFit` cuts to 17
characters and appends a space, so "PLA, printed" and "PETG, printed" survive but
"Onyx nylon, printed" becomes "Onyx nylon, print", "6061 aluminum, printed" becomes
"6061 aluminum, pr", and "Prusament PLA Galaxy Black, printed" becomes "Prusament PLA Gal". Any part
carrying its own material name longer than eight characters loses the one marker that says the row
was weighed as a print.

### 4.6 Weight Budget prints two number formats for the same quantity three lines apart

File `FRC Hardware Geometry.txt`, `frcWeightBudgetBuild` closing lines 631 to 632. The closing prints
the literals `R103 115.0 lb, R408 135.0 lb` and then `I102 150 lb` from
`frcLb(FRC_INSPECTION_LIMIT)`, because `frcLb` drops the trailing zero, while the same panel's limit
lines print `of 115 lb` and `of 135 lb`.

### 4.7 Bolt Pattern prints 0.500 in and 0.5 in in the same panel

File `FRC Shop Geometry.txt`, `frcPatternBuild`. The closing literal reads
`FRC tube vendors drill 0.500 in grids` while the Spacing line above it prints `frcInches(0.5 in)`,
which is `0.5 in`.

### 4.8 Lighten, the report line for "Single pocket" starts with a stray comma

File `FRC Plate Geometry.txt`, `frcLightenOneFace` lines 547 and 1346. `detail` is initialised to `""`
and is only assigned in the TRUSS, HONEYCOMB/CIRCLES and `frcHasRibs` branches, so for NONE it stays
empty and line 1346 builds `", wall 0.25 in, rib 0.25 in, pocket 2.4167 in"`.

### 4.9 Lighten, the enum doc comment "so every pocket reaches a wall" is not true of the geometry

File `FRC Plate Geometry.txt` line 16, repeated in the dialog description for Pattern. Counted on the
finished rasters, most pockets are interior triangles bounded only by ribs and boss islands: 16 of 28
landlocked on the reference plate, 21 of 35, 18 of 30 and 20 of 30 on the three other cases. The
geometry is right, because an interior triangle is exactly what a truss should produce, so this is a
wording defect, but the sentence a user reads in the dialog is false.

### 4.10 Teardrop Hole, the FLAT doc claim that the hole stays inside its own circle is false

File `FRC Fabrication Geometry.txt` lines 908 to 912. Only the height is capped at the bore top. The
roof corners at plus and minus `half`, `r` sit at `sqrt(half^2 + r^2)` from the centre, which is
1.0824 r at the default 45 degrees, 8.2 percent outside the bore, rising to 1.2605 r at the 15 degree
bound. A FLAT hole close to an outside face still breaks out, just less than a point would. The
comment should say it stays within the height of the bore, not inside its circle.

### 4.11 `FRC_OVERHANG_BOUNDS` comment gives 15 degrees where the crossover is 19.47

File `FRC Fabrication Geometry.txt` lines 877 to 880. The comment says "Below about 15 degrees the
point on a teardrop grows taller than the hole is wide, which is where the range stops." The point
height above the bore top is `r (1 / sin over - 1)`, which equals the hole width `2 r` at
`sin over = 1/3`, that is 19.47 degrees. At the 15 degree bound the point is already 2.864 r, 1.43
times the hole width.

### 4.12 Teardrop Hole, the keyhole "Bridge span" line describes a flat bridge over an arched roof

File `FRC Fabrication Geometry.txt` line 1250. `Bridge span : 0.196 in at the slot roof` is a flat
bridge figure, but the roof drawn is a semicircular arch of radius 0.098 in, which has the same
zero-support problem at its crown that a round hole does. The code does say "A keyhole is a slide
fit, not a bridging shape", so this is wording, not geometry.

### 4.13 Gearbox, the doc comment claims tangent pitch circles that the default allowance separates

File `FRC Structure Geometry.txt` lines 1404 to 1405. The comment says "the operating pitch circles,
which come out tangent because that is what a center distance is." At the shipped defaults stage 1
draws radii 0.3 plus 1.5 = 1.8 in against centres of 1.802 in, so the circles are drawn 0.002 in
apart, and the same on stage 2. They are tangent only with `allowance` set to zero, and the default is
0.002 in.

### 4.14 Gear, "True involute flanks with a root fillet, not arcs" describes points, not what is built

File `FRC Motion Geomtery.txt` line 246. `skPolyline` is used, so the flank is 14 straight chords
through points that lie exactly on the involute, and the tip and root arcs are three-chord
approximations. Maximum deviation of the drawn polyline from the true involute is 0.07 thou, which is
small, but the report's wording implies a curve. One word, "sampled", would fix it, or a spline.

### 4.15 Arm Pivot and Climber print a nominal wall thickness through the signed allowance formatter

File `FRC Mechanism Geometry.txt` lines 2221 and 2386. `frcThou` at `FRC Core.txt` line 627 prepends
"+" for any non-negative value, so a nominal 0.0625 in wall prints as `Wall : +62.5 thou`, which
reads as a tolerance.

### 4.16 Sheet Layout, the group key with byThickness off is the literal string "all"

File `FRC Fabrication Geometry.txt` line 760. The report row then reads `all in : 9 parts on 3
sheets`, which reads oddly next to `0.125 in : ...`.

### 4.17 Frame, the stock name zero pad covers one decade only

File `FRC Structure Geometry.txt` line 1128. `((cutLen < 10) ? "0" : "")` makes 9.5 in sort as
`09.5 in` correctly ahead of 26 in, but a member of 100 in or more would sort ahead of 26 in again.
Not reachable on an FRC frame.

### 4.18 `FRC_PERIMETER_BOUNDS` declares a stale default

`FRC Mechanism Geometry.txt` line 510 declares 110 in. `frcInspection`'s defaults map at
`FRC ToolKit.txt` line 1610 sets 120 in, which is the 2026 R104 number and is what wins. Harmless,
but the two disagree.

### 4.19 Lighten, the four phase honeycomb search is dead code

File `FRC Plate Geometry.txt` lines 954 to 960, with `frcIslandCenters` at line 190. The loop tries
phases (0,0), (0.5,0), (0.25,0.5) and (0.5,0.5) and keeps the candidate set with the most centres, but
`frcIslandCenters` returns `(2 * nRow + 1) * (2 * nCol + 1)` points for every phase, because `phase`
only shifts positions and never changes the count. `size(cand) > size(bestCenters)` is therefore true
only on the first iteration and phase (0,0) always wins. All four sets have 121 entries on the
reference plate.

### 4.20 Finger Joint, the T-bone doc comment says "the v edge" where there are two

File `FRC Fabrication Geometry.txt` lines 148 to 152. Circles are placed at `cv = v0` and at
`cv = v1`, so the over-cut leaves through both and the slot ends up 0.5 in across instead of 0.25 in
at the defaults. That is the trade the comment calls "deepens the slot"; it is just twice as much of
it as the singular reads.

### 4.21 Electronics, the SystemCore ear margin is 1.5 mm

File `FRC Electrical Geometry.txt` lines 94 to 100. Holes of 4.50 mm at plus and minus 64.00 and
32.00 mm in a 135.50 by 71.50 mm envelope leave 1.5 mm, 0.059 in, of ear outboard of the hole on both
axes, the tightest hole-to-edge in the component table. Consistent with "corner ears", and the
entry's own note already says to check against production hardware, but the margin is worth knowing.

---

## What the drawings confirmed is correct

These were verified to machine precision or against the vendor data the library cites, so they need
no attention.

- **The gear involute.** Against the analytic involute of the base circle with a single start angle,
  the maximum residual over the 15 flank points is 1.1e-16 in. It is the involute exactly. A least
  squares circle through the same points needs R = 0.15573 in and still misses them by 0.33 thou, so
  it is demonstrably not an arc. Pitch and outside diameters match the report to 0.0e+00. A full
  segment-intersection test over the 720 point closed polyline finds no self intersections, and
  adjacent teeth leave 2.464 degrees of clear root arc. Mesh centre distance is exact for 18 plus 30
  and 18 plus 18.

- **The sprocket seating curve constant, 0.5025.** This was the disputed number and it is confirmed
  from the drawn geometry rather than the algebra. The end of the seating curve and the start of the
  working flank land on the same point, separation 1.4e-17 in, and the identity `E - R - ac` evaluates
  to exactly zero, so there is no radial step. The reviewer's proposed 0.50025 opens a step of
  0.0002925 in, which is exactly the 0.00225 Dr the source comment predicts, so the comment's own
  figure is right too. The result is invariant at 0.000, 0.002 and 0.008 in of roller clearance,
  because R and E each gain the clearance and F loses it. Every other junction closes to machine zero,
  and the closure at z is exact for every tooth count because `delta = A - B - gamma` holds
  identically with the code's coefficients.

- **The belt tooth rounding.** `frcStockableBeltTeeth(74.8)` returns 75, which is the smallest
  multiple of five at or above the exact requirement. Boundaries check out: 0 gives 5, -1 gives 5,
  75.0 gives 75 (at, not above), 75.0001 gives 80, 143 gives 145. `frcSolveCenter` then returns a
  centre distance consistent with that tooth count to a residual of 1.8e-15 in, and 3.6e-15 in on the
  60 to 12 reduction. The doc comment's own claim about swapping big and small in `frcWrapLength`
  (1.8 in, nine teeth of HTD 5 mm) is confirmed at 1.83765 in and 9.34 teeth.

- **The three Lighten fixes made today.** The wall anchor stations: a 12 in square plate now gives
  exactly 16 stations, four per side, exactly as the comment at lines 566 to 570 predicts, against 4
  for the pocket-only step it replaced, and the `+ 1e-9` epsilon at line 131 is load bearing because
  11.25 divided by 2.8125 is exactly 4 and would otherwise floor to 3 on the meter-valued division.
  The rib anchoring: 0 of 56, 72, 58 and 62 rib ends across four test plates terminate in open pocket,
  and every wall end buries itself exactly `wall + rib` = 0.5 in measured perpendicular to the wall at
  every arrival angle, which is what the `grow / sin(arrival)` in `frcWallExtension` is for; the
  `extCap = 3.0` cap dropped nothing on those plates. The rib count: computed, printed and feature
  name agree on all seven patterns, and the `vHalf` band filter matches a raster count of the bars
  that actually cross the pocket, 13 of 33 for isogrid, 8 of 22 for grid, 10 of 22 for diagonal.

- **The swerve hole stations against the vendor table.** SDS MK4c and MK4n at 0.250, 1.250, 2.250 in
  and SDS MK5i and MK5n at 0.250, 1.750 in were recovered exactly off the drawn hole centres, at both
  rail ends and all four corners. The rail cut length comes out 27 minus 2 times 4.250 = 18.5 in,
  which is the `pattern` string's own claim of drive base minus 8.500 in. Hole counts per corner are
  6 and 4, matching the `screws` strings. Mixed modules produce one report row per distinct module,
  each naming its own corners and leading with its own fastener line, and the `frcOneLine(.., 44)`
  clip preserves the fastener count and size.

- **Belt Path's loop solver.** The drawn perimeter, taken off the sketch entities the feature creates,
  matches `frcBeltLoop` to 0.0e+00 in. Every tangent is perpendicular to both radii it touches, with a
  maximum dot product of 6.7e-16; every arc end meets its tangent end to 0.0e+00 in; the total signed
  turn is exactly 360 degrees. The three-equal-pulley identity and the two-pulley closed form both
  match to 0.0e+00 in. The doc's claim of five decimals is understated.

- **The rack length fix.** `od` is now read back off the drawn points as `xHi - xLo`, giving
  2.781221 in, which is what the report prints. The doc comment's formula
  `PI / (2 DP) - 2.5 tan(PA) / DP` agrees to 3e-16, and its rule of thumb of about 0.9 / DP to about a
  thou. The two back points are appended at the tooth extremes, so the reported number is the extent
  of the part.

- **The pulley face clearance and the polycord groove root.** The face is belt width plus exactly
  2.000 mm, leaving 1 mm of land each side, and the cord case leaves exactly 1.000 mm each side so the
  revolved groove does not break out through either rim. The drawn groove root of 1.125000 in equals
  the reported `OD - cordD / 2` to 0.0e+00, and the radial depth is exactly a quarter of the cord
  diameter as the report says.

- **The teardrop pointed and flat profiles.** The flank is exactly tangent to the bore, error 0.0e+00
  to 2.5e-16, at 15, 30, 45, 60 and 80 degrees; the flank leans exactly the overhang angle off the
  build direction; the apex height is `r / sin(over)` as the doc says; the flat roof corner lies
  exactly on the tangent line from the bore, error 2e-16. Every loop closes and none self-intersects.

- **The Finger Joint T-bone relief.** The shipped placement is correct and the reviewer's second
  reading is the one the geometry supports. Offsetting the circle centre a full radius along u leaves
  it tangent to the u0 wall and takes 0 in out of each neighbouring finger, against 0.0366 in for the
  dogbone and 0.125 in for the proposed alternative, so the finger keeps its full 0.4615 in. At the
  shipped defaults the alternative would be worse still, because the slot depth is exactly two cutter
  radii, so the two circles on one wall would land on the same point.

- **Every `frcComponentData` hole position.** All 21 entries the doc comment dimensions were checked
  and none disagrees, including roboRIO 4.000 by 5.000, PDP 7.176 by 4.110, PDH 8.500 by 4.000,
  Limelight 2.835 by 1.575, Falcon 2.000 bolt circle six, Kraken X60 2.000 bolt circle eleven at
  30 degrees, and SystemCore 128.0 by 64.0 mm. The `count == 11 ? 12` divisor produces exactly eleven
  holes at a 30 degree step with the gap at the start angle, matching the stator-bump note.

- **The Insert Pocket taper.** Measured off the drawn cone, the half angle is exactly 4.0000 degrees,
  eight degrees included as specified, and the diameter where the cone crosses the face is exactly
  0.2059 in, the mouth. The lift compensation, which is easy to get wrong, is right. `comp` is applied
  only to the PRINTED family, exactly as the comment above the code says.

- **The pneumatic cylinder table.** `ext100` is exactly area times 100 for all five bores, and
  `ret100` is `(area - rod area)` times 100 to within 0.03 lb, so the areas, rods and both force
  columns are mutually consistent. Retracted length is `stroke + adder` and comes out exactly for
  every published combination, and the two sentinels distinguish "no captured length" from "the
  vendor says it does not exist" correctly.

- **The Drivetrain panel.** All eight numbers were recomputed from the defaults and agree: free speed
  15.2 ft/s, 264 lb at stall, 151 lb at 60 A, traction 143 lb, launch 1.1 g, 180 in in 1.26 s at
  15.1 ft/s crossing, 420 A asked at stall.

- **The Frame cut list.** Every finished length agrees with the drawing: four 30 in mitered rails from
  28 in node to node and a 26 in cross member, with the mitered rails reaching exactly half the
  section width past each node as the closing line claims. Joint counts, section area and mass all
  match.

- **The Bumper bare outline and the other four rule checks.** The drawn bare outline is 104.9706 in,
  which is exactly what the report prints. The band runs 1.25 to 6.25 in above the floor, matching the
  report, and R405, R403, R402-A and R402 all agree with the drawing.

- **The Arm Pivot bearing seats.** All 12 bearing outside diameters against all 3 fits were computed
  and reported, and nothing throws. The seat, the fit allowance and the printed thou figure all agree
  with the geometry cut.

- **Sheet Layout's packer, within its limits.** Every position in the report matches the drawing, the
  shelf advance and the new-sheet test behave as written, and both utilisation figures are correct
  against whole sheet area.

- **The Gearbox layout arithmetic.** Centre distances, shaft positions, spread, overall ratio and bore
  diameters are all the numbers the report prints, and `frcPinionCenters` correctly lifts a 16 tooth
  pinion to its acts-as count of 18 when spacing it.

- **The Roller and Shooter kinematics.** Wheel stations honour the end margins exactly, axis distance
  and rpm are right, hood radius and gap are printed exactly as drawn, and the inertia constant `kw`
  behaves correctly for a bored disc.

- **Measure's rounding and the three-state Inspection check.** Rounding is to a step rather than a
  digit count and behaves correctly at 0.001 in, 1/16 in and 0. The "checked and passed" line and the
  "NOT CHECKED: no parts picked" line cannot be confused by eye or by grep, share no prefix beyond
  "Measured height ", and `boxChecked` gates the failure list correctly, so a not-checked run neither
  passes nor fails that item.

---

## What remains unknown

A Python transliteration cannot answer these. Each is gathered from the five agents' own lists of
approximations.

**Whether Onshape's boolean operations succeed, and what they leave.** Every subtraction was computed
as succeeding. The Wheel lighten subtraction, the Bearing Block hole subtraction, the Frame butt
subtraction, the Shaft ring groove subtraction, the Lighten spoke subtraction and the Electronics hole
subtraction all sit inside `try` or `try silent`. The specific case that matters is Bearing Block with
the round style and the bolt circle preset, where the four holes fall partly off the part: whether a
partially intersecting subtraction succeeds, leaving scallops and printing "Holes cut : 4", or throws
and prints no holes line at all, is a kernel behaviour that could not be determined from the source.
The renders draw the full hole circles and annotate the 0.1605 in overrun rather than pick an outcome.
For the Wheel, whether the resulting subtraction splits the body into loose pieces is likewise
unknown.

**Whether `try silent` blocks are swallowing a real failure.** The MK4 pattern drill, the AndyMark
bolt circles, the MAXSpline subtraction, the turret pinion draw, the Wheel spoke subtraction and the
Lighten spoke subtraction all sit inside `try silent` and were computed as succeeding. If Onshape
refuses one, the feature still builds and the panel still prints the same numbers, so the drawings
would show holes that are not there. For the Wheel specifically, `spokesCut` stays 0 if the boolean
throws, which is the only observable difference.

**Whether a query still resolves after a face-moving operation.** The Lighten truss re-finds its wall
faces after the wall offset, with a comment saying the queries taken before the offset no longer
resolve; whether the re-find returns what is expected was not tested. Hole "Resize" runs
`opOffsetFace` on picked faces and then reports a count that assumes each call succeeded.

**Whether `qSketchRegion(id, false)` returns enclosed regions.** Three findings rest on this reading:
Wheel lighten (1.1), Gusset SKELETON (1.7) and Belt Path envelope (1.8). It is taken from the
library's own comment in `frcLightenOneFace` at lines 932 to 934, which states it directly as the
reason each truss bar gets its own sketch, and from the contrasting use of `true` at
`FRC Structure Geometry.txt` line 561. It was not verified against Onshape. If the reading is wrong,
all three findings are void.

**Loop edge parameterisation direction.** `frcPerimeterStations` samples
`evEdgeTangentLine(edge, parameter : i / nsub)`, which starts at the edge's own start vertex. The
renders assumed every loop edge runs in the loop's traversal direction. Onshape does not guarantee
this, and it is the single assumption that decides whether a symmetric plate comes out symmetric:
enumerating all 16 combinations of edge direction on one test plate's wall run showed that only 2 of
16, all-forward and all-reversed, give a mirror-symmetric station set, while the other 14 lose a
corner station and leave stations unpaired. The doc comment at lines 132 to 134 claims that sampling
each edge from its own start is sufficient; it is sufficient only for those two cases.

**Face iteration order feeding the triangulation.** The island list comes from `frcSideWallGroups`,
whose order follows Onshape's face iteration order, and that order is the insertion order into
`frcDelaunay`, where `frcInCircumcircle` uses strict inequalities. Cocircular boss layouts could
triangulate differently under a different order. The renders used the order the holes are listed in
each test plate.

**`opOffsetFace` on a non-convex outline.** The wall offset was modelled as an erosion, which is exact
for a convex outline but rounds concave outline corners where `opOffsetFace` would extend the two
faces to a sharp intersection. Every test plate was a rectangle, so this never fired; a plate with a
notch or an L outline would need a real offset. The Bumper's grown band has the same caveat, and the
code's own error message calls out a notch narrower than the offset.

**`frcRoundAlong`'s fallback path.** It tries one fillet over all edges and, if that fails, retries
each edge at r and then at r/2. The renders assumed the first attempt succeeds everywhere. Where it
does not, real masses differ slightly and `sharpCorners` would be non-zero.

**Onshape's fillet solver.** Fillet Edges' three counts, `done`, `absorbed` and `skipped`, depend
entirely on which edges the solver accepts, merges or rejects on a particular body. Only the radius
line in that panel is computed; both rendered panels are labelled as assumed.

**`evBox3d` without `tight`.** `frcMeasureBuild` in EXTENT mode and `frcMaterialDepth`, which Dogbone
Corners uses to set its cut depth, both call `evBox3d` with only `topology` and `cSys`. Onshape's
non-tight box may be larger than the true one on bodies with curved faces. On a flat plate it is
exact; on a body with cylindrical or spline faces the reported extent can read high, and in Measure's
case it is then published into a variable that other features drill to. The magnitude could not be
quantified.

**How Onshape splits a circular edge.** The Wire Path hexagon finding (3.1) assumes a full circle is
one closed edge, which gives six chords at `perEdge = 6`. If Onshape represents it as two half-circle
edges the count doubles and the error halves, 0.127 in on the 1.9 in pocket instead of 0.255.

**Every mass line.** `evVolume` runs on the real solid after bores, grooves, chamfers and edge breaks.
Volumes were computed analytically from the 2D profile times the extrude depth. Fillets and chamfers
were modelled as area corrections of `(1 - PI/4) r^2` per unit length of edge, and the 0.02 to 0.03 in
`frcBreakEdges` chamfers were ignored entirely as below the reported precision. Mitred rail cavity
volumes used a Sutherland-Hodgman clip of two convex quads, which is exact for those shapes but is the
agent's own code, not Onshape's. Reported masses are therefore good to about a percent, not to the
three decimals `frcFormatMass` prints, and the Shaft and Spacer masses are upper bounds.

**FeatureScript's number to string, and `roundToPrecision`'s tie breaking.** Both were reimplemented,
not observed. The assumption is shortest round trip with a trailing `.0` stripped, which is what makes
`frcInches(2 in)` print `2 in`, and round-half-away-from-zero. If FeatureScript in fact prints `2.0`,
every panel gains two characters per integral value and several more cross sixty. If it uses banker's
rounding, a handful of last-digit values could differ; the candidates are the elevator's
`21 percent` and the shooter's `24.3 percent`. No value in any panel landed on a tie.

**Placement and pattern transforms.** `frcPickFrame` was assumed to return the XY plane, and
`getRemainderPatternTransform` and `transformResultIfNecessary` were assumed to be the identity, so
every drawing is in the feature's local frame. No pattern or mirror case was exercised.

**`frcClassifyBoundaries` on a real assembly of tubes.** The Bumper's reported perimeter comes from
`frcClassifyBoundaries(frcSideWallGroups(...))`, whose outer-face classification could not be run. On
the solid octagonal plate the renders used, the eight side walls are unambiguous; on a real four-tube
frame the classification is what decides the number. `frcClassifyBoundaries` also marks a boundary
round only when `squareness > 0.98 && size(group) <= 2`, and a non-round island takes a different
`protR` with no `holeFactor` growth; every hole in every test plate was round, so that path is
untested.

**Everything that needs a model to exist.** Part counts, centroids, volumes, own-material counts and
printed counts do not exist without a model, so the Parts, Weight Budget, Center of Gravity and
Inspection panels were driven from chosen inputs (stated in every caption) through the code's own
arithmetic. The same applies to Measure's picks, Belt and Chain's and Belt Path's pulley positions and
centre distances, Sheet Layout's plate extents from `frcPlateExtents`, Finger Joint's overlap box from
`frcOverlapBox`, the stock thicknesses `frcMaterialDepth` would return, and Mate Connectors' choice of
near end in `frcHoleFrames`, which depends on which end Onshape calls the surface origin.

**Module envelopes and vendor drawings.** The axis-inset check reads each module's envelope out of a
prose `height` string. Only SDS MK4i publishes an axis-to-edge dimension (2.625 in); for SDS MK4 the
axis was inferred from the 2.75 in pattern legs; for every other module the axis was assumed central
in the published square, which the vendors do not state. REV MAXSwerve publishes two footprints, 5.24
in over the tabs and 3.96 without, and REV does not say which governs frame clearance. The SDS MK4
layout drawing itself is not in the repository, so whether `frcSwerveMk4Points` matches it could not
be checked; nor could the WCP drawings behind the two tight bearing plates, nor the uncited source
behind the Sport gearbox's 1.500 in boss. For the COTS "do the holes fit inside the face" check, the
table records no outer dimension, so only figures the library states elsewhere were used and the rest
are reported as a minimum required face diameter rather than a pass or a fail.

**The regen error paths.** The `> 140 points` and `> 260 segments` truss limits, the `> 900` cell
limit, the `> 400` bar limit, the `> 3000` tube hole limit, the 1200-hole rail grid guard and the
`> 400` dogbone corner limit were never reached on the test cases, so the errors behind them are
transcribed but unexercised. The two regen errors that were rendered, Turret at 20 DP and the 1-1/2 in
double-end cylinder, are predicted from the guards rather than observed.

**Chamfers and edge breaks as drawn.** `opChamfer` and `frcBreakEdges` results are drawn as ideal 45
degree flats of the nominal size. Onshape's equal-offset chamfer on a hex corner or a circular edge
will differ slightly at the vertices. The Shaft ring-groove side view shows the groove at full depth
on the corners, with the scalloped result shown in the end view instead, because rendering the 3D
intersection of a revolve with a hex prism in 2D would have needed a solid modeller.
