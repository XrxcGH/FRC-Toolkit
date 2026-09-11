"""Drawing harness for the FRC Toolkit reference sheets.

The Onshape API allocation is exhausted, so nothing in this library can be built
or photographed. The substitute is to transliterate a builder's geometry into
Python, draw what it produces, and state on the same sheet what the feature
CLAIMS to produce. A defect shows up as a disagreement between the two.

These sheets are reference documents, not internal scratch output. Every sheet
is laid out from its content so that nothing overlaps and nothing is clipped,
and every recorded check is always printed. Earlier versions stopped drawing
checks once they ran out of room, which meant a failing check could vanish from
a sheet while still being counted in the totals; that cannot happen now.

Units are inches throughout and y is up, as in the FeatureScript.

    import sys; sys.path.insert(0, r"...\\_renders\\_tools")
    from renderkit import Sheet, report

    s = Sheet("plate_lighten_truss",
              "FRC Lighten, Truss Between Holes",
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

House style, which the sheets are judged against:

* Titles are Title Case and name the feature and the configuration. The helper
  applies Title Case for you, preserving acronyms, part numbers and units.
* Subtitles and captions are sentence case, full sentences, no abbreviations
  the reader has to decode.
* Check names are Title Case noun phrases naming what was measured, not code
  identifiers. "Pitch diameter" rather than "pd_calc".
* `expect(what, want, got)` records a check. `want` is what the FEATURE claims;
  `got` is what the drawing actually MEASURED. A check that recomputes the same
  expression twice proves nothing, so derive the wanted value from first
  principles, from the published standard, or from the vendor drawing.
"""

import os
import math
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
from matplotlib.lines import Line2D

RENDERS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIGSIZE = (13.0, 9.75)          # 2080 x 1560 at 160 dpi
DPI = 160

C = {
    "part":   "#d3d3d3",        # material that stays
    "edge":   "#1a1a1a",
    "cut":    "#ffffff",        # removed or open
    "pocket": "#c8322c",        # boundary of removed material
    "hole":   "#ffffff",
    "ref":    "#8a8a8a",        # construction, keep-outs, axes
    "warn":   "#b4530a",        # a check that failed
    "ok":     "#2f6f3e",
    "sec":    "#b0b8c4",        # a secondary body
    "txt":    "#33312e",
    "rule":   "#c9c4bd",        # hairlines and table rules
    "paper":  "#ffffff",
}

# Words that stay lower case inside a title unless they lead or close it.
_SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
          "nor", "of", "on", "onto", "or", "over", "per", "the", "to", "up",
          "via", "with", "without"}


def _c(k):
    if k in (None, "none"):
        return "none"
    return C.get(k, k)


def title_case(s):
    """Title Case that leaves technical tokens alone.

    A word is left exactly as written when it already carries a capital after
    the first character (HTD, MK4i, roboRIO), when it contains a digit or a
    symbol (#25, 1.125, 20DP, T5/T10), or when it is a unit. Everything else is
    capitalised, except the small words, which stay lower unless they lead or
    close the title.
    """
    words = str(s).split()
    out = []
    for i, w in enumerate(words):
        core = w.strip("(),.:;")
        keep = (any(ch.isdigit() for ch in core)
                or any(ch in "#/_%\"'" for ch in core)
                or any(ch.isupper() for ch in core[1:])
                or core.lower() in ("in", "mm", "lb", "kg", "deg", "rpm"))
        if keep:
            out.append(w)
        elif core.lower() in _SMALL and 0 < i < len(words) - 1:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:] if w else w)
    return " ".join(out)


_UNITS = [("in^2", "sq in"), ("in2", "sq in")]


