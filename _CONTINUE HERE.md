# Continue here

State of the FRC Toolkit review, written to be read cold by a session with no
memory of the work. Read this first, then `_renders/_tools/README.md`.

Last updated 2026-09-01.

## What this project is

46 Onshape custom features across 11 Feature Studio tabs, one `.txt` file per
tab in this folder, which the owner pastes into Onshape by hand.

`FRC ToolKit.txt` holds all 46 dialogs, so parameter defaults, bounds and
preconditions live there. The geometry tabs hold the builders. `FRC Core.txt`
holds shared maths and data tables and is imported by every other tab, so a
defect there is a defect in many features at once. A `frcDefinition()` aliasing
layer at the top of ToolKit renames some dialog parameters for the builders
(`partLength` to `length`, `cubeSize` to `size`, `flipSide` to `flip`,
`floorFace` to `floor`, `chamferSize` to `chamfer`, `beltLength` to `length`,
`partMaterial` to `material`), so a parameter that looks unread often is not.

## The hard constraint

The Onshape API allocation is exhausted (2,608 of 2,500 used on 2026-08-30) and
does not reset until **2026-10-13**. Nothing can be compiled, regenerated or
photographed. Establish everything by reading the source and by running Python
over it. Transliterate, measure, and compare; do not reason about the code and
call that verification.

## Non-negotiable house rules for any edit

* **Cite code by a searchable anchor, never by a line number.** Every edit
  to a tab moves every line below it, and a stale citation reads as a fact.
  Name the function, the constant or a unique fragment of the line instead:
  `opOffsetFace(context, id + "wall"` keeps working, `line 743` does not.
  A sweep on 2026-09-03 found this class in every companion document.

* CRLF throughout, pure ASCII, no tabs, no em dashes.
* Braces, parens and brackets must balance.
* Dialog labels 30 characters or fewer, tooltips 110 or fewer.
* **Run `python "_renders/_tools/verify.py"` after every edit.** It must report
  `0 tab(s) with a problem`.
* The two characters backslash-n are how a newline is written inside a string.
  A shell heredoc will collapse that escape into a real newline, which is a
  syntax error in FeatureScript. This has happened twice. Verify at byte level.
* A parameter id equal to a symbol exported by an imported Feature Studio makes
  the whole tab silently evaluate to nothing. Checked clean; keep it that way.
* Onshape does **not** render newlines in `reportFeatureInfo`; it collapses the
  panel into one paragraph. All 46 panels are punctuated prose. Keep them so.

## Be honest

Say which findings are mechanically established and which are a reading. A
confident wrong claim is worse than no claim. Two examples from this work: a
reviewer reported the Bolt Pattern pilot bore cut line-to-line over its boss,
having misread which number was the boss (0.750 in) and which was the vendor's
published bore (0.755 in); and the orchestrator flagged the swerve mitered rail
as the most urgent open defect when it had already been fixed. Both were caught
by recomputing. Check the premise as carefully as the arithmetic.

## 2026-09-01, from the owner's own Onshape screenshots

Three findings, all from photographs the owner posted while the session ran.
The Onshape API is still exhausted, so every one was settled by transliterating
the builder into Python and drawing it.

**1. Solid corners on a hole-dense plate. Diagnosed, not a code change.**
`roomFor` refuses an interior node within `bossRadius + 0.50 * uEdgeMax` of a
hole (the `uBossClear` constant, applied in `roomFor`), and
`uEdgeMax = 2 * (pocket + rib) / sqrt(3)`, which
on 0.250 in 6061 edge on aggressive is 4.075 in. On the owner's 15 by 20 plate
with eleven holes those keep-outs cover **93.8 per cent** of the face, so
**zero** interior nodes are seeded: the mesh is 18 wall stations plus 11 hole
centres and nothing else. Every corner triangle then runs from a large boss to
the wall, its ring reaches across its own triangle, and the guard on
`rr[i] >= dot(lineN[jj], p[i]) - lineK[jj]`
throws the WHOLE triangle away. That single test caused 100 per cent of the
discards at all three presets. The same plate with four small holes has 32.6
per cent coverage, seeds seven interior nodes and discards nothing.

