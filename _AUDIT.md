# FRC FeatureScript Library — Final Static Audit

**Date:** 2026-08-28
**Scope:** 11 code tabs (`READ ME.txt` excluded as documentation), 45 features, 21,296 lines.
**Method:** Static analysis only. The Onshape connection is down; nothing was compiled or
regenerated. Every check below was run by script over all 11 files, not by reading.
**Verdict:** No blocking defects. No serious defects. 7 minor items, none of which affect
compilation or behaviour.

---

## Findings by severity

| Severity | Count |
|---|---|
| BLOCKING (will not compile, or throws at regeneration) | **0** |
| SERIOUS (compiles, but misbehaves) | **0** |
| MINOR (house rules, consistency, dead code) | **7** |

### The five most urgent items

All five are MINOR. There is nothing above MINOR in this library.

1. `FRC Core.txt:1470` — tooltip 130 chars, limit 110. In `frcBorePredicate`, so it is shown by six features.
2. `FRC Core.txt:1476` — tooltip 115 chars, limit 110. Same predicate, same six features.
3. `FRC Hardware Geometry.txt:1027` — `frcInspectionBuild` report reaches 14 lines worst case, limit 10.
4. `FRC Core.txt:380`, `FRC Core.txt:559`, `FRC Plate Geometry.txt:176` — three exported functions nothing calls.
5. Trailing-newline inconsistency across the 11 files (4 end with CRLF, 7 do not).

---

## BLOCKING

**None.**

Every check whose failure would stop compilation or throw at regeneration passed:

- No unresolved identifier anywhere in the library.
- No cross-tab reference the import graph forbids.
- No parameter read that the precondition does not declare.
- No `Enum.MEMBER` reference that is not a member of that enum.
- No enum-keyed map lookup that can miss.
- No unbalanced delimiter, unterminated string, or unterminated block comment.
- No `const` reassignment.
- No value-returning function that can fall off the end.
- No import-version conflict.

---

## SERIOUS

**None.**

---

## MINOR

### M1. Two tooltips exceed the 110-character limit

| File | Line | Length | Text |
|---|---|---|---|
| `FRC Core.txt` | 1470 | 130 | "MAXSpline is the REV pattern and SplineXL the WCP one. SplineXS 15T is the Kraken and NEO 2.0 shaft. Falcon 500 is the 14T spline." |
| `FRC Core.txt` | 1476 | 115 | "Named by outside diameter, with the shaft bore beside it. 1.375 in is a flanged bearing, 0.750 in a bronze bushing." |

Both live in `frcBorePredicate`, which Gear, Pulley, Sprocket, Spacer, Shaft and Wire Path
all pull in, so both are visible in six dialogs.

**Fix.** Line 1470: cut the Falcon clause to "Falcon 500 is 14T." (119) or drop
"the WCP one" and keep the rest (117); to land under 110, use
`"MAXSpline is REV, SplineXL is WCP. SplineXS 15T is the Kraken and NEO 2.0 shaft. Falcon 500 is 14T."` (99).
Line 1476: drop "with the shaft bore beside it" — the enum labels already carry the bore —
giving `"Named by outside diameter. 1.375 in is a flanged bearing, 0.750 in a bronze bushing."` (85).

These are the only 2 of 210 `"Description"` strings in the library over the limit.

### M2. Seven report panels exceed 10 lines

Counted at worst case: every conditional line in the panel firing at once. In the common
case each of these renders shorter.

| File | Line | Builder | Worst-case lines |
|---|---|---|---|
| `FRC Hardware Geometry.txt` | 1027 | `frcInspectionBuild` | 14 |
| `FRC Manufacturing Geometry.txt` | 102 | `frcDriveBuild` | 12 |
| `FRC Motion Geomtery.txt` | 379 | `frcPulleyBuild` | 12 |
| `FRC Structure Geometry.txt` | 270 | `frcBumperBuild` | 12 |
| `FRC Fabrication Geometry.txt` | 179 | `frcFingerJointBuild` | 11 |
| `FRC Mechanism Geometry.txt` | 1593 | `frcShooterBuild` | 11 |
| `FRC Mechanism Geometry.txt` | 2524 | `frcPneumaticBuild` | 11 |

