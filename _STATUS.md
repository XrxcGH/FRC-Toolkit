# Status, feature by feature

## Added after this document was written

Three things landed after the 15:13 UTC re-check below, so read the rest with these in mind.

- **There are now 46 features, not 45.** A new one, **Teardrop Hole**, was added to
  FRC Fabrication Geometry.txt with its declaration in FRC ToolKit.txt. It reshapes a round hole
  into a teardrop or keyhole so a 3D printer can build the top without bridging, in two modes:
  convert existing cylindrical holes in place, or cut new ones on a picked face. It has never
  been compiled or drawn, so put it on the regenerate-first list below, near the top.
- **A crash was fixed.** `frcMaterialLabel` in FRC Hardware Geometry.txt kept its own copy of the
  material name table and was missing the two materials Core gained today, so Weight Budget,
  Center of Gravity and Inspection all threw the moment a user picked pool noodle foam or a wire
  bundle. It now forwards to Core's `frcMaterialName`, which is the single source.
- **Reports were compressed further.** Weight Budget is 10 lines in the ordinary case, Center of
  Gravity 8, Inspection 8, Swerve Chassis 8. Every dialog label is now 30 characters or fewer and
  every tooltip 110 or fewer, so nothing is truncated by Onshape's narrow field column.

A final static audit after all of the above found zero blocking and zero serious defects across
all twelve files. Its report is in _AUDIT.md.


Snapshot. The eleven code tabs were read at **2026-08-28 15:01 UTC** and every statement below is
measured against that read, not taken from a change log. Other agents were writing to the same
files throughout: FRC Plate Geometry.txt, FRC Structure Geometry.txt and FRC ToolKit.txt were all
rewritten at 15:00 UTC, one minute before that read, and FRC Hardware Geometry.txt was rewritten
again at about 15:10 UTC, compressing the Weight Budget and Inspection panels further. A re-check
at 15:13 UTC confirmed that every specific claim below still holds against the files, but the
files are moving and anything written after 15:13 UTC is not in this document.

Covers all 45 features declared in FRC ToolKit.txt. The count was taken from the file: 45
`"Feature Type Name"` entries, 45 `defineFeature` calls, 45 distinct `frc*Build` functions, all
of them defined and exported, alphabetically Arm Pivot through Wire Path.

## The ground this document stands on has moved

Two things changed today and both change what every row below means.

**The Onshape connection is gone.** The API allocation ran out and the server has since
disconnected. Nothing in this library has been compiled, published or regenerated since. The
twelve .txt files in `` are now the deliverable, and the owner pastes
each one into its matching Onshape tab by hand. That procedure is in PUBLISH_QUEUE.md.

**Everything this document used to call "staged" has landed in the .txt files.** There is no
longer a staged copy waiting on a publish beside a live copy without it. There is one copy, on
disk, and Onshape holds whatever was published before the connection dropped, which is now behind
on every tab. The files the old queue named, `hardware_WITH_PRINTED_DENSITY_unpublished.fs`,
`frc-structure-geometry.PENDING-PUBLISH.fs`, `electrical_WITH_FIXES_unpublished.fs`,
`work/plate_STAGED.fs` and `work/toolkit_STAGED.fs`, are superseded history. Do not paste from
them.

The consequence is that **unverified is now the normal state of the whole library**, not the
exception. Every one of the 45 builder functions differs from the backup taken at 07:57 UTC this
morning, which was itself already a day's work in. No FeatureScript compiler has seen any of it.
The static audit at `_AUDIT.md` expects the library to compile and found no unresolved
symbol, no bracket imbalance and no missing enum member, but a text scanner is not a compiler and
it says so itself. Read "uncompiled" below as literal: not compiled, not drawn, not looked at.

## Regenerate and eyeball these first

In this order, once Onshape is back. The reason each one is here is the second column.