Sheets `plate_truss_corner_asym` and `plate_truss_corner_sym`. The model
reproduces the mechanism but UNDER-predicts the improvement the owner measured
when he moved a hole, so quote Onshape's numbers for that, not the model's.

**2. Isogrid tether stubs. FIXED, at `frcBar(needy[i].center`.**
The tether bar was drawn `L + s.rib` long, `L` being measured ALONG the tether
to the rib centre line, while the rib is a slab of half width
`h = rib / 2 + toolRad` measured ACROSS itself and `frcBar` gives a SQUARE end
perpendicular to the tether. The end's leading corner therefore sat
`rib * |cos| + h * |sin|` past the centre line and anything over `h` stood in
the next pocket. It fired at EVERY rib width, cutter and landing angle, 0.070
to 0.249 in, three stubs per boss; burying that corner would need a cutter 1.86
times the rib width and `frcMinWall` holds the rib at or above the cutter
diameter. The bar now ends on the centre line: corners at `h * |sin|`, inside
the slab always, and the joint is `h / |cos|`, longer than the overshoot it
replaced. Sheets `plate_spoke_land_before` and `plate_spoke_land_after`, checked
two independent ways (offset geometry and a raster of the same cut agree on the
stub area to four decimals). `_renders/_tools/model/patterns6.py`, at its `spokes.append` call,
was updated in the
same step.

**A four lens sweep for the same defect elsewhere. Nothing else found.**
Forty five bar-on-member sites were classified across all eleven tabs, twelve
were raised as suspects, and an independent verifier refuted every one with
arithmetic. The two nearest siblings are safe by construction and were checked
explicitly: the NONE-pattern tie, `frcBar(isl.center, u, L + grow.extension`,
divides its overshoot by
`sinArrival` through `frcWallExtension` and lands in a thick wall, and the
honeycomb tie, `frcBar(isl.center, u, tieLen`, penetrates by
`linkW = max(0.4 * s.rib, 0.05 in)`,
which is under `h` for every rib and cutter. So the isogrid tether was the only
one of its kind.

Two things the sweep raised that are now recorded in the source beside that call
rather than fixed:

* The containment proof depends on the tether and the rib being drawn the SAME
  width, `s.rib + 2 * toolRad`, at the lattice bars and at the tether.
  Nothing ties
  them together, and widening one alone brings the stub back silently.
* GRID and DIAGONAL use the same three spoke angles against families 90 degrees
  apart, so a cosine of 0.174 is reachable and the corner then clears the far
  edge by only 1.5 per cent of `h`. Any sliver that leaves is far under the
  cutter and `frcDropSlivers` takes it. Mitring the end would be worse: at that
  cosine the two corners land 5.7 `h` either side of the line.

**The stale backups still carry the defect.** `FRC Plate Geometry.txt.bak2`,
`.bak3`, `.bak5` and `.coverage-verified` all still contain `L + s.rib`.
Restoring or merging from any of them silently reinstates the stub. They were
left in place rather than deleted, because deleting the owner's backups is his
call.

**3. CONSERVATIVE threw on the eleven hole plate. DIAGNOSED, message improved.**
Not the truss. `opOffsetFace(context, id + "wall"` moves EVERY lateral face
of the cut tool by `-(s.wall + toolRad)`, which pulls the outline
IN and pushes every hole OUT by the same amount, so a hole and the outline
collide whenever the clear gap between them is under
`2 * (s.wall + toolRad)`. On this plate three holes are inside
that bound: the nearest, the 2.017 in bore at (13.297, 1.997), has 0.6945 in of
clear material against the 1.000 in CONSERVATIVE asks for. The two lighter
presets ask for 0.750 in and build, which is exactly the pattern in the owner's
screenshots; the symmetric four hole plate has no hole inside the bound at any
preset and builds at all three.