**Fix.** `frcInspectionBuild` is the one worth touching: its perimeter and height checks each
spend a second continuation line on the comparison (`FRC Hardware Geometry.txt:1043-1046` and
`1047-1050`). Folding each pair onto one line the way the weight line already does takes the
panel from 14 to 12. The other six are one or two lines over and can stand.

The remaining 38 panels are within limits. Panel-height distribution across all 45:
1 line ×1, 2 ×2, 3 ×4, 4 ×5, 5 ×4, 6 ×5, 7 ×5, 8 ×4, 9 ×6, 10 ×2, 11 ×3, 12 ×3, 14 ×1.

### M3. Three exported functions nothing calls

| File | Line | Function |
|---|---|---|
| `FRC Core.txt` | 380 | `frcBearingPartName(b is FRCBearingOD) returns string` |
| `FRC Core.txt` | 559 | `frcRefindFace(context, bodyQ, pl)` |
| `FRC Plate Geometry.txt` | 176 | `frcPerimeterAnchors(context, outerFaces, ...)` |

**Fix.** Leave them if they are intended as library API for team use; they cost nothing at
runtime. If they are leftovers, delete all three. Do not delete `frcRefindFace` without
checking first — it is the kind of helper a tracking-query fix reaches for, and the Plate tab
already carries comments about tracking queries going stale.

### M4. Three exported bounds constants nothing references

| File | Line | Constant |
|---|---|---|
| `FRC Core.txt` | 1459 | `FRC_RACKLEN_BOUNDS` |
| `FRC Manufacturing Geometry.txt` | 809 | `FRC_ROUNDTO_BOUNDS` |
| `FRC Structure Geometry.txt` | 1164 | `FRC_STAGES_BOUNDS` |

`FRC_STAGES_BOUNDS` is the likely residue of the Gearbox rework: Gearbox now carries a
`twoStages` boolean and derives `stages` in the Toolkit body, so an integer stage-count bound
has no caller.

**Fix.** Delete all three, or wire `FRC_RACKLEN_BOUNDS` into the Gear feature's rack-length
parameter if that parameter is currently bounded by something more generic. Deleting an
exported constant is safe here — the sweep below confirms nothing outside these three
declarations names them.

### M5. Trailing-newline inconsistency

Four files end with a final CRLF; seven do not.

| Ends with CRLF | No final CRLF |
|---|---|
| `FRC Hardware Geometry.txt` | `FRC Core.txt` |
| `FRC Manufacturing Geometry.txt` | `FRC Electrical Geometry.txt` |
| `FRC Mechanism Geometry.txt` | `FRC Fabrication Geometry.txt` |
| `FRC Shop Geometry.txt` | `FRC Motion Geomtery.txt` |
| | `FRC Plate Geometry.txt` |
| | `FRC Structure Geometry.txt` |
| | `FRC ToolKit.txt` |

All 11 begin identically with `FeatureScript 3044;`. No effect on compilation.

**Fix.** Pick one and apply it to all 11 before pasting. Either is fine for Onshape.

### M6. `FRC_POUND` and `frcFit` are duplicated in Mechanism

| Symbol | Exported from | Duplicated (file-local) in |
|---|---|---|
| `FRC_POUND` | `FRC Hardware Geometry.txt:221` | `FRC Mechanism Geometry.txt:24` |
| `frcFit` | `FRC Hardware Geometry.txt:323` | `FRC Mechanism Geometry.txt:27` |

**Not a defect.** Mechanism imports only Core and Motion, so Hardware's exports are not
visible to it, and the local copies are correctly non-exported — no file in the library can
see both, and there is no shadowing. The comment at `FRC Mechanism Geometry.txt:22-23`
documents the choice. The two `frcFit` bodies and the two `FRC_POUND` values are currently
character-identical.