| # | What to regenerate | Why it is this high |
| --- | --- | --- |
| 1 | **Lighten**, truss pattern, on the same three plates that produced the original defect images | Its three defects were reported from a screenshot and its fixes have never been seen working. It is also the largest and most intricate change of the day: a new station function, a new wall-extension function, a new pocket-crossing test, a station-spacing cap and a floating-point epsilon, all interacting. Photograph and compare against the originals. The harness counts are a proxy; the pictures are the check. |
| 2 | **Weight Budget** and **Center of Gravity**, on a mixed selection including a printed part, a pool noodle and a wire run | Two reasons. First, `frcMaterialLabel` in FRC Hardware Geometry.txt was a nine-entry table against an eleven-member enum until about 14:37 UTC today, and until then these two features and Inspection threw a return-type failure the moment a user picked Pool noodle or Wire bundle. The fix is under half an hour old and has never been compiled. Second, both features now weigh each part at its own assigned material and weigh printed parts at an infill-reduced density, so every number they print is new arithmetic. |
| 3 | **Bumper**, on a 27 by 27 in frame | It gained a new dialog field, `perimeterLimit`, and this is the only new field added to the Toolkit today. A bound that does not resolve is a dialog that will not open. Its foam now reads 27.7 kg/m3 from Core instead of an invented 35, so the reported bumper mass should drop by roughly a fifth. Three exported constants were deleted from the tab and an indentation bug in the report was closed. Four separate changes, none seen. |
| 4 | **Any feature under a pattern or a mirror.** Sample five: Slot (moves before a boolean), Frame (moves after the cut lengths are measured), Wheel (moves after the material is applied), Gearbox (guarded by a `moved` flag), Belt and Chain (guarded by `made`) | Thirty features gained pattern and mirror support today. Before today only the five in FRC Structure Geometry had it. The placement of the move differs per feature and each placement is a judgement call that has never been executed. A wrong placement gives no error: it returns the seed instance and drops the rest, or moves nothing. |
| 5 | **Swerve Chassis**, at defaults and then with Mount style set to "Bottom, plate on rails" | Its report was rewritten from up to 26 lines to 8, and the bottom-mount dropdown was read by nothing anywhere in the library until today. The two NOTE lines appearing and disappearing as Mount style is changed is the only proof the parameter is read at all. This feature has also never been drawn in a Part Studio since it was rewritten module aware. |
| 6 | **Frame** and **Tube**, two members and two tubes each | Both now name their bodies from what they measured, so a cut list reads `Tube 2x1x0.1 - 24.0 in` rather than `Frame Member 1`. Both also publish a computed feature name. Those name strings are assembled from rounded measurements and landed at 15:00 UTC. |
| 7 | **Hole**, **Tube** and **Gusset**, one regen each | They share the Plate tab with Lighten. That tab stopped compiling once already today. A compile check there is a check on four features. |
| 8 | **Electronics** with NEO 550 selected | New component data, from REV-21-1651-DR and DS. Measure the bolt circle: 25.0 mm, not 2.000 in. Then confirm the NEO entry's six-hole pattern is unchanged and its UNRESOLVED note prints. |
| 9 | **Wire Path**, then **Weight Budget** over it | The Wire Run body now carries a material at 1640 kg/m3, so the harness should appear in the total with a non-zero mass for the first time. |
| 10 | The seven features that have never been drawn at all: Swerve Chassis, Arm Pivot, Turret, Climber, Shooter, Pneumatic Cylinder, Battery Mount | Compiling is not working. Nothing has ever been built with these. |

## How to read the table

**State.** Every one of the 45 builders changed today, so the only distinctions worth carrying
are whether the feature has ever been drawn and, in the next column, what kind of change landed.

| Value | Meaning |
| --- | --- |
| Changed today, uncompiled | The builder differs from this morning's backup. No compile, no regen since. |
| Changed today, uncompiled, never drawn | The same, on a feature no Part Studio has ever regenerated on any version of the code. |

**Done but unverified** is work that is in the code now and has never been compiled or run.
**Outstanding** is work that has not been done at all. That split is the point of this table:
nothing here is confirmed, but the two columns are not the same kind of not-confirmed.

One change reached every feature and is not repeated in every row: the information panel of all
45 was condensed today, so report wording, column widths and line breaks differ everywhere from
what is published in Onshape. Where only that happened, the Changed today column says so.

Sticky field counts were counted from the file: 69 `REMEMBER_PREVIOUS_VALUE` hints across
FRC ToolKit.txt, 68 inside feature blocks and one on the shared `frcWeighPredicate`, which is why
Weight Budget and Center of Gravity each show one that is not declared in their own block.

## FRC Plate Geometry