The wall itself fits perfectly well, twice over. What does not fit is a wall on
BOTH sides of the same gap, which is what offsetting both faces at once asks
for. So the throw is correct, but its message named only the wall. It now counts
the holes responsible and reports the gap they have against the gap the offset
needs, measured with `evDistance` from each hole's faces to the
outer faces, every measurement inside `try silent` so the failure
path cannot fail again. Sheet `plate_lighten_wallfit`, 7 checks.

## Done and verified

* **All 46 info panels** rewritten as flowing prose.
* **Core is clean**: an audit of every export except `frcDelaunay` found 0
  defects across roughly 480,000 cases.
* **`frcDelaunay` is mirror-covariant**; 36 of 36 symmetric layouts now give a
  symmetric mesh, 1400 of 1400 generic cases unchanged.
* **Lightening symmetry is solved**: 0 unmatched mirror pockets across all
  six preset/thickness rows, confirmed at the SHIPPED sizing by a second,
  independent transliteration.
  CORRECTION, worth reading before quoting older numbers: this was first
  reported as "down from 18, and removed area rose in every row". Those two
  figures came from `_renders/_tools/model/whyC.py`, whose `sizing()` predated the
  buckling-span-to-pocket conversion and so oversized pockets at 0.125 in.
  At the shipped sizing the 0-unmatched result holds, but the pre-rework
  configuration also reaches 0 there and removed area moves both ways, so
  neither of those two claims transfers. A scratch patcher, since gone, fixed the
  model; after it, whyC and truss6 agree pocket for pocket. A separately
  quoted "largest blob 2.38 to 0.79 sq in" is not reproducible from
  anything on disk and should not be repeated.
* **Dialogs are clean**: 334 defaults against bounds, 455 parameter ids against
  488 exported symbols, 145 declaration-order conditions, all pass.
* **30 tier-1 and tier-2 findings** from `_RENDER FINDINGS.md` triaged:
  19 fixed, 2 partly, 9 open, 0 wrong.
* Fixes applied: dead "Material name" control retired; three wrong tooltips
  corrected; Bolt Pattern reports its pilot bore; bumper **envelope** now
  includes the cover (it was 0.03 in undersize); Wheel panel flags a rim under
  the 0.090 in minimum wall; Elevator panel reports its overlap ratio.

## Outstanding work, in priority order

Every reference sheet check passes except one deliberate finding, across
20 generators and 198 sheets. The plate tab was rendered last and found
four more library defects; three are fixed and the fourth is left visible
on its sheet as a decision for the owner.

0. **The gusset skeleton arm erosion is the one open FAIL on a sheet, and
   it is a decision, not a bug to be quietly patched.** With lighten on,
   the default pass insets pocket edges by rib/2 from the arm CENTRELINES,
   so a 0.5 in arm finishes at 0.326 in beside one pocket and 0.15 in
   between two, and the Arm width dialog value becomes a dead letter. On
   the hull that behaviour is intended, since it pockets a solid web. On
   the skeleton the fix is either to inset from the arm EDGE or to leave
   lighten off by default, and both change what existing models build.
   Measured on `plate_gusset_skeleton`.
1. **Finding 3.2, swerve THROUGH_FACE reports every hole as drilled.** In
   `frcSwerveChassisBuild`, the THROUGH_FACE branch ends `wanted += size(pts);
   drilled += size(pts);` with no containment test, while the MK4 plate branch
   and the typed top branch both test `frcChassisInQuad`. So that pattern can
   never report a miss however far it spreads. The fix is a containment test
   against the rail FACE rectangle, and it was deliberately not attempted here:
   the face test needs the rail's vertical datum (is `pl.origin` the bottom of
   the rail?), and inferring it wrongly would reject valid holes, which is worse
   than the present over-reporting. Establish the datum first, then apply the
   same shape of fix the plate branch already has.