**Fix.** None required. Recorded as a drift hazard: if the column padder or the pound
constant is ever changed in Hardware, `FRC Mechanism Geometry.txt:24` and `:27` must change
with it. Moving both into Core would remove the hazard, since every tab imports Core.

### M7. Only 2 of 45 features carry a `"Feature Type Description"`

Present on Belt and Chain (`FRC ToolKit.txt:364`) and Parts (`FRC ToolKit.txt:1845`).
The other 43 have none.

**Fix.** Either add one to all 45 or remove the two, so the custom-features menu reads
consistently. Not a rule violation as stated; flagged for consistency only.

---

## CLEAN — what was checked and found sound

### 1. Unresolved symbols — CLEAN

Built the definition set across all 11 tabs: `export function`, `export predicate`,
`export enum` and their members, `export const`, `export type`, plus every non-exported
top-level definition per file. **803 top-level names**, 84 enums, 378 enum members.

- Every `frc*`, `FRC_*` and `FRC[A-Z]*` identifier used in the library resolves. **0 undefined.**
- **162 `FRC_` constants defined, 162 referenced, 0 dangling.** The three constants deleted
  from Structure and the two from Hardware left no references behind.
- **0 cross-tab references the import graph forbids**, after correcting the graph (below).
- The `motorGuard` → `cornerCovers` and `guardThickness` → `cornerCoverThickness` renames are
  complete. No occurrence of either old name survives. Both new names are declared
  (`FRC ToolKit.txt:2663`, `:2668`), defaulted (`:2694`, `:2695`) and read
  (`FRC Mechanism Geometry.txt:1347`, `:1364`, `:1369`).

**Correction to the audit brief.** The brief states nine geometry tabs import only FRC Core.
Two of them import a second tab as well, and this is correct and declared:

```
FRC Manufacturing Geometry.txt:4   export import("82d221137a697995b51d4734", ...)
FRC Mechanism Geometry.txt:4       export import("82d221137a697995b51d4734", ...)
```

`82d221137a697995b51d4734` is FRC Motion Geometry — Manufacturing uses `frcBeltData` and
`frcChainData` from it (lines 144, 153, 457, 465) and Mechanism uses `frcGearOutline`
(lines 1886, 1971). FRC Motion Geometry itself imports only Core, so there is no cycle.
The true graph is: Core imports nothing from the library; Motion imports Core; Manufacturing
and Mechanism import Core and Motion; the other six geometry tabs import Core; ToolKit
imports all ten. Under that graph there are zero violations.

**Import versions are consistent.** Core is imported at version `578eb867bbdba7daf29ca549` by
all ten importers; Motion at `da6966cb2fb984d08cceddd0` by all three. No tab pulls two
versions of the same module. `FRC Plate Geometry.txt:3` additionally imports
`onshape/std/modifyFillet.fs`, which is required — `opModifyFillet` and `ModifyFilletType`
are not in `common.fs`, and Plate is the only tab that uses them.

### 2. Parameter contract, ToolKit to builders — CLEAN

`frcDefinition()` (`FRC ToolKit.txt:19-38`) was read first and its aliases applied throughout:

```
partMaterial -> material    partLength -> length    beltLength -> length
cubeSize     -> size        drivePlane -> plane     floorFace  -> floor
flipSide     -> flip        chamferSize-> chamfer
```

Preconditions were expanded through the shared predicates they call (`frcWeighPredicate`,
`frcBorePredicate` — 8 call sites), defaults expanded through `mergeMaps(CONST, {...})`
(`FRC_WEIGH_DEFAULTS`), and injected keys picked up from `mergeMaps(definition, {...})` in the
feature bodies. Builder reads were followed transitively through every call that passes the
definition map along, including through renamed parameters and `const d = definition` aliases.