def _tidy(s):
    """Fold bracketed unit tags into prose and repair sentence breaks.

    Generators were written at different times and several tag their units as
    "(in)", which reads as a parenthetical aside rather than as a unit, and a
    few separate clauses with a pipe. These sheets are reference documents, so
    both are folded into ordinary prose. A word opening a new sentence is
    capitalised, since the break may not have existed when it was written.
    """
    s = str(s)
    # " (in)" and "(in)" both become ", in", without leaving a doubled space.
    def unit(m):
        u = m.group(1).strip()
        for a, b in _UNITS:
            u = u.replace(a, b)
        return ", " + u
    s = re.sub(r"\s*\(((?:sq )?in\^?2?|in|mm|deg|lb|kg|rpm|ft/s|s|percent)\)", unit, s)
    s = s.replace(" | ", ". ")
    s = " ".join(s.split())
    # Folding a separator into a full stop can leave a space in front of it.
    s = re.sub(r"(?<![.,;:])\s+([.,;:])(?![.,;:])", r"", s)
    s = re.sub(r"(?<![.,;:])([,;:])(?=[A-Za-z])", r" ", s)
    # Capitalise whatever now opens a sentence.
    s = re.sub(r"(?<![.,;:])([.!?]\s+)([a-z])",
               lambda m: m.group(1) + m.group(2).upper(), s)
    return s


def _sentence(s):
    """Sentence case: capitalise the opening letter, leave the rest alone.

    Generators were written at different times and some open a label or a check
    name in lower case. Nothing else is touched, because the rest of the string
    routinely carries part numbers, units and acronyms that must not be
    recased.
    """
    s = str(s).strip()
    if not s:
        return s
    s = _tidy(s)
    return s[:1].upper() + s[1:]


def _num(v):
    """Format a check value for the table without inventing precision."""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e12:
            return str(int(v))
        for p in (4, 5, 6):
            t = ("%." + str(p) + "f") % v
            if float(t) == round(v, p):
                return t.rstrip("0").rstrip(".")
        return "%.6g" % v
    return str(v)