3. **The radio tie size disagreement.** The Electronics dialog default is
   `FRCTieSize.TIE_190`, which cuts a 0.210 in slot, but the VH-109 entry's own
   fastener line calls for 1/4 in cable ties, and a 0.250 in strap will not pass
   a 0.210 in slot. The geometry is correct for whichever tie is selected, so
   this is a question of which of the two should move. It is the owner's call,
   not a silent default change. Stated on `shop_electronics_radio`.
4. **The 3/4 in NITRA piston area.** `frcCylinderData` publishes 0.40 sq in for
   the 3/4 in bore where the bore geometry gives 0.4418, a 9.5 per cent gap;
   every other bore sits within 2.2 per cent. The table IS internally coherent
   (`ret100 = (area - rod area) x 100` holds to 0.03 lb on all five bores), so
   these are vendor effective areas rather than arithmetic, and the entry should
   be checked against the catalog rather than recomputed. Force scales directly
   with it. Stated on the cylinder sheets.
5. **The retaining ring groove.** The library cuts 0.460 in on a 1/2 in shaft;
   one source says 0.458 and another 0.468. Blocked on a Rotor Clip or Smalley
   print. Do not guess; `_REMAINING IDEAS.md` A6 says the same.
6. **The remaining open findings.** The two triage reports they were written
   in lived in a session scratchpad and are gone; the tally is kept here
   because it is all that survived. Across all 79: 50 FIXED, 4 PARTLY, 23 OPEN,
   2 STALE, 0 WRONG. The ones that would hurt a user most are 2.1 (the chassis
   typed pattern lands 8 of 24 holes at the shipped defaults) and 2.2 (the
   module stands 0.125 in proud of the frame face silently). 2.16 compares an
   arm reach against an extension limit that may be a different quantity
   entirely, so think before changing it. 2.5 is a vendor data gap with an
   escape hatch and 2.18 is arguably by design; both can stay open.
7. **Keep verifying sheets by eye**, one at a time, recomputing the numbers
   independently. That is how the shooter defect below was found.
8. **Refresh the documentation** once the code settles. `_PASTE INTO ONSHAPE.md`
   was refreshed on 2026-09-03: nine of its twelve line counts were wrong and
   its byte figures named the wrong largest tab. The handoff note it used to
   pair with lived outside this folder and is gone.

## Open findings cleared in the final pass

Eleven more of the 79 closed. Roughly 61 of 79 are now fixed.

* **2.1, the typed chassis pattern missing the rails.** At the shipped defaults
  the grid is 2 in across where a rail is about 1 in wide, so only the row that
  lands in the rail band is drilled, 8 holes of 24. The count was reported
  honestly but nothing said WHY. The panel now names the rail width and tells
  the user to narrow the spacing across it, matching the guidance the plate
  pattern already had.
* **2.2, the module standing proud of the frame face.** SDS dimension the MK4i
  steering axis 2.625 in from both outer edges and that figure lived only in a
  prose height string, so nothing compared it against the typed inset. At the
  shipped 2.5 in the module hangs an eighth of an inch over, silently. The
  figure is now a numeric field, read guardedly, and the panel warns with the
  amount. Only this module of twelve publishes the number, so only it carries
  the field: inventing it for the rest is what this library refuses to do.
* **3.16**, the truss reporting "Pocket capped" while the same panel suppresses
  the pocket figure. The note now names the capped value, so it is
  self-contained whatever the pattern does with that line.
* **3.20 and 3.21**, root diameters computed and never reported. The sprocket
  now prints its root, using the same expression the geometry cuts to,
  clearance and all; the pulley now prints its groove root for toothed belts,
  not just for round cord. That is the number that says whether a bore breaks
  into the grooves.
* **3.22**, the turret plate diameter. With the ring off, the one diameter the
  user typed never came back. Now printed.
* **3.24**, Hole RESIZE never saying which way it went. A bore larger than the
  target is driven smaller, which ADDS material. Counted and noted, and the
  panel says "resized" rather than "cut" in that mode.