Four features. The tab stopped compiling for a period earlier today and everything in it was dead
while that lasted. It balances and resolves as far as a text scan can tell, and no further. This
tab was rewritten at 15:00 UTC, one minute before the snapshot.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Lighten | Plate | Changed today, uncompiled | The truss fix landed in the file. New `frcPerimeterStations` returns each wall station with the direction the wall runs there, and `frcPerimeterAnchors` is kept as a thin wrapper returning the points alone so existing callers do not change. New `frcWallExtension` divides the rib extension by the sine of the arrival angle, capped at 3.0, so a rib buries its end in the wall at any angle instead of stopping inside the pocket below about 49 degrees. A rib that cannot be anchored within the cap is reported unanchored and dropped rather than left dangling. A new `crossesPocket` closure keeps chords between two wall stations where they genuinely cross open pocket, probing the midpoint and both quarter points to each side, because a point sitting exactly on a wall face is not a reliable answer. Station spacing is capped at a quarter of the longer span and `floor(L / maxEdge)` gained a 1e-9 epsilon, which is also what makes a symmetric outline come out mirror symmetric. Separately: corners that would not fillet are now counted into `sharpCorners` and reported instead of dropped silently; the rib count for isogrid, grid and diagonal now counts bars that reach the pocket rather than every bar index sketched over the circumscribing square, so the panel, the tree name and the graphics area should finally agree; pattern and mirror support was added, with the transform read inside `frcLightenOneFace` so each face moves under its own sub-id and no two faces collide; 20 `regenError` calls in this tab gained a faulted query. Six sticky fields. | All of it. The three photographed defects, torn rib edges, ribs ending in open space and an untriangulated region, have fix code in the file and no evidence of any kind that it works. The rib count and the sharp-corner warning have never printed. The per-face pattern transform has never run. | Nothing new is queued for Lighten beyond proving the above. Click-to-skip manipulators (`_REMAINING IDEAS.md` C2) and raycast exclusion regions (B21) are unstarted. |
| Hole | Plate | Changed today, uncompiled | Pattern and mirror support on the new-holes branch, with the transform placed before `opBoolean` because the subtraction consumes the drills. The resize branch is deliberately left without one: `opOffsetFace` on picked faces creates no body to move. `regenError` calls gained faulted queries, including the single hole that would not resize. Report condensed. Three sticky fields (hole size, fit, process). | The pattern transform and the fault highlighting. | Route the NEW mode through the standard `hole()` feature instead of extruding and subtracting circles, so holes carry a `HoleAttribute` and appear in drawing hole tables. Neither `onshape/std/hole.fs` nor `holetables.gen.fs` is imported anywhere in the library. `_REMAINING IDEAS.md` B9. |
| Tube | Plate | Changed today, uncompiled | Two changes beyond the report condensation. The size note now describes every tube: `secMin`, `secMax`, `lenMin`, `lenMax` are tracked across the loop, so the report gives a number where every tube agrees and "mixed sections" or "mixed lengths" where they do not, instead of printing the first body's size beside a count of all of them. And at 15:00 UTC each tube body gained a name built from what was measured, `Tube <major>x<minor>x<wall> - <length> in`, with the length zero-padded below 10 so an alphabetical parts list runs short to long. The feature publishes `tubes` and its tree name is `Tube - #tubes tubes`. Four sticky fields. | Both. The name string is assembled from rounded measurements and has never been rendered. The computed feature name has never resolved. | No pattern or mirror support, by a decision recorded in the source: this builder creates no body that outlives the feature, and a pattern instance of Tube alone re-enters `opShell` on an already shelled body. Pattern the extrusion feature together with the Tube feature. Also outstanding: `makeRobustQueriesBatched` before the shell (B6), partial-hole cleanup by face area (B7), and a fallback face classification for a tube that already carries a cope (B16). |
| Gusset | Plate | Changed today, uncompiled | Pattern and mirror support, with the move after `frcRoundAlong` and before `evVolume`, since volume is invariant under a rigid move. `regenError` gained `definition.holes`. At 15:00 UTC it began publishing `bolts`, tree name `Gusset - #bolts holes`; the parameter is named `bolts` and not `holes` because the dialog already has a `holes` selection that a `#holes` token would resolve to instead. Two sticky fields. | The transform, the fault query and the computed name. | Replace the overlapping `frcBar` quads at each node with mitred offsets at `dist = ptSize / sin(dangle/2)` on the bisector. `frcBar` in FRC Core.txt still returns a plain four-point quad, so arms still lump at every node. Perimeter fillets and inferred hole rows are also unstarted. `_REMAINING IDEAS.md` B12. |

## FRC Motion Geometry

Five features. All five gained pattern and mirror support today; before today this tab had none.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Gear | Motion | Changed today, uncompiled | Pattern and mirror support. The reported rack length is now read back off the extreme x values of the points that were drawn, instead of a second closed-form expression that overstated the blank by about 0.9/DP, which is 0.046 in at 20 DP. The geometry was already right; only the number was wrong. Two sticky fields. | Both. A 20 DP, 12 tooth rack should measure 1.8386 in end to end and the panel should print that, not 1.8850 in. | None recorded. |
| Pulley | Motion | Changed today, uncompiled | Pattern and mirror support. The face is now belt or cord width plus a `faceClear` of 2 mm, so 1 mm of land shows each side; the report line prints the figure and calls it a rule of thumb, which it is, because no vendor in the belt table publishes a face width. The polycord branch gained a `Groove root` line at `OD - cordD / 2`. Flange edges are broken by `frcBreakEdges`. One sticky field. | All three. A 24T HTD 5 at a 0.375 in belt should measure 0.4488 in across the rim, flanges on or off. | Break the groove top land, 0.43 mm on HTD 5 and 0.25 mm on GT2 3, so the belt does not load a sharp corner. Not present: the only land handling in this tab is the sprocket tooth-tip land. `_REMAINING IDEAS.md` A10. |
| Sprocket | Motion | Changed today, uncompiled | Pattern and mirror support. No profile change. Report condensed. One sticky field. | The transform. | None. **The seating-curve item this document used to carry is closed.** `R = 0.5025 * Dr + 0.0015` is correct and forced by `E = ac + R` with `ac = 0.8 Dr` and `E = 1.3025 Dr + 0.0015`; 0.50025 would open a 0.00225 Dr step between the seating curve and the flank. The derivation is in the source at FRC Motion Geomtery.txt:522-528 and in `_REMAINING IDEAS.md` D1. Do not raise it again. |
| Shaft | Motion | Changed today, uncompiled | Pattern and mirror support. Report condensed. The retaining-ring groove correction to the 3/8 band predates today. One sticky field. | The transform. | `frcRingGroove` is still five buckets, not a keyed table. The 3/8 band is correct: 0.375 in falls in the `<= 0.40` bucket at depth 0.0115, width 0.030. The band still wrong is 0.55, where a 0.020 depth grooves a 1/2 in shaft at 0.460 dia; the two third-party sources disagree with us and with each other, 0.458 against 0.468, so this is **blocked on a real print** rather than merely undone. E-clips are modelled nowhere: zero occurrences in the library. Hollow stock IDs, Churro and captive ends are also unstarted. `_REMAINING IDEAS.md` A6, C9. |
| Spacer | Motion | Changed today, uncompiled | Pattern and mirror support. Report condensed. One sticky field. | The transform. | Take the bore from the circular edge the user picked. `evCurveDefinition` is called in Core, Manufacturing and Shop but not in `frcSpacerBuild`, so the feature still asks for the location and then every diameter again. `_REMAINING IDEAS.md` B13. |