Across all 45 features:

| Check | Result |
|---|---|
| Read but never declared (runtime undefined) | **0** |
| Declared but never read (dead UI) | **0** |
| Declared without a default | 76, **all of them Query parameters** |
| Default key with no declaration | **0** |

The 76 undefaulted parameters were type-checked individually: every one is
`definition.X is Query`, which correctly takes no default in FeatureScript. Zero non-Query
parameters lack a default.

**`perimeterLimit` comes out clean, as expected.** It is declared and defaulted in all three
features that use it — Bumper (`FRC ToolKit.txt:590`, default `110 * inch` at `:599`),
Inspection (`:1588`, default `120 * inch` at `:1610`) and Swerve Chassis (`:2535`, default
`110 * inch` at `:2682`). The defensive read in Structure is genuine and correct:

```
FRC Structure Geometry.txt:296-297
    const perimLimit = (definition.perimeterLimit is ValueWithUnits)
        ? definition.perimeterLimit : FRC_ROBOT_PERIM_MAX;
```

No feature reaches that fallback in practice, because `frcBumperBuild` is called only by
Bumper, which declares the field. The guard is belt-and-braces, not a defect.

There are **no other defensive reads with fallbacks** in the library — the read-but-undeclared
set is empty, so the deliberate-versus-defect distinction has nothing else to sort.

### 3. Enum integrity — CLEAN

- **84 enums, 378 members.** Every `SomeEnum.VALUE` reference in the library is a real member
  of that enum. **0 bad references.**
- **29 enum-keyed map literals** across the library. 27 are exhaustive. The two partial ones
  are both in `frcCotsPatternData` (`FRC Shop Geometry.txt:508`) and both are safe:

  - `FRC Shop Geometry.txt:579` — `const motors = {…}` covers 7 of 13 `FRCCotsPattern`
    members, and is read through a guard: `if (motors[p] != undefined)` at line 666-1.
    A miss returns `undefined` and falls through instead of throwing.
  - `FRC Shop Geometry.txt:666` — `const t = {…}[p];` covers 4 of 13 and is **unguarded**,
    but it is unreachable for the other 9. The function returns early for `MK4` (line 511)
    and `CIM_FACE` (line 534), and the guarded `motors` block returns for the 7
    motor/gearbox members (line 660). 1 + 1 + 7 + 4 = 13. The dispatch is exhaustive by
    elimination, so `t[p]` can only ever be indexed by one of its own four keys.

  This is the exact pattern that produced the earlier blocking defect, and it does not recur.

- **The `frcMaterialLabel` fix is correct.** `FRC Hardware Geometry.txt:260-263` now forwards
  to Core:

  ```
  export function frcMaterialLabel(m is FRCMaterial) returns string
  {
      return frcMaterialName(m);
  }
  ```

  `frcMaterialName` (`FRC Core.txt:662`) maps all **11 of 11** `FRCMaterial` members,
  `FOAM_NOODLE` and `WIRE_BUNDLE` included. The three other `FRCMaterial`-keyed maps in Core
  (lines 68, 97, 664, 685) are all 11/11 as well. Nothing can miss.

- **23 enum members are never referenced by name.** Every one was traced to its dispatch and
  every one is covered by an `else` arm, a ternary's false branch, or a terminal `return`.
  Verified individually; the two non-obvious cases:

  - `FRCChassisHoles.THROUGH_TOP` — a 4-member enum whose chain is
    `useVendor && railEnd` → `useVendor && plateDatum` → `== THROUGH_FACE` → `else`
    (`FRC Mechanism Geometry.txt:1171-1189`). The final `else` is the typed top pattern, which
    is exactly what `THROUGH_TOP` means. Covered.
  - `FRCSwerveModule.CUSTOM` — 21 comparison sites in `frcSwerveModuleData`
    (`FRC Mechanism Geometry.txt:611`), ending in an unconditional `return`. Covered.

  There are **no `switch` statements anywhere in the library**, so if-chains are the only
  dispatch form and all of them terminate.