* **3.25**, the swerve perimeter being the bounding rectangle without saying so.
  Now "Bounding perimeter".
* **3.26**, a module with no rail print or plate datum falling through to the
  typed pattern and reading exactly like a typed pattern. Now named.
* **4.9, 4.13, 4.14**, doc comments and a tooltip that lied: "every pocket
  reaches a wall" (most interior cells are landlocked), pitch circles "tangent"
  (the shipped 0.002 in allowance separates them), and "true involute flanks,
  not arcs" (a sampled polyline).
* **4.17**, the frame stock name zero pad covering one decade. Three now.

## A wrong claim in one of the reports, corrected

A sweep report written in a session scratchpad, now gone, stated that
`frcSlendernessLimit`'s shipped values
cannot be reproduced from standard E and Fy, quoting 12.9 for 6061 against a
shipped 16.3, and blocked an item on that basis. **It was wrong**, and the
correction is recorded here instead, because that file did not survive.

It applied the 0.85 margin twice: the documented coefficient
`0.85 * pi / (K * sqrt 12)` is 0.9636 at K = 0.8 and already contains the 0.85,
and 0.9636 x 0.85 is exactly the 0.819 the report used. It also took Fy as
276 MPa where the table is built on 241 MPa, the common 35 ksi minimum for
6061-T6. With the documented coefficient and 241 MPa the answer is 16.29
against a shipped 16.3, and all nine values reproduce the same way. The
reference sheet `plate_lighten_truss` prints a third independent confirmation.

**Do not "fix" the slenderness table on the strength of that report.** It is the
physics backbone of the lightening feature and it is sound.

## Still open, and why

* **3.2, swerve THROUGH_FACE reports every hole as drilled.** Needs a
  containment test against the rail FACE rectangle, which needs the rail's
  vertical datum established first. Guessing it would reject valid holes, which
  is worse than the present over-reporting.
* **2.16**, the arm pivot comparing a reach from the pivot against an extension
  limit that may be a different quantity. Think about the semantics before
  touching it.
* **2.5** is a vendor data gap with an escape hatch, **2.18** is arguably by
  design, **4.21** is informational.
* Four need something off a page nobody here has: the 3/4 in NITRA piston area,
  the retaining ring groove, the gusset skeleton arm decision, and the radio
  tie size. The last two are decisions rather than lookups.

## The owner's decisions, taken

Two were settled by the owner and are now in the code; two stand, for the
reasons below.

**1. Gusset skeleton arms: inset from the EDGE. DONE.** The lighten pass insets
the Delaunay cells from the lines joining boss CENTRES, so the inset distance is
what the arm keeps on each side. It used half the RIB, which measured from the
centreline and ate the arm from both sides: a 0.5 in arm came out 0.326 in
beside one pocket and 0.15 in between two, and the Arm width field meant nothing
whenever lighten was on. A skeleton now insets by half the ARM width, so the arm
finishes at the width that was asked for; a hull has no arms to protect and
keeps the rib measure, which is what it always wanted.

A consequence worth knowing, and it is the right one: on a skeleton the material
IS the arms, so once the pockets stop at the arm edge they fall entirely in the
web that is already open and remove nothing. The feature now says so rather than
cutting nothing in silence. Measured on `plate_gusset_skeleton`: narrowest arm
0.496 in against the 0.5 in asked, 0 pockets cut. That sheet used to be the one
deliberate failure in the set; it passes now.

**2. The VH-109 radio tie. DONE, without moving a shared default.** Vivid-Hosting
size the notches for a 1/4 in strap, and the tie ladder has no 1/4 in entry, so
the one that passes is the heavy duty 0.300 in. The 0.190 in default cuts a
0.210 in slot that a 1/4 in strap will not go through. The entry now carries
`tieMin : 0.25 * inch`, read guardedly the way `axisEdge` is, and the panel
warns when the selected tie is narrower than the part needs and names the tie
that fits. Changing the global default instead would have moved the slot on
every other component to fix one.