## FRC Structure Geometry

Five features. This tab already had pattern and mirror support before today; it was the only tab
that did. Rewritten at 15:00 UTC, one minute before the snapshot.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Slot | Structure | Changed today, uncompiled | Report condensed, and four `regenError` calls gained a faulted query: the over-200 case and the unreadable-points case highlight `definition.locations`, the square-edge case highlights the offending edge itself. No geometry change; the pattern transform predates today. One sticky field. | The fault queries, and the older pattern transform, which has also not been regenerated since the connection dropped. | None recorded. |
| Bumper | Structure | Changed today, uncompiled | The largest change in this tab. Foam density now reads `FRCMaterial.FOAM_NOODLE` out of Core at 27.7 kg/m3 rather than an invented 35 in this file, worth about 0.4 lb across a set against a 135 lb limit. Cover density is a named constant `FRC_BUMPER_COVER_DENSITY` at 600 kg/m3, with a comment saying it is a rule of thumb; the value itself did not change. The R104 limit is now read from a new `perimeterLimit` field with the old constant as fallback, and the field is declared in FRC ToolKit.txt at precondition scope rather than inside the output branch, so it exists for every output mode instead of silently reverting to the constant when the user switches output. Report labels changed: `Perimeter` became `Bare frame`, the rule line reads "R104 bare frame outline at most", and two lines now point at FRC Inspection for the over-bumpers check, so the two panels read as two measurements rather than a contradiction. Three exported constants were deleted, `FRC_BUMPER_HARD_MAX`, `FRC_BUMPER_GAP_MAX` and `FRC_BUMPER_CORNER_FILL`, and their numbers folded into the "not checked" block, which still cites R404 1.25 in, R401 1.25 in, R406 2.25 in, R412 and R408. `frcGrownBand` gained a faulted query. And the "foam sampled" note, which printed unconditionally because it sat outside its `if` on indentation alone, is now inside braces. One sticky field. | All of it. The new field is the sharpest risk: a bound that does not resolve is a dialog that will not open, and this is the only new field in the Toolkit today. Expect the reported bumper mass to fall by roughly a fifth against the last run. | Decide the cover density. `study/hardware.md` A2 puts nylon bumper fabric at 550 kg/m3 against the 600 in the file, and the value was deliberately left. Change it or write down why not. |
| Wheel | Structure | Changed today, uncompiled | Report only. The panel was condensed: over-tread and seat merged onto one line, tread thickness and wrap length merged with the "cut it short" advice, flange size and stand merged, channel width folded into the width line, and the pattern source moved to an indented continuation. No geometry change; pattern support predates today. Two sticky fields. | The condensed panel, and the older pattern transform, which needs a mirror across the robot centreline to confirm both wheels come back as real bodies. | None recorded. |
| Frame | Structure | Changed today, uncompiled | Three `regenError` calls gained faulted queries, including the single curved edge out of a picked set. At 15:00 UTC members stopped being named "Frame Member N" and started being named for the stock they come out of and the length they are cut to: `Tube 2x1x0.1 - 24.0 in`, or `Bar` where the wall is zero, with the larger section dimension first the way stock is listed and the cut length zero-padded below 10. The feature publishes `members`, tree name `Frame - #members members`. Five sticky fields. | All of it, and the naming is an hour old. | Add a frame-perimeter warning at the R104 limit, as a warning and not an error, since a practice frame may exceed it deliberately. Not present: there is exactly one `reportFeatureWarning` in the whole library and it is in Inspection. `_REMAINING IDEAS.md` B17. |
| Gearbox | Structure | Changed today, uncompiled | Report only. The ratio-search table was recast into fixed-width columns with a header naming them, the allowance moved onto the pitch line, and the closing advice was shortened. No geometry change; pattern support on the layout branch, with the move before the bore subtraction and a `moved` flag so the layout sketch still moves when no bores are cut, predates today. One sticky field. | The condensed panel, and the `moved`-flag path, which needs two regens to exercise: once with bores off, once with bores on. | None recorded. |

## FRC Mechanism Geometry

