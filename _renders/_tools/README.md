# How the reference sheets are made

The Onshape API allocation runs out (2,608 of 2,500 used on 2026-08-30, resets
2026-10-13), and without it nothing in this library can be built, regenerated or
photographed. These scripts are the substitute, and they live here rather than in
a session scratchpad because the previous set of renders was made by a session
whose scripts did not survive, so the whole harness had to be rebuilt from a
screenshot.

The method: transliterate a builder's geometry into Python, draw what it
produces, and state on the same sheet what the feature CLAIMS to produce. A
defect shows up as a disagreement between the two.

These are reference documents, meant to be handed to someone, not internal
scratch output.

## renderkit.py

One `Sheet` per configuration, saved as a 2080 by 1560 PNG into the folder above.

    import sys; sys.path.insert(0, r"...\_renders\_tools")
    from renderkit import Sheet, report

    s = Sheet("plate_lighten_truss",
              "FRC Lighten, truss between holes",
              "12 by 8 by 0.25 in plate, 8 holes, otherwise dialog defaults")
    s.legend_default()
    s.poly(outline, fill="part")
    for p in pockets:
        s.poly(p, fill="cut", edge="pocket")
    s.dim_h(0, 12, -0.7, "12 in")
    s.scalebar(2)
    s.caption("Sizes come from frcAutoSizing at 0.25 in 6061 ...")
    s.expect("Pocket count", 34, len(pockets))
    s.save()

Units are inches and y is up, as in the FeatureScript.

### expect() is the whole point

`expect(what, want, got)` records a check. `want` is what the FEATURE claims;
`got` is what the drawing actually MEASURED. Failures print in the verification
table in orange, and `report(sheets)` prints them to the console.

A check that recomputes the same expression twice proves nothing. Derive the
wanted value from first principles, from the published standard, or from the
vendor's drawing, independently of the line of code that produced it. And check
the premise as carefully as the arithmetic: a check once read `pilot clears the
0.755 in boss`, when 0.755 in was the vendor's published BORE and the boss was
0.750 in. The check failed, the sheet cried defect, and the library was right.

### What the harness guarantees

* **No check is ever dropped.** An earlier version stopped drawing once it ran
  out of room, so a failing check could vanish from a sheet while still being
  counted in the totals. Leading is now computed from the content and every row
  is drawn.
* **Nothing is clipped or overlapped.** The page is laid out from its content:
  title, subtitle and legend are measured from the top, the caption and
  verification table from the bottom, and the drawing gets what is left.
* **The part is centred.** The view centres horizontally on the drawn geometry
  rather than on the union of geometry and annotation, so a scale bar or a note
  on one side does not push the part off centre.
* **A dimension label never masks its own arrow**, and never gets struck
  through by a centre line running behind it.

### House style, enforced in the harness

You do not have to remember these; `Sheet` applies them. They are written down
so a generator written later reads the same as one written earlier.

* **Titles** are Title Case, and `title_case()` preserves acronyms, part
  numbers, and units: `HTD`, `MK4i`, `roboRIO`, `#25`, `20DP`, `T5/T10`, `16 T`.
* **Subtitles, captions, notes, legend labels and check names** are sentence
  case. Only the opening letter is touched, because the rest of the string
  routinely carries part numbers and acronyms that must not be recased.
* **Units fold into the phrase.** `bore cut dia (in)` becomes `Bore cut dia, in`,
  and `(in^2)` becomes `, sq in`. A bracketed unit reads as a parenthetical
  aside, which it is not.
* **Pipes become full stops**, and the word after gains a capital.

### Conventions worth following in a generator

* Dimension a **diameter** across the feature itself, not as a tall dimension
  out at the margin, where it reads as the height of the part.
* Put provenance and caveats in `note()`, not as a floating label in the
  drawing, where they unbalance the composition.
* Name a check for what was measured, not for the variable that held it.

## mkindex.py

Rebuilds `index.html` from whatever is actually in the folder, grouped by tab and
by feature. It reads the directory rather than a list, so a sheet that failed to
render is visibly absent instead of appearing as a broken image, and the counts
in the headings are the truth. Run it after any batch lands.

## verify.py

Not a render: a byte-level check of all eleven Feature Studio tabs. It tokenizes
each file the way FeatureScript does, tracking comments, string literals and
backslash escapes, so bracket counts are computed on code only and are not
skewed by punctuation inside a string.

Each check is there because it has actually bitten:

* **encoding** - CRLF throughout, pure ASCII, no tabs, no em dash. A stray
  non-ASCII character has broken a paste into Onshape.
* **balance** - braces, parens and brackets, never dipping below zero, which
  catches a stray closer that a net count of zero would hide.
* **raw newline in a string literal** - a real newline where the two characters
  backslash-n were meant. This happened twice in one session, both times because
  a shell heredoc collapsed the escape, and it is a syntax error in
  FeatureScript.
* **panel and guard counts** - `reportFeatureInfo` and `regenError` call sites,
  so an edit that silently drops a panel or an error guard shows up.

## model/

The Python transliterations of the FeatureScript builders that every
sheet is drawn from. They lived in a session scratchpad under the system
temp directory until 2026-09-03, when a sweep found this folder's own
state file pointing at that directory as though it were durable. See
`model/README.md` for what transliterates what, and for the failure
mode that has bitten three times: a model does not error when the source
moves out from under it, so diff it against the tab before trusting it.

## A thing worth knowing about the info panels

Onshape does not render newlines in `reportFeatureInfo`. It collapses the whole
panel into one flowing wrapped paragraph. A panel written as an aligned table
with `\n` and padded labels comes out as run-together text with stray double
spaces, and two facts on separate source lines appear welded together. Every
panel in this library is therefore written as punctuated prose. If you add one,
write it that way, and never rely on a newline to separate two facts.

## A trap in the scratch directory

A scratch file named `six.py` once sat beside these scripts and shadowed the
real `six` package, which broke matplotlib for anything run from that directory.
If an import fails in a way that makes no sense, check for a local file
shadowing a library.