- **All 136 value-returning functions end in an unconditional `return` or `throw`.** None can
  fall off the end and return nothing against a typed return.

### 4. Computed feature-name tokens — CLEAN, and exactly four

Exactly four templates carry a `#token`, and the pairing is one-to-one with the four
`setFeatureComputedParameter` calls in the library. No orphans in either direction, no
collisions with a `definition.<id>` in the same precondition.

| Feature | Template | Token | Set by |
|---|---|---|---|
| Frame (`FRC ToolKit.txt:1180`) | `Frame - #members members` | `members` | `FRC Structure Geometry.txt:814` in `frcFrameBuild` |
| Gusset (`FRC ToolKit.txt:1393`) | `Gusset - #bolts holes` | `bolts` | `FRC Plate Geometry.txt:2003` in `frcGussetBuild` |
| Lighten (`FRC ToolKit.txt:1614`) | `Lighten - #ribs ribs` | `ribs` | `FRC Plate Geometry.txt:1387` in `frcLightenBuild` |
| Tube (`FRC ToolKit.txt:2698`) | `Tube - #tubes tubes` | `tubes` | `FRC Plate Geometry.txt:1909` in `frcTubeBuild` |

All 45 features have a `"Feature Name Template"`; the other 41 are literal.

### 5. Duplicate and shadowed definitions — CLEAN

- **0 real duplicates within a file.** One name is defined twice in `FRC Core.txt`:
  `frcPrintedDensity` at line 152 (4 arguments) and line 171 (3 arguments). Arities differ,
  so this is a legal FeatureScript overload, not a redefinition.
- **0 names exported by two tabs.**
- **0 enum type names defined twice.**
- **0 shadowings** — no local definition anywhere carries a name that an imported tab exports.
  The two names defined in more than one file (`FRC_POUND`, `frcFit`) are covered under M6:
  no file in the library can see both copies.
- 27 enum member names are reused across different enums (`NONE` in 12 enums, `CUSTOM` in 11,
  and so on). Members are scoped to their enum in FeatureScript, so this is legal and
  intentional.

### 6. Structural sanity — CLEAN

**Delimiters.** Balanced and correctly nested in all 11 files, with comments and string
literals stripped first:

| File | `{}` | `()` | `[]` |
|---|---|---|---|
| FRC Core.txt | 349/349 | 711/711 | 251/251 |
| FRC Electrical Geometry.txt | 189/189 | 577/577 | 289/289 |
| FRC Fabrication Geometry.txt | 159/159 | 421/421 | 123/123 |
| FRC Hardware Geometry.txt | 145/145 | 571/571 | 61/61 |
| FRC Manufacturing Geometry.txt | 153/153 | 451/451 | 95/95 |
| FRC Mechanism Geometry.txt | 466/466 | 1547/1547 | 265/265 |
| FRC Motion Geomtery.txt | 205/205 | 552/552 | 51/51 |
| FRC Plate Geometry.txt | 359/359 | 1151/1151 | 471/471 |
| FRC Shop Geometry.txt | 164/164 | 381/381 | 92/92 |
| FRC Structure Geometry.txt | 268/268 | 845/845 | 223/223 |
| FRC ToolKit.txt | 985/985 | 781/781 | 12/12 |

**No unterminated string or block comment** in any file.

**Pattern transforms.** 35 functions use `getRemainderPatternTransform`; all 35 pair it with
at least one `transformResultIfNecessary` in the same function. 35 remainder calls, 38
transform calls. The three functions with two transform calls are the allowed
several-exit-branches case, and each uses an explicit `moved` flag so exactly one fires:

| File | Function | Remainder | Transforms | Guard |
|---|---|---|---|---|
| `FRC Electrical Geometry.txt` | `frcElectronicsBuild` | 324 | 441, 451 | `moved = true` at 442; `if (!moved && madeKeepout)` at 450 |
| `FRC Electrical Geometry.txt` | `frcWirePathBuild` | 937 | 1098, 1109 | `moved = true` at 1099; `if (!moved && madeBundle)` at 1108 |
| `FRC Structure Geometry.txt` | `frcGearboxBuild` | 1368 | 1446, 1464 | `moved = true` at 1447; `if (!moved)` at 1463 |

Coverage spans 9 tabs (every geometry tab), matching the brief's "roughly ten tabs and
thirty-five features" — 35 functions exactly.

**Bytes.** All 11 files: pure CRLF (0 bare LF, 0 lone CR), pure ASCII (0 bytes above 0x7F),
0 tab characters. All 11 open with `FeatureScript 3044;`. Final-newline handling is
inconsistent — see M5.

**Other compile-error classes checked and clean:** 0 `const` reassignments (scope-aware walk
of every function body); 0 `regenError` parameter ids that are not parameters of the calling
feature (197 ids checked); 0 precondition parameters missing an annotation (616 checked).

### 7. House rules — 2 violations, both minor

| Rule | Checked | Violations |
|---|---|---|
| Field labels ≤ 30 chars | 628 `"Name"` strings in ToolKit | **0** |
| Dropdown options ≤ 24 chars | 378 enum member labels | **0** |
| Tooltips ≤ 110 chars | 210 `"Description"` strings | **2** (M1) |
| Report lines ≤ 60 chars | 45 panels | **0** |
| Report panels ≤ 10 lines | 45 panels | **7** (M2) |
| No em-dash | all 11 files | **0** |
| No "simply" | all 11 files | **0** |
| No minimising "just" | all 11 files | **0** |
| Query parameters have `"Filter"` or `ALWAYS_HIDDEN` | 76 Query parameters in ToolKit | **0** |
| Exactly 45 `"Feature Type Name"` entries | — | **45** ✓ |
| Alphabetical | — | ✓ (verified case-insensitively, Arm Pivot → Wire Path) |
| Each followed by a `defineFeature` | — | ✓ (45 annotations, 45 `defineFeature` calls, no duplicates) |

Notes on the two text rules:

- **Report line width is clean.** Two independent methods agree. A branch-aware
  reconstruction of all 45 panels puts the widest real literal line at 56 characters. A
  second, method-independent sweep — measuring every complete line that sits between two
  `\n` inside a single string literal — found **0 lines over 60** across the whole library.
  Earlier drafts of this check reported false positives at `frcSpacerBuild`
  (`FRC Motion Geomtery.txt:922`) and `frcBeltPathBuild` (`FRC Manufacturing Geometry.txt:428`);
  both were artefacts of concatenating mutually exclusive `if`/`else` arms, and both were
  confirmed clean by reading the source.
- **The single "just"** is `FRC Motion Geomtery.txt:191`, in a comment: "Measured off the
  outline that was just drawn". That is temporal, not minimising. No violation.
- The 370 `--` sequences are ASCII section-divider rules in comment banners, not em-dashes.
  No `U+2014` appears anywhere; the files are pure ASCII.

### 8. Feature-to-builder coverage — CLEAN, 45 to 45

All **45 features resolve to an existing builder**, and **every builder is reached by exactly
one feature**. No orphans in either direction, and no builder shared between two features.

| | |
|---|---|
| Features declared | 45 |
| Features with no builder | **0** |
| Builders defined in geometry tabs | 45 |
| Builders never reached | **0** |
| Builders used by more than one feature | **0** |