**3. Stable sub-ids, backlog B3. NOT DONE, and this one needs you.** Zero sites
use `setExternalDisambiguation`, so deleting one pocket renames every later one
and downstream sketches drop. The fix is real, but it is a refactor of the id
scheme across about ten tabs that CANNOT be compile-checked here, and changing
the scheme changes the identity of every face existing models already reference,
so the first paste after it breaks those sketches ONCE even as it protects them
for good afterwards. Two things argue for doing it soon anyway: the cost is
paid once and only grows as teams build on the library, and the paste document
already tells teams to link a released version rather than the workspace, which
is exactly the mechanism that makes such a change survivable. It is a migration,
not a defect fix, so it should be a deliberate, focused pass with its own
verification, not a tail-end edit.

**4. The arm pivot defaults. LEFT AS THEY ARE, deliberately.** With the sign
fixed the defaults correctly report 24 in of extension against a 12 in limit,
over it. That is TRUE of a 30 in arm pivoted 6 in inside the frame reference,
and the rule figure itself moved 16, 48, 12, 18, 12 in from 2022 to 2026, so no
single default passes every season. The library's pattern elsewhere, at 2.1 and
2.2, is to warn honestly at the defaults rather than bend them to silence the
warning, and a first-run warning that names a real conflict is worth more than a
clean panel that hides it.

## The last findings pass

Five read-only investigations, then edits applied with one writer per file.
Two of the five returned NO edits, which is the most useful thing they could
have done.

**Refuted, no change made:**

* **Pattern and mirror support.** 0 MISSING across all 46 builders: 36 bracket
  their work, 10 genuinely do not apply because they build nothing or only
  modify picked bodies. The backlog's "only one tab does this" was stale in the
  opposite direction from feared. Both count imbalances, Electrical 2/4 and
  Structure 5/6, are deliberate commented fallbacks where exactly one branch
  runs per regen.
* **COTS stand-in masses.** The backlog's central example does not exist:
  BEARINGS ARE NEVER DRAWN. Every consumer of the bearing table cuts a seat and
  none extrudes a body, and no body in any tab is named for one. A hypothetical
  solid ring would be +22 per cent, not the claimed +46, and neither figure is
  reproducible from anything on disk. The battery is a typed field; gearboxes
  are a plan report plus bore cuts. No data table carries a vendor weight at
  all, so the proposed remedy had nothing to read. And it would have been
  INVISIBLE anyway: frcWeighGroups supplies its own density and never reads a
  mass override, getProperty returns undefined inside a custom feature here, and
  Inspection weighs a typed number. Zero edits.

**Fixed:**

* **3.2, the THROUGH_FACE branch counting air as drilled.** The datum was
  settled: the frame plane is the rail bottom, corroborated by the rail extrude,
  the belly pan and the top-drill range. The subtlety that justified holding off
  is real, and is why a naive test would have rejected valid holes: the drill
  plane's sketch y axis is plus or minus pl.normal with a sign that VARIES BY
  CORNER, verified numerically for all four corners and both rail settings. The
  containment test now uses upSign = dot(cross(dpl.normal, dpl.x), pl.normal)
  and the same outer end stations that shaped the rail planform. At the shipped
  defaults the panel went from claiming "24 of 24" to "8 of 24, 16 missed".
  The most-missed NOTE now gives face-appropriate advice, since a face pattern
  misses vertically or off the rail ends, not across the rail width.
* **2.16, a sign error, not the apples-to-oranges pair I guessed.** The dialog
  defines pivotSetback as how far the pivot sits INSIDE the point extension is
  measured from, and armLength as pivot-to-tip, so extension past the reference
  is L - setback. The code added it, charging the arm twice for the same
  distance: 36 in at the defaults where the geometry stands 24 in past the
  reference. Both reach expressions now subtract, and the panel figure is named
  "Extension past the frame reference" so it says what it compares. The
  corrected defaults still read 24 against 12, over it, which is TRUE, so no
  default was bent to silence the warning.