Nine features. Eight of the nine gained pattern and mirror support today; Drivetrain builds no
geometry. Six of the nine have never been drawn in a Part Studio.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Drivetrain | Mechanism | Changed today, uncompiled | Report only, and one error message made more specific. No geometry, so no pattern support and none wanted. The sprint integrator was verified numerically when it was written. No sticky fields. | The condensed panel. | None. |
| Swerve Chassis | Mechanism | Changed today, uncompiled, never drawn | Three changes. The report no longer prints one corner's module data as the whole chassis: corners are grouped by module name and each distinct module gets a row naming its corners and leading with its fastener line, clipped by a new `frcOneLine` helper at a word boundary so the count and thread size always survive. A chassis with an MK4c at one corner and an MK4i at another used to be shown the MK4c's screw count as the whole robot's, which is wrong hardware ordered. The panel was cut from 23 lines at defaults to 8, and from 26 to 9 on a loaded chassis; frame size, rail size, the forced-cut note, the rail grid count, the support and cover counts and three trailing advisories were dropped, and the dead variables left behind were removed. And the Mount style dropdown, which was read by nothing anywhere in the library, is now read: picking "Bottom, plate on rails" prints two NOTE lines saying the top mount was built and the corner cut, pattern and height must be set by hand. The geometry is deliberately unchanged, because `frcSwerveModuleData` carries no bottom-mount cut length, hole datum or plate thickness, and inventing them would have put invented numbers under the heading "From the vendor drawings". Pattern and mirror support added. Seven sticky fields: rail width, rail height, rail wall, hole size, belly pan thickness, gusset thickness, material. | All of it, on a builder that has never been drawn at all since it was rewritten module aware. The bottom-mount test is exact: the two NOTE lines must appear when Mount style changes and disappear when it changes back, with the Mass line and the part list identical either way. Any geometry change there is a failure of the fix. | Warn when `c2c + wheel / 2 >= sidelength / 2`, the module-collision case. `_REMAINING IDEAS.md` B17. |
| Elevator | Mechanism | Changed today, uncompiled | Pattern and mirror support, placed after `frcApplyPart` on the stack; the fillet-edge selection that reads original axes already sat before the transform. Report condensed. Four sticky fields. | The transform. | None recorded. |
| Arm Pivot | Mechanism | Changed today, uncompiled, never drawn | Pattern and mirror support, placed after the axle chamfer. Report condensed. Two sticky fields. | The transform, on a builder that has never been drawn. | Check the bearing seats against a real 1.125 in flanged bearing when it is first drawn. |
| Turret | Mechanism | Changed today, uncompiled, never drawn | Pattern and mirror support, placed after the pinion's material. Report condensed. Two sticky fields. | The transform, on a builder that has never been drawn. | Confirm the ring gear meshes with the phased pinion, including the 180/N rotation when the pinion tooth count is even. |
| Climber | Mechanism | Changed today, uncompiled, never drawn | Pattern and mirror support, placed after `frcApplyPart` on the tubes; the per-stage mass sum already sat before it. Report condensed. Two sticky fields. | The transform, on a builder that has never been drawn. This is one of two features that build several bodies at once, so all its bodies must move together. | Regen at one and two stages. |
| Roller | Mechanism | Changed today, uncompiled | Pattern and mirror support, placed after the wheel loop. Report condensed. One sticky field. | The transform. | None recorded. |
| Shooter | Mechanism | Changed today, uncompiled, never drawn | Pattern and mirror support, placed after the hood. Report condensed. One sticky field. | The transform, on a builder that has never been drawn. | Check the reported exit speed against a hand calculation. |
| Pneumatic Cylinder | Mechanism | Changed today, uncompiled, never drawn | Pattern and mirror support, placed after the rod's material. Report condensed. No sticky fields. | The transform, on a builder that has never been drawn. Its own `definition.mountStyle` is an `FRCCylMount` and is unrelated to the swerve parameter of the same name; that collision is what made the swerve dropdown look wired up to a grep while nothing read it. | Check the retracted length against the published adder for each mount style. |

## FRC Hardware Geometry

