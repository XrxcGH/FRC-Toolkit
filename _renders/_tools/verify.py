"""Independent byte-level check of every Feature Studio tab.

The agents editing these files report themselves clean. This does not take their
word for it. It tokenizes each file the way FeatureScript does -- tracking line
comments, block comments, string literals and backslash escapes -- so the
bracket counts are computed on code only and are not skewed by punctuation
inside a string or a comment.

What it checks, and why each one has actually bitten today:
  encoding    CRLF throughout, pure ASCII, no tabs, no em dash. Onshape's
              editor is fussy and a stray non-ASCII character has broken a paste.
  balance     braces, parens, brackets, counted on code only, and never dipping
              below zero, which catches a stray closer that a net count hides.
  raw NL      a real newline written inside a string literal. This has happened
              twice today: a heredoc collapsed a two-character backslash-n into
              an actual newline, which is a syntax error in FeatureScript.
  panels      the number of reportFeatureInfo call sites, so a rewrite that
              silently dropped a panel shows up.
  errors      the number of regenError call sites, so a rewrite that dropped a
              guard shows up.
"""

import os
import re
import sys

LIB = r"C:\Users\ericj\Documents\FRC Toolkit"

TABS = [
    "FRC Core.txt",
    "FRC ToolKit.txt",
    "FRC Plate Geometry.txt",
    "FRC Structure Geometry.txt",
    "FRC Motion Geomtery.txt",
    "FRC Mechanism Geometry.txt",
    "FRC Fabrication Geometry.txt",
    "FRC Manufacturing Geometry.txt",
    "FRC Shop Geometry.txt",
    "FRC Electrical Geometry.txt",
    "FRC Hardware Geometry.txt",
]


def scan(text):
    """Walk the file as code / comment / string. Returns a findings dict."""
    i, n = 0, len(text)
    depth = {"{": 0, "(": 0, "[": 0}
    pair = {"}": "{", ")": "(", "]": "["}
    neg = []
    strings = 0
    raw_nl = 0
    unterminated = False
    line = 1
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        # comments
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    line += 1
                i += 1
            i += 2
            continue
        # string literal
        if c == '"':
            strings += 1
            start = line
            i += 1
            had_nl = False
            closed = False
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    closed = True
                    i += 1
                    break
                if text[i] == "\n":
                    had_nl = True
                    line += 1
                i += 1
            if had_nl:
                raw_nl += 1
                neg.append("raw newline in string starting line %d" % start)
            if not closed:
                unterminated = True
            continue
        if c in depth:
            depth[c] += 1
        elif c in pair:
            depth[pair[c]] -= 1
            if depth[pair[c]] < 0:
                neg.append("%s went negative at line %d" % (pair[c], line))
                depth[pair[c]] = 0
        i += 1
    return {"depth": depth, "neg": neg, "strings": strings,
            "raw_nl": raw_nl, "unterminated": unterminated}