* **1.5 residual.** The plateMissed note advised a band whose endpoints put hole
  CENTRES exactly on a rail face, where the boundary-inclusive test counts them
  drilled while the drill cuts them half off. It now points at the middle of the
  band and says what happens at the ends.
* **2.4 is no longer true** of current code; the refusal is diagnosable. The
  finding as written is WRONG of today's library.
* **Part names now carry their size.** Sprocket, pulley, gear, shaft and spacer
  bodies were named generically; an exported cut list read "Sprocket" rather
  than "16T #25 Sprocket". Five naming edits, verified for identifier scope at
  each site.

**That coverage gap is now closed.** `mech_swerve_face_pattern` draws the rail
face in ELEVATION, which is the plane the containment test works in; a plan
view cannot show whether a hole sits above or below the rail. At the shipped
defaults the pattern sits 1 in up a 2 in rail with rows 2 in apart, so its
rows land at -1, 1 and 3 in and only the middle one is on the face: 4 of 12
drilled on one face, 8 of 24 across the chassis. Nine checks, including that
a hole exactly on the top edge counts as inside, which is the case a naive
containment test gets wrong and the reason the fix carries a tolerance.

## Also resolved, later in the session

* **Honeycomb cells finished oversize and their webs undersize.** The cell is
  drawn on its CIRCUMradius but the cutter grows back on the INRADIUS, so
  subtracting the tool radius there shrank the inradius by only
  toolRad sqrt(3)/2 against a full toolRad of grow-back. Cells came out
  (2 - sqrt 3) toolRad too wide across the flats and the web between them ran
  0.22 in where the dialog asked 0.25 in. A claimed 2.417 in cell now builds at
  exactly 2.417. The circles branch never had it; its arithmetic cancels.
* **The tube's centred hole pattern reserved no end margin at all.** It fitted
  against L - pitch, which bought a 32nd hole by putting the end one 0.25 in
  from the end, half the vendor index its own indexed branch uses. It now fits
  against L - 2 startL and centres the leftover: 31 columns at 0.500 in,
  centring preserved.
* **The cell-pattern panel over-reported**, saying 28 cells where the part
  carries 14. Counting survivors needs a point-in-polygon test this file does
  not have, so the number is now stated honestly as cells LAID, with the reason
  at the site.
* **Hole RESIZE never said which way it went.** A bore already larger than the
  target is driven smaller, which ADDS material, and one undirected counter
  could not say so. It now counts them and notes it, and the panel says
  "resized" rather than "cut" in that mode.
* **The swerve perimeter is the bounding rectangle** and said so nowhere. On a
  corner-cut chassis the drawn rails total less. Now "Bounding perimeter".
* **Three doc comments and one tooltip that lied**, the class the next
  maintainer trusts: the truss claim that "every pocket reaches a wall" (most
  interior cells are landlocked), the gearbox claim that the pitch circles come
  out tangent (the shipped 0.002 in allowance separates them), and the gear
  panel's "true involute flanks, not arcs" (the flank is a sampled polyline).

## Resolved this session

Every reference sheet check now passes across all 14 generators. Nine checks
were failing at the start of this pass and five more surfaced after; of those,
seven were defects in the CHECKS and seven were defects in the LIBRARY.

Library defects found and fixed:

* **The dual-opposed shooter ignored its second wheel.** The feature builds the
  opposed wheel but computed `iw` from the driven set alone and divided by
  `4 * iw`, omitting the opposed wheel's inertia referred through the gearing as
  G squared. Exit speed came out 36.4 ft/s where an independent five-unknown
  impulse solve gives 47.8, and the drop 47.9 per cent against 31.5.