Arm Pivot→`frcArmPivotBuild`, Battery Mount→`frcBatteryMountBuild`,
Bearing Block→`frcBearingBlockBuild`, Belt and Chain→`frcDriveBuild`,
Belt Path→`frcBeltPathBuild`, Bolt Pattern→`frcPatternBuild`, Bumper→`frcBumperBuild`,
Center of Gravity→`frcCenterOfGravityBuild`, Climber→`frcClimberBuild`,
COTS Pattern→`frcCotsBuild`, Design Constants→`frcConstantsBuild`,
Dogbone Corners→`frcDogboneBuild`, Drivetrain→`frcDrivetrainBuild`,
Electronics→`frcElectronicsBuild`, Elevator→`frcElevatorBuild`,
Extrude Individual→`frcExtrudeIndividualBuild`, Fillet Edges→`frcFilletEdgesBuild`,
Finger Joint→`frcFingerJointBuild`, Frame→`frcFrameBuild`, Gear→`frcGearBuild`,
Gearbox→`frcGearboxBuild`, Gusset→`frcGussetBuild`, Hole→`frcHoleBuild`,
Insert Pocket→`frcInsertPocketBuild`, Inspection→`frcInspectionBuild`,
Lighten→`frcLightenBuild`, Mate Connectors→`frcMateConnectorsBuild`,
Measure→`frcMeasureBuild`, Origin Cube→`frcOriginCubeBuild`, Parts→`frcPartsBuild`,
Pneumatic Cylinder→`frcPneumaticBuild`, Pulley→`frcPulleyBuild`, Roller→`frcRollerBuild`,
Shaft→`frcShaftBuild`, Sheet Layout→`frcSheetLayoutBuild`, Shooter→`frcShooterBuild`,
Slot→`frcSlotBuild`, Spacer→`frcSpacerBuild`, Sprocket→`frcSprocketBuild`,
Swerve Chassis→`frcSwerveChassisBuild`, Tube→`frcTubeBuild`, Turret→`frcTurretBuild`,
Weight Budget→`frcWeightBuild`, Wheel→`frcWheelBuild`, Wire Path→`frcWirePathBuild`.

The `READ ME.txt` feature list is consistent: all 45 feature names appear in it, and it
states the count as 45.

---

## Confidence that this library compiles as it stands

**High.** I expect all 11 tabs to compile, and I expect all 45 features to regenerate without
throwing on their default parameter values.

What that confidence rests on. Every failure mode that a FeatureScript tab can hit at parse
or load time was checked mechanically across all 11 files and all came back empty: unresolved
identifiers, forbidden cross-tab references, unbalanced delimiters, unterminated literals and
comments, duplicate definitions in a scope, `const` reassignment, and conflicting import
versions. The runtime-throw classes that this library has actually shipped before were
checked specifically and are sound: every enum-keyed map is either exhaustive or provably
exhaustive by elimination, every value-returning function terminates in a `return` or
`throw`, and no builder reads a parameter its precondition does not declare. The two edits
most likely to have broken something — the five deleted constants and the two renamed
parameters — leave zero dangling references. The `frcMaterialLabel` fix that motivated this
pass is correct and its target covers all 11 material members.

What the confidence does not cover, and why it cannot. Static analysis cannot see geometry.
Nothing here says that a pocket lands on the plate, that a boolean subtraction finds a target,
that a query resolves after an operation replaces the face it was tracking, or that a value
computed at regeneration falls inside its declared bounds. Those are the failures that need
Onshape, and they are what open task #21 exists for. The library is in a state where pasting
it in is a reasonable next step; the regeneration sweep is still required before anyone
should trust it on a real robot.

Two smaller caveats on this audit's own reach. First, the import graph was inferred from the
declared `export import` statements and from which tab defines each symbol, not from the
Onshape tab ids themselves — I could not query the document. The inference is unambiguous
(Manufacturing and Mechanism import exactly one non-Core tab, and use exactly Motion's
symbols), but it is an inference. Second, report panel heights are worst-case counts assuming
every conditional line fires; the real panels are usually shorter, so M2 may overstate.

---

*Checks run: 21 scripted passes over 11 files, 21,296 lines, 803 top-level definitions,
84 enums, 378 enum members, 45 features, 45 builders, 616 declared parameters, 162 bounds
constants, 210 tooltips, 628 field labels, 45 report panels.*