Five features. This tab carried the only blocking defect found in today's static audit, and that
defect was fixed after the audit was written.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Bearing Block | Hardware | Changed today, uncompiled | Pattern and mirror support, placed after `frcApplyPart`. Report condensed. Three sticky fields. | The transform. | Name the bearing and quote its VEXpro part number in the report. Core exports `frcBearingData` and `frcBearingPartName` and **nothing outside Core calls either**; `frcBearingPartName` has no caller at all. Also outstanding: `MASS_OVERRIDE` from the vendor weights the bearing table already carries, since a 1/2 by 1-1/8 flanged bearing modelled as solid stock computes about 0.085 lb against a real 0.058 lb. `_REMAINING IDEAS.md` B11. |
| Weight Budget | Hardware | Changed today, uncompiled | Three changes beyond the panel. Each part is weighed at the material assigned to that part, read with `getProperty`, falling back to the group material and then the global one, and the report says how many parts were weighed at their own material and how many at an assumed one. This corrects a belief recorded in the source and printed in the report, that a custom feature cannot read part materials; it can. Printed parts are weighed at `frcPrintedDensity` from surface area, volume, infill and wall count instead of solid plastic, driven by two new dialog fields, Printed infill and Printed wall count, bound by `FRC_INFILL_BOUNDS` and `FRC_WALLS_BOUNDS`, with a count of parts that came back at solid density because the shell estimate already filled them, and a note where surface area could not be read. Every new path is wrapped so a failure leaves the part at solid density, which is the conservative way to be wrong in a weight budget. And `frcMaterialLabel`, a nine-entry table against an eleven-member enum, now forwards to Core's `frcMaterialName`. The heaviest-parts default dropped from 10 rows to 5. One sticky field, through the shared weigh predicate. | All of it. The `frcMaterialLabel` fix is the sharpest: until about 14:37 UTC today this feature threw the moment a user picked Pool noodle or Wire bundle, both of which its own dropdown offers and both of which its tooltip and the read me advertise. Weighing PLA, PETG or Onyx solid overstates a real print by roughly a factor of two, so expect printed masses to fall by about half. | Weigh a real printed bracket at 20 percent infill and 3 walls and compare with the slicer; expect roughly 35 to 45 percent of solid, and expect a part under about 2 mm to read close to solid with the report saying so. Then cut the 10 lb catch-all allowance down to fasteners and unmodelled electronics, once the wire harness is counted. An array parameter would remove the four-group cap; the library has zero array parameters. `_REMAINING IDEAS.md` B8. |
| Center of Gravity | Hardware | Changed today, uncompiled | Same per-part material read and same printed-density path as Weight Budget, with the same two new fields and a report line saying it falls back to the Core print defaults when the fields are absent. Gained the 600-part guard Weight Budget already had, with the same error wording, so a whole-robot selection fails instead of spinning. The `frcMaterialLabel` fix reaches it too. One sticky field, through the shared weigh predicate. | All of it. Confirm the CG point actually moves once printed parts are re-weighed at infill density. Deliberately given no pattern support, correctly: it measures the whole model, so a patterned instance would re-measure the same model and place its point by that measurement rather than by the pattern transform. | Same as Weight Budget. |
| Inspection | Hardware | Changed today, uncompiled | Two changes. The measured-height check had `boxOk` initialised true and assigned only inside the branch that runs when bodies are picked, so an empty pick silently passed; there are now three states, `boxChecked` and `boxOk`, and the failure list tests `boxChecked && !boxOk`. The two perimeter report lines became three and say "over the bumpers" explicitly. The `frcMaterialLabel` fix reaches it too. One sticky field. | Both. Run with the bodies field empty and a height limit below anything in the model: the panel must say the measured height is not checked, and no warning may name it. Then pick a body over the limit and the warning must name it. | A hole-diameter table would slot in here. `_REMAINING IDEAS.md` C10. |
| Battery Mount | Hardware | Changed today, uncompiled, never drawn | Pattern and mirror support, placed after `frcApplyPart`. Report condensed. Two sticky fields. | The transform, on a builder that has never been drawn. | Check the strap slots and lead notch against a real battery envelope when it is first drawn. |

## FRC Electrical Geometry

Two features.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Electronics | Electrical | Changed today, uncompiled | The single entry labelled "NEO or NEO 550 (round face)" was split in two. `FRCComponent.NEO_550` is new, from REV-21-1651-DR and REV-21-1651-DS: four M3 on a 25.0 mm bolt circle tapped 4.75 mm deep, a 13.0 mm pilot taken to 0.517 in with the library's own clearance, and a 35.0 by 44.5 mm can. A team that picked the old combined entry for a NEO 550 got 10-32 holes two inches apart on a motor 1.378 in across. Where the holes sit around the circle is not published, so they are cut at 90 degrees from the rotation the user sets and the note says to check that against the motor. The NEO entry was left numerically alone and carries an UNRESOLVED note: it cuts six evenly spaced holes, REV-21-1650-DR calls out four at an 89 degree step, and four holes at 89 degrees is not a pattern this feature can cut, so nothing was guessed. Pattern and mirror support added, with two `transformResultIfNecessary` calls on mutually exclusive paths guarded by a `moved` flag. One sticky field. | All of it. The new enum member appears in the Toolkit's dropdown with no Toolkit change, because the Electronics declaration branches only on `CUSTOM`, so the two tabs are not coupled and no matched paste is required. | Settle the NEO face by measuring a real motor or getting a hole table from REV, and either fix the count or keep the note. Also outstanding: clock the footprint to a reference edge and leave a mate connector, so a mirrored footprint is not handed the wrong way round. There is no rotation input at all today. `_REMAINING IDEAS.md` B10. |
| Wire Path | Electrical | Changed today, uncompiled | The Wire Run body now carries `FRCMaterial.WIRE_BUNDLE` at 1640 kg/m3 through `frcApplyPart`, an envelope density measured as the mass of a real routed bundle over the volume drawn around it. It previously had a name and a translucent colour and no material, so it weighed nothing and several pounds of harness fell off every weight budget silently. The report prints the bundle mass, tells the user to keep the body rather than delete it, and says the density is mass over envelope volume with the air between conductors already in it, so it must not be read as a solid. Pattern and mirror support added, same `moved`-flag shape as Electronics. The empty-path `regenError` picks its query on the mode: `pathEdges` in sketch mode, `endPoints` otherwise, because both are already known non-empty by the time that error can fire. One sticky field. | All of it. Run Wire Path with the bundle on, then Weight Budget over it, and confirm a non-zero harness mass appears in the total. | A fallback wire diameter for gauges not in the table, as a fallback only and never as a replacement for the table. `_REMAINING IDEAS.md` B23. |

## FRC Manufacturing Geometry