* **The wire bundle was geometrically impossible.** `frcBundleDiameter` used
  `d sqrt(n) 1.12`, an asymptotic packing law that at real counts sits BELOW the
  minimum enclosing circle: two 0.170 in wires need 0.340 in and it returned
  0.269. The bundle body is what the clearance check reads, so it reported room
  that was not there. Now the published optimal packing ratios up to twelve, the
  hexagonal density beyond, and the same 1.12 looseness allowance on top.
* **Belt Path applied no pitch-circle correction to chain.** `pld` is set only
  in the belt branch, so a sprocket picked at its outside edge came in 0.0627 in
  oversize on a 16 tooth #25, about 1.6 links over a two-sprocket run. A prior
  reviewer called this unfixable without a tooth count the dialog never asks
  for; it is fixable in closed form, because ANSI B29.1 gives
  `Do = P (0.6 + cot(180 / N))`, so `cot(pi / N) = 2 r / P - 0.6` inverts to
  `N = pi / atan(1 / that)` and the pitch radius follows exactly. Added as
  `frcSprocketPitchRadius`, which returns the radius unchanged when the pick
  cannot be a sprocket for that chain. Cord is deliberately left alone: its
  neutral axis needs a cord diameter this dialog does not ask for.
* **The bumper ENVELOPE was built without the cover**, because `wantCover` is
  `output == ALL` and is false by construction inside the envelope branch. The
  one body whose job is to mark the outermost extent stood 3.25 in where the
  bumper stands 3.28.
* **Wire Path reported the tie spacing it asked for, not the one it built.**
  `frcPathStations` divides the usable run into a whole number of equal gaps, so
  the gap is always at or above the target; the panel said "about 2.29 in" where
  the part measures 2.44. It now derives the figure from the layout.
* **Arm Pivot computed an as-drawn reach and never printed it**, while the
  comment above it promised it would be reported "the way the gravity torque
  line reports level and as drawn", which that line does.
* **The Wheel hub bolt-circle guard required no margin**, passing at 0.0595 in
  of rim against the 0.090 in this library treats as a minimum wall. Now noted
  in the panel, matching how COTS Pattern flags a thin bearing-plate web.
* **The Elevator dropped its overlap ratio** in the prose rewrite. It is
  derived, not a dialog echo, and the defaults sit one point above the floor.
* **A bearing block comment misstated its own arithmetic**, claiming the 1.5 in
  circle falls 0.00025 in short of the 0.090 in floor. It meets it exactly:
  0.750 - 0.098 - 0.562 = 0.090. The comment had halved the radial allowance a
  second time.
* Earlier: the dead "Material name" control retired, three wrong tooltips
  corrected, Bolt Pattern now reports the pilot bore it cuts.

Checks that were themselves wrong, corrected rather than believed:

* Rounding 5.03 to the nearest 1/16 is 5.0000, not 5.0625.
* The dogbone overcut check carried an extra factor of 0.7071 and produced the
  sixty degree answer for a ninety degree corner.
* The cylinder area check tested published vendor areas as though they were bore
  geometry. The table is internally coherent: `ret100 = (area - rod area) x 100`
  holds to 0.03 lb on all five bores.
* The NEO hole-count check tested the entry against a drawing the entry
  explicitly says it cannot match, and says why.
* The Bolt Pattern pilot check had the boss and the vendor bore the wrong way
  round.
* The bearing web and arm reach checks lagged fixes made to the library.

## A trap worth remembering

Adding `frcSprocketPitchRadius` I first pasted it INSIDE `frcBeltPathBuild`.
FeatureScript has no nested function definitions, but a helper pasted inside
another function still BALANCES, so the bracket counts could not see it and
`verify.py` reported the file clean. `verify.py` now has a `nested_exports`
check that walks the same code, comment and string states and flags any
`export` at non-zero brace depth; it is self-tested against a nested export, a
string containing the word export, and a commented-out one.

The same session also collapsed a `
` escape into a real newline inside its
own Python while writing that very check. That is the third time this escape has
bitten in this project. Build the backslash with `bytes([92])` when writing
through a shell heredoc.