class Sheet:
    def __init__(self, name, title, subtitle="", equal=True):
        self.name = name
        self.title = title_case(title)
        self.subtitle = _sentence(subtitle)
        self.equal = equal
        self.items = []
        self.legend_items = []
        self.checks = []
        self.caption_text = ""
        self.notes = []
        self._xs = []
        self._ys = []
        self._gxs = []      # the drawn part alone, used to centre the view
        self._gys = []

    # ---- bookkeeping ----------------------------------------------------
    def _seen(self, pts, geometry=False):
        for p in pts:
            self._xs.append(float(p[0]))
            self._ys.append(float(p[1]))
            if geometry:
                self._gxs.append(float(p[0]))
                self._gys.append(float(p[1]))

    # ---- geometry -------------------------------------------------------
    def poly(self, pts, fill="part", edge="edge", lw=1.3, z=2, alpha=1.0, dash=None):
        pts = [(float(p[0]), float(p[1])) for p in pts]
        if len(pts) < 2:
            return
        self._seen(pts, geometry=True)
        self.items.append(("poly", pts, fill, edge, lw, z, alpha, dash))

    def circle(self, c, r, fill="hole", edge="edge", lw=1.3, z=3, dash=None):
        c = (float(c[0]), float(c[1]))
        r = float(r)
        self._seen([(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)], geometry=True)
        self.items.append(("circ", c, r, fill, edge, lw, z, dash))

    def line(self, a, b, color="ref", lw=1.0, z=4, dash=None):
        self._seen([a, b])
        self.items.append(("line", (float(a[0]), float(a[1])),
                           (float(b[0]), float(b[1])), color, lw, z, dash))

    def crosshair(self, c, r):
        self.line((c[0] - r, c[1]), (c[0] + r, c[1]), color="edge", lw=0.8)
        self.line((c[0], c[1] - r), (c[0], c[1] + r), color="edge", lw=0.8)

    def label(self, at, text, color="txt", size=9, ha="center", va="center"):
        self._seen([at])
        self.items.append(("text", (float(at[0]), float(at[1])), str(text),
                           color, size, ha, va))

    # ---- annotation -----------------------------------------------------
    def dim_h(self, x0, x1, y, text):
        self.items.append(("dimh", float(x0), float(x1), float(y), str(text)))
        self._seen([(x0, y), (x1, y)])

    def dim_v(self, y0, y1, x, text):
        self.items.append(("dimv", float(y0), float(y1), float(x), str(text)))
        self._seen([(x, y0), (x, y1)])

    def scalebar(self, length, text=None):
        self.items.append(("scale", float(length), text or ("%g in" % length)))

    def legend(self, entries):
        """entries: list of (label, fill, edge). Labels are sentence case."""
        self.legend_items = [(_sentence(n), f, e) for (n, f, e) in entries]

    def legend_default(self):
        self.legend([("Material that stays", "part", "edge"),
                     ("Material removed", "cut", "pocket"),
                     ("Existing hole", "hole", "edge")])

    def caption(self, text):
        self.caption_text = _sentence(text)

    def note(self, text):
        self.notes.append(_sentence(text))

    # ---- audit ----------------------------------------------------------
    def expect(self, what, want, got, tol=1e-6):
        num = (isinstance(want, (int, float)) and isinstance(got, (int, float))
               and not isinstance(want, bool) and not isinstance(got, bool))
        if num:
            ok = abs(float(want) - float(got)) <= tol
        else:
            ok = (want == got)
        self.checks.append((_sentence(what), want, got, ok))
        return ok

    @property
    def failures(self):
        return [c for c in self.checks if not c[3]]

    # ---- output ---------------------------------------------------------
    def save(self, outdir=RENDERS):
        if not os.path.isdir(outdir):
            os.makedirs(outdir)

        fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=C["paper"])
        W, H = FIGSIZE[0], FIGSIZE[1]

        # ---- lay the page out from its content, top down and bottom up, so
        # ---- the drawing gets whatever is left and nothing can collide.
        pad = 0.030
        y = 1.0 - 0.038
        fig.text(0.5, y, self.title, fontsize=21, fontweight="bold",
                 ha="center", va="top", color="#141210")
        y -= 0.047
        if self.subtitle:
            for ln in textwrap.wrap(self.subtitle, 108) or [""]:
                fig.text(0.5, y, ln, fontsize=11.5, ha="center", va="top",
                         color="#5c574f")
                y -= 0.026
        y -= 0.006
        if self.legend_items:
            handles = [Rectangle((0, 0), 1, 1, facecolor=_c(f), edgecolor=_c(e),
                                 linewidth=1.2)
                       for (_, f, e) in self.legend_items]
            leg = fig.legend(handles,
                             [n for (n, _, _) in self.legend_items],
                             loc="upper center", bbox_to_anchor=(0.5, y),
                             ncol=min(4, len(self.legend_items)), frameon=False,
                             fontsize=10.5, handlelength=1.5, columnspacing=2.6)
            leg.get_frame().set_linewidth(0)
            y -= 0.052
        top_of_art = y - 0.012

        # ---- bottom block: caption prose, then the verification table ----
        cap_lines = []
        for para in ([self.caption_text] if self.caption_text else []) + self.notes:
            cap_lines += (textwrap.wrap(para, 124) or [""])

        rows = self.checks
        n_rows = len(rows)
        cap_step = 0.0215
        row_step = 0.0205
        head_h = 0.040 if n_rows else 0.0
        foot_h = 0.030

        block = (len(cap_lines) * cap_step) + head_h + (n_rows * row_step) + foot_h
        # If a sheet is unusually wordy, tighten the leading rather than drop
        # anything. Nothing is ever omitted.
        max_block = 0.46
        if block > max_block:
            k = max_block / block
            cap_step *= k
            row_step *= k
            head_h *= k
            block = max_block

        bottom_of_art = block + 0.030

        # ---- the drawing --------------------------------------------------
        art_h = max(top_of_art - bottom_of_art, 0.10)
        ax = fig.add_axes([0.055, bottom_of_art, 0.89, art_h])
        ax.set_facecolor(C["paper"])
        if self.equal:
            ax.set_aspect("equal", adjustable="box", anchor="C")
        ax.axis("off")

        _pre_x = self._xs or [0.0, 1.0]
        _pre_y = self._ys or [0.0, 1.0]
        _span0 = max(max(_pre_x) - min(_pre_x), max(_pre_y) - min(_pre_y), 1e-6)
        _lift = [0.015 * _span0]

        has_scale = any(it[0] == "scale" for it in self.items)
        for it in self.items:
            k = it[0]
            if k == "poly":
                _, pts, fill, edge, lw, z, alpha, dash = it
                ax.add_patch(Polygon(pts, closed=True, facecolor=_c(fill),
                                     edgecolor=_c(edge), linewidth=lw,
                                     zorder=z, alpha=alpha,
                                     linestyle=(dash or "solid"),
                                     joinstyle="round"))
            elif k == "circ":
                _, c, r, fill, edge, lw, z, dash = it
                ax.add_patch(Circle(c, r, facecolor=_c(fill), edgecolor=_c(edge),
                                    linewidth=lw, zorder=z,
                                    linestyle=(dash or "solid")))
            elif k == "line":
                _, a, b, col, lw, z, dash = it
                ax.add_line(Line2D([a[0], b[0]], [a[1], b[1]], color=_c(col),
                                   linewidth=lw, zorder=z,
                                   linestyle=(dash or "solid")))
            elif k == "text":
                _, at, s, col, size, ha, va = it
                ax.text(at[0], at[1], s, color=_c(col), fontsize=size,
                        ha=ha, va=va, zorder=9)
            elif k == "dimh":
                _, x0, x1, yy, s = it
                ax.annotate("", xy=(x0, yy), xytext=(x1, yy),
                            arrowprops=dict(arrowstyle="<|-|>", color="#6a655d",
                                            linewidth=0.9,
                                            shrinkA=0, shrinkB=0,
                                            mutation_scale=9), zorder=8)
                ax.text((x0 + x1) / 2.0, yy + _lift[0], s, fontsize=10,
                        color=C["txt"], ha="center", va="bottom", zorder=9,
                        bbox=dict(boxstyle="square,pad=0.12", fc=C["paper"],
                                  ec="none"))
            elif k == "dimv":
                _, y0, y1, xx, s = it
                ax.annotate("", xy=(xx, y0), xytext=(xx, y1),
                            arrowprops=dict(arrowstyle="<|-|>", color="#6a655d",
                                            linewidth=0.9,
                                            shrinkA=0, shrinkB=0,
                                            mutation_scale=9), zorder=8)
                ax.text(xx - _lift[0], (y0 + y1) / 2.0, s, fontsize=10,
                        color=C["txt"], ha="right", va="center", rotation=90,
                        zorder=9,
                        bbox=dict(boxstyle="square,pad=0.12", fc=C["paper"],
                                  ec="none"))

        if self._xs:
            x0, x1 = min(self._xs), max(self._xs)
            y0, y1 = min(self._ys), max(self._ys)
        else:
            x0, x1, y0, y1 = 0.0, 1.0, 0.0, 1.0
        w = max(x1 - x0, 1e-6)
        h = max(y1 - y0, 1e-6)
        span = max(w, h)
        m = 0.09 * span
        low = y0 - m - (0.15 * span if has_scale else 0.0)
        if has_scale:
            for it in self.items:
                if it[0] == "scale":
                    L, s = it[1], it[2]
                    bx = (x0 + x1) / 2.0 - L / 2.0   # centred under the art
                    by = y0 - m - 0.060 * span
                    ax.add_line(Line2D([bx, bx + L], [by, by],
                                       color=C["txt"], lw=1.5))
                    for t in (bx, bx + L / 2.0, bx + L):
                        ax.add_line(Line2D([t, t],
                                           [by - 0.018 * span, by + 0.018 * span],
                                           color=C["txt"], lw=1.5))
                    ax.text(bx + L / 2.0, by - 0.040 * span, s, fontsize=9.5,
                            color=C["txt"], ha="center", va="top")
        fx0, fx1 = x0 - m, x1 + m
        gx = self._gxs or self._xs or [0.0, 1.0]
        cx = (min(gx) + max(gx)) / 2.0
        hx = max(cx - fx0, fx1 - cx)
        ax.set_xlim(cx - hx, cx + hx)
        ax.set_ylim(low, y1 + m)

        # ---- caption prose ------------------------------------------------
        yb = block + 0.006
        for ln in cap_lines:
            fig.text(0.5, yb, ln, fontsize=9.8, ha="center", va="top",
                     color=C["txt"])
            yb -= cap_step

        # ---- verification table -------------------------------------------
        if n_rows:
            n_bad = len(self.failures)
            head = ("Verification: %d checks, all passed" % n_rows) if not n_bad \
                else ("Verification: %d checks, %d failed" % (n_rows, n_bad))
            yb -= 0.004
            fig.text(0.5, yb, head, fontsize=10, fontweight="bold",
                     ha="center", va="top",
                     color=(C["ok"] if not n_bad else C["warn"]))
            yb -= 0.019
            LX, EX, MX, RX = 0.085, 0.585, 0.725, 0.885
            fig.text(LX, yb, "Measurement", fontsize=8.6, ha="left", va="top",
                     color="#7a736a")
            fig.text(EX, yb, "Expected", fontsize=8.6, ha="right", va="top",
                     color="#7a736a")
            fig.text(MX, yb, "Measured", fontsize=8.6, ha="right", va="top",
                     color="#7a736a")
            fig.text(RX, yb, "Result", fontsize=8.6, ha="right", va="top",
                     color="#7a736a")
            yb -= 0.013
            fig.add_artist(Line2D([LX, RX], [yb, yb], color=C["rule"],
                                  linewidth=0.8))
            yb -= 0.008
            for (what, want, got, ok) in rows:
                col = C["txt"] if ok else C["warn"]
                nm = what if len(what) <= 74 else what[:71] + "..."
                fig.text(LX, yb, nm, fontsize=9.2, ha="left", va="top",
                         color=col)
                fig.text(EX, yb, _num(want), fontsize=9.2, ha="right", va="top",
                         color=col)
                fig.text(MX, yb, _num(got), fontsize=9.2, ha="right", va="top",
                         color=col)
                fig.text(RX, yb, "Pass" if ok else "FAIL", fontsize=9.2,
                         ha="right", va="top",
                         color=(C["ok"] if ok else C["warn"]),
                         fontweight=("normal" if ok else "bold"))
                yb -= row_step

        # ---- footer --------------------------------------------------------
        fig.add_artist(Line2D([0.085, 0.915], [0.026, 0.026],
                              color=C["rule"], linewidth=0.8))
        fig.text(0.085, 0.017,
                 "FRC Toolkit reference sheet. Geometry computed from the "
                 "shipped FeatureScript, not built in Onshape.",
                 fontsize=8.2, ha="left", va="top", color="#8c857b")
        fig.text(0.915, 0.017, self.name, fontsize=8.2, ha="right", va="top",
                 color="#8c857b")

        path = os.path.join(outdir, self.name + ".png")
        fig.savefig(path, dpi=DPI, facecolor=C["paper"])
        plt.close(fig)
        return path


def report(sheets):
    """Print every check. Auditors read this; the sheet is for the reader."""
    bad = 0
    total = 0
    for s in sheets:
        f = s.failures
        bad += len(f)
        total += len(s.checks)
        print("%-42s %3d checks, %d failed" % (s.name, len(s.checks), len(f)))
        for (what, want, got, ok) in s.checks:
            if not ok:
                print("      FAIL  %s: expected %s, measured %s"
                      % (what, _num(want), _num(got)))
    print("TOTAL: %d checks across %d sheets, %d failed" % (total, len(sheets), bad))
    return bad