def nested_exports(text):
    """Every `export` that is not at file scope, with its line number.

    Walks the same code/comment/string states as scan(), tracking brace depth,
    and reports any export declared while inside a block.
    """
    out = []
    i, n, depth, line = 0, len(text), 0, 1
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    line += 1
                i += 1
            i += 2
            continue
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    i += 1
                    break
                if text[i] == "\n":
                    line += 1
                i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth = max(depth - 1, 0)
        elif (c == "e" and text.startswith("export ", i)
              and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"))):
            if depth != 0:
                out.append((line, depth, text[i:i + 60].split("\n")[0]))
        i += 1
    return out



def _strip_noncode(text):
    """The file with comments and string bodies blanked, newlines preserved."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                out.append(" "); i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                out.append("\n" if text[i] == "\n" else " "); i += 1
            out.append("  "); i += 2
            continue
        if c == '"':
            out.append(" "); i += 1
            while i < n:
                if text[i] == "\\":
                    out.append("  "); i += 2; continue
                if text[i] == '"':
                    out.append(" "); i += 1; break
                out.append("\n" if text[i] == "\n" else " "); i += 1
            continue
        out.append(c); i += 1
    return "".join(out)


def unused_locals(text):
    """Declarations assigned inside a function and never read again.

    Onshape's own editor reports these as "Variable x set but not used" and
    "Unused declaration", and until a tab is pasted there is no other way to
    see them. This reproduces the check locally so a rewrite that orphans a
    helper is caught before the paste rather than after it. Comments and
    string bodies are blanked first, so a name mentioned in prose does not
    count as a use.
    """
    code = _strip_noncode(text)
    lines = code.split("\n")
    out = []

    # private functions never called anywhere in the file
    for i, l in enumerate(lines):
        m = re.match(r"\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", l)
        if m and not l.lstrip().startswith("export"):
            nm = m.group(1)
            if len(re.findall(r"\b" + re.escape(nm) + r"\b", code)) <= 1:
                out.append((i + 1, "unused private function", nm))

    # locals declared and never read
    spans = []
    for i, l in enumerate(lines):
        if re.match(r"\s*(export\s+)?function\s+[A-Za-z_]", l) or            re.match(r"\s*(export\s+)?const\s+\w+\s*=\s*defineFeature", l):
            depth, j, started = 0, i, False
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if lines[j].count("{"):
                    started = True
                if started and depth <= 0:
                    break
                j += 1
            spans.append((i, min(j, len(lines) - 1)))
    for (a, b) in spans:
        body = "\n".join(lines[a:b + 1])
        for m in re.finditer(r"\b(?:var|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", body):
            nm = m.group(1)
            # A feature is declared "export const frcX = defineFeature(...)"
            # at file scope. That is public surface, not a local, and Onshape
            # does not flag it either.
            head = body[:m.start()].rsplit(chr(10), 1)[-1]
            if head.lstrip().startswith("export"):
                continue
            uses = re.findall(r"\b" + re.escape(nm) + r"\b", body)
            assigns = re.findall(r"\b" + re.escape(nm) + r"\s*(?:=[^=]|\+=|~=|-=)", body)
            if len(uses) - len(assigns) <= 0:
                ln = a + body[:m.start()].count("\n") + 1
                out.append((ln, "set but not used", nm))
    return out


def main():
    bad = 0
    print("%-32s %8s %6s %5s %4s %4s %-14s %5s %5s"
          % ("tab", "bytes", "CRLF", "ASCII", "tab", "em", "balance",
             "panel", "err"))
    for t in TABS:
        p = os.path.join(LIB, t)
        if not os.path.exists(p):
            print("%-32s MISSING" % t)
            bad += 1
            continue
        raw = open(p, "rb").read()
        text = raw.decode("latin-1")
        crlf = raw.count(b"\r\n")
        bare_lf = raw.count(b"\n") - crlf
        bare_cr = raw.count(b"\r") - crlf
        nonascii = sum(1 for b in raw if b > 127)
        tabs = raw.count(b"\t")
        em = raw.count("\u2014".encode("utf-8")) + raw.count(b"\x97")
        r = scan(text)
        nested = nested_exports(text)
        unused = unused_locals(text)
        d = r["depth"]
        ok = (bare_lf == 0 and bare_cr == 0 and nonascii == 0 and tabs == 0
              and em == 0 and d["{"] == 0 and d["("] == 0 and d["["] == 0
              and r["raw_nl"] == 0 and not r["unterminated"] and not r["neg"]
              and not nested and not unused)
        if not ok:
            bad += 1
        bal = "%d/%d/%d" % (d["{"], d["("], d["["])
        print("%-32s %8d %6d %5s %4d %4d %-14s %5d %5d %s"
              % (t, len(raw), crlf, "yes" if nonascii == 0 else "NO",
                 tabs, em, bal,
                 text.count("reportFeatureInfo"), text.count("regenError"),
                 "" if ok else "  <-- PROBLEM"))
        if bare_lf or bare_cr:
            print("      bare LF %d, bare CR %d" % (bare_lf, bare_cr))
        if r["unterminated"]:
            print("      UNTERMINATED STRING LITERAL")
        for m in r["neg"][:6]:
            print("      %s" % m)
        for (ln, dep, snippet) in nested[:6]:
            print("      NESTED EXPORT at line %d, brace depth %d: %s"
                  % (ln, dep, snippet))
        for (ln, why, nm) in unused[:8]:
            print("      line %d: %s: %s" % (ln, why, nm))
    print("\n%d tab(s) with a problem" % bad)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
