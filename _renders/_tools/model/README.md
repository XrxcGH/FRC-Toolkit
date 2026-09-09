# Verification models

Python transliterations of the FeatureScript builders. The Onshape API
allocation is exhausted until 2026-10-13, so nothing in the library can be
compiled, regenerated or photographed; the only way to check a claim is to
transliterate the builder, run it, and compare. These are those
transliterations, and every reference sheet under `_renders` is drawn from
them.

They used to live in a session scratchpad under the system temp directory,
which is cleaned. A sweep on 2026-09-03 found the state file pointing at that
directory as though it were durable, so they were moved here.

| File | Transliterates |
|---|---|
| `whyC.py` | the truss pocket loop in `frcLightenOneFace`, with a reason recorded for every triangle dropped |
| `patterns6.py` | the isogrid, grid, diagonal, honeycomb, circles and single-pocket branches, including the tether pass |
| `truss.py`, `truss2.py`, `truss5.py` | the shared maths: Delaunay, perimeter stations, polygon predicates, auto sizing |
| `flips.py` | cocircular tie-breaking and mirror axis detection |

Self-contained: each adds its own directory to `sys.path`, so

```
cd _renders/_tools/model
python -c "import whyC; print(whyC.build((15,20), [(4.7,4.8,3.18)])['edge_max'])"
```

works from a clean checkout with only the packages `renderkit.py` already
needs, plus `shapely` for the sheets that do offset geometry.

## The failure mode these have, and it has bitten three times

A transliteration does not error when the source moves out from under it. It
agrees with itself, produces clean tables, and passes its own checks. Before
trusting one, diff it against the tab it claims to transliterate, clause by
clause. `whyC.py`'s `sizing()` has been stale twice: once when a buckling span
became a pocket size, and once when that conversion grew the
`(sqrt(3) / 2) * span - rib` form it has now.

When a builder and its model are edited in the same session, the model update
belongs in the same step as the code change, not on a list for later.