Five features. **This tab is no longer a blind spot.** The previous version of this document
carried two Unknown rows here because the only copy on disk was a transcription dated 2026-08-26.
The tab is now a current file at `FRC Manufacturing Geometry.txt`, read
at 15:01 UTC, and both rows are resolved against it.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Belt and Chain | Manufacturing | Changed today, uncompiled | Pattern and mirror support, with the transform guarded by `if (made)` since nothing is built when the path is not drawn. The polycord branch no longer prints the same number twice: `counted` is never set for cord, the unused unit name went with it, and cord gets one line reading "cut to length, no stock sizes". Belt tooth counts round up to a multiple of five through `FRC_BELT_TOOTH_STEP` and `frcStockableBeltTeeth`; chain still rounds up to an even link count. The two shaft centres pick carries `ALLOW_QUERY_ORDER`, one of only two such hints in the library. **This feature has no sticky fields**, which corrects a claim in the previous version of this document. | The transform and the cord report line. The belt tooth step and the query order predate today. | A belt as a real part, split across the pitch line rather than a flat ribbon on it. `_REMAINING IDEAS.md` C7. |
| Belt Path | Manufacturing | Changed today, uncompiled | Pattern and mirror support, same `if (made)` guard and same reason. The pulley-circle pick carries `ALLOW_QUERY_ORDER`; without it Onshape returned the pulleys in internal order, so the loop walked the wrong polygon and signed the wrong sides, which was silently wrong rather than visibly broken. No sticky fields. | The transform. | Run a four-pulley path with a reversed idler and check the reported teeth in mesh at each pulley against the geometry. Widen the pick filter, which is `EntityType.EDGE && GeometryType.CIRCLE` only, to the full set `frcPickFrame` already resolves. |
| Dogbone Corners | Manufacturing | Changed today, uncompiled | **Resolved from Unknown.** Pattern and mirror support, with the transform between `opExtrude` and `opBoolean` because the boolean consumes the cutters and a transform after it would find nothing left to move. `regenError` passes `definition.faces`. One sticky field. | The transform. Pattern the dogbone feature over three pockets: before this change all three relief sets landed in the first pocket. | None recorded. |
| Fillet Edges | Manufacturing | Changed today, uncompiled | The report separates edges absorbed by an earlier fillet from edges that genuinely failed: `absorbed` and `skipped` are counted separately and printed on separate lines, so "Edges skipped" means what it says. Deliberately given no pattern support: it creates no bodies and rounds edges on bodies the user picked, which a pattern moves on its own. Two sticky fields. | The two counters. | Add a chamfer mode and a "borders these faces" scope, for deburring every hole in a punched tube without touching the corner radii. `_REMAINING IDEAS.md` B15. |
| Measure | Manufacturing | Changed today, uncompiled | **Resolved from Unknown.** A `faultQ` variable was added beside the existing `fault`, set in the same three places, so "That pick could not be measured" highlights the pick that failed; it starts as the union of the two picks because both the distance and the angle modes read them. Deliberately given no pattern support: it creates no bodies and publishes a variable. No sticky fields. | The fault query. | Move `setVariable` to `assignVariable` with an explicit `VariableType`, so the value is typed and visible in the tree. The file still calls `setVariable`, at FRC Manufacturing Geometry.txt:1008. That line also settles an old question: `study/utils.md` C4, which says Measure only reports, is **wrong**. It writes a Part Studio variable. `_REMAINING IDEAS.md` B19. |

## FRC Shop Geometry

Seven features. Four of the seven gained pattern and mirror support today.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Bolt Pattern | Shop | Changed today, uncompiled | Pattern and mirror support. Report condensed. One sticky field. | The transform. | Derive the grid from face tangent planes with a flatness check, add a tolerance before `floor` so 27.999999 does not lose a row, and cut one cylinder and pattern its faces rather than booleaning N tools. `_REMAINING IDEAS.md` B20, and the click-to-skip manipulator, C2. |
| COTS Pattern | Shop | Changed today, uncompiled | Seven mounting faces added: CIM-class with pilot boss, 550, 775, BAG, REV UltraPlanetary, REV MAXPlanetary and Sport gearbox. Most come from a community FeatureScript library rather than a vendor drawing and the code says so: each new entry carries `vendor` set to false, a note naming what is corroborated and what rests on that single source, and the source line, and the report repeats it. Three are corroborated against vendor data the library already holds. VersaPlanetary was left out on purpose because its quoted 0.1695 in hole is smaller than the 0.190 in major diameter of the screw it must pass. In the dialog, the Sport gearbox now shares the CIM-class branch that exposes hole count and start angle, because its source gives no count, and the bore checkbox reads "Cut the bore as well" rather than "Cut the bearing bore as well", since these are pilot bosses and not bearing seats. Pattern and mirror support added. One sticky field. | All of it. | Measure a real 550, 775, BAG, UltraPlanetary and Sport face and either confirm the single-source numbers or replace them. The Sport entry is the weakest: its 1.500 in boss leaves about 0.15 in of plate to the holes and no vendor is even named. |
| Design Constants | Shop | Changed today, uncompiled | Report only. The closing advice was reflowed to fit the panel width. Two sticky fields. | The condensed panel. | Switch from `setVariable` to `assignVariable` with a `VariableType`; add `frcTryVariable` so downstream features can default when Design Constants is absent, since `getVariable` throws on a missing name; and publish the derived relationships teams retype into every sketch. `_REMAINING IDEAS.md` B19. |
| Extrude Individual | Shop | Changed today, uncompiled | Pattern and mirror support. Report condensed. No sticky fields. | The transform. | Add symmetric and up-to-face bounds; it is BLIND only. `_REMAINING IDEAS.md` B14. |
| Mate Connectors | Shop | Changed today, uncompiled | Report only, plus faulted queries on two `regenError` calls. No pattern support and none needed: the connectors are owned by the parts they sit on. No sticky fields. | The fault queries. | None. |
| Origin Cube | Shop | Changed today, uncompiled | Pattern and mirror support. Report condensed. No sticky fields. | The transform. | None. |
| Parts | Shop | Changed today, uncompiled | Report only, plus a faulted query on the too-many-parts error. One sticky field. | The fault query. | Set `PART_NUMBER` and keep an attribute ledger of what has been numbered, so re-running does not renumber everything. The library uses **zero** attributes and sets `PART_NUMBER` nowhere; both greps return nothing. A real table would then replace the hand-padded string report. `_REMAINING IDEAS.md` C3. |

## FRC Fabrication Geometry

Three features. All three gained pattern and mirror support today; before today this tab had none.

| Feature | Tab | State | Changed today | Done but unverified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Finger Joint | Fabrication | Changed today, uncompiled | Pattern and mirror support, called under the per-joint id. Report condensed. Two sticky fields. | The transform. | None. **The T-bone relief axis is closed.** It was raised as a defect and checked against the code: the offset moves each circle into the slot, so the whole overcut lands beyond the plate thickness and no neighbouring finger loses material. The proposed change would have taken a full cutter radius out of the finger, against a dogbone's 0.2929 r, and on 0.125 in stock with a 1/8 in cutter it would have collapsed the two circles at each slot end onto one another. Code and doc comment have never disagreed. |
| Insert Pocket | Fabrication | Changed today, uncompiled | Pattern and mirror support. Report condensed. No sticky fields. | The transform. | None. |
| Sheet Layout | Fabrication | Changed today, uncompiled | Pattern and mirror support. Report condensed. No sticky fields. | The transform. | None. |

## What is not known

These are the gaps, so that nobody reads a confident sentence above and assumes it covers
everything.

- **Nothing here has been compiled.** No FeatureScript compiler has seen any of today's work. The
  static audit at `_AUDIT.md` expects the library to compile: 2,810 identifier uses resolved
  with zero unresolved, zero cross-tab reference violations, zero references to a non-existent
  enum member, balanced delimiters in all eleven files, no unterminated string or comment, no
  duplicate export, and 45 of 45 features resolving to an exported builder. That is a text scan.
  It cannot see a `ValueWithUnits` passed where a number is wanted, a map field read off a record
  that does not carry it, or a wrong argument type in a call whose arity is right.
- **The files were moving while this was written.** Plate, Structure and the Toolkit were rewritten
  at 15:00 UTC, one minute before the snapshot at 15:01 UTC. The Frame and Tube naming and the
  three new computed feature names are that recent. Another pass may have landed since.
- **Two changes today are recorded in no log.** The blocking `frcMaterialLabel` defect and the
  Bumper report indentation bug were both fixed at about 14:37 UTC, after `_AUDIT.md` was
  written and after `work/fix2_structure_mfg.md` explicitly recorded the indentation bug as noted
  and deliberately not changed. Both fixes are in the code, confirmed by diff against
  `work/blocker_backup/`. No .md file in `work/` describes either of them. Trust the code.
- **Thirty features gained pattern and mirror support in a single day**, each with a hand-placed
  transform, and not one has been executed. This is the largest untested surface in the library.
  The failure mode is silent: the seed comes back and the instances do not, or nothing moves.
- **Seven features have never been regenerated in a Part Studio at all**: Swerve Chassis, Arm
  Pivot, Turret, Climber, Shooter, Pneumatic Cylinder, Battery Mount. Marking them says what is
  known. It does not say they are wrong and it does not say they are right.
- **The live Onshape state is unknown and unreadable from here.** Every tab on disk is now ahead of
  what is published by an unknown amount, and no tool available can compare them. The element ids
  of the ten supporting tabs are still in the Toolkit's import lines, but the mapping from id to
  tab name is no longer derivable from any file, because the Toolkit's header comment naming the
  tabs was removed in the recovery trim. The manual paste workflow does not need them.
- **The Motion tab's Core pin.** Every tab on disk now pins Core at `578eb867bbdba7daf29ca549`,
  Motion included, so the one-version-behind problem this document used to record is not visible on
  disk. Whether Onshape's own copy agrees cannot be checked from here, and pasting a stale import
  line would silently roll it back. See PUBLISH_QUEUE.md, warning one.
- **Three data corrections are still open and none is blocked.** Plywood is 600 kg/m3 in
  `FRC Core.txt` where baltic birch, the FRC bumper backing use, is 680. The rounded-hex corner
  circles are stored as 0.541 and 0.404 in where ThunderHex is drawn in millimetres, 13.75 and
  10.25 mm, worth 0.34 and 0.46 thou on the exact surface a bore seats on. The chain table carries
  no overall link width, so no clearance check can be written at all. `_REMAINING IDEAS.md` A2, A4,
  A5.
