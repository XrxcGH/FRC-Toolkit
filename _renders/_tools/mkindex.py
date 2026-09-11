"""Rebuild _renders/index.html from whatever sheets are actually in the folder.

Run it after any batch of sheets lands. It reads the directory rather than a
list, so a sheet that failed to render is visibly absent instead of showing as a
broken image, and the counts in the headings are the truth.
"""

import os
import re
import time

RENDERS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATS = [
    ("mech",   "Mechanism"),
    ("struct", "Structure and Fabrication"),
    ("motion", "Motion and Manufacturing"),
    ("plate",  "Plate Geometry"),
    ("shop",   "Shop, Electrical and Hardware"),
]

HEAD = """<!doctype html><meta charset="utf-8"><title>FRC Toolkit expected-output renders</title>
<style>
:root{--bg:#fff;--fg:#111;--mut:#666;--line:#ddd}
@media(prefers-color-scheme:dark){:root{--bg:#151515;--fg:#eee;--mut:#999;--line:#333}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:28px 32px;max-width:1500px}
h1{font-size:24px;margin:0 0 4px} .sub{color:var(--mut);margin:0 0 28px;max-width:70ch}
h2{font-size:19px;margin:34px 0 6px;padding-bottom:5px;border-bottom:2px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px;color:var(--mut);text-transform:capitalize;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}
figure{margin:0;border:1px solid var(--line);border-radius:7px;overflow:hidden;background:#fff}
figure img{width:100%;display:block;cursor:zoom-in}
figcaption{font-size:11.5px;color:var(--mut);padding:6px 8px;background:var(--bg);word-break:break-all}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.9);display:none;align-items:center;justify-content:center;z-index:9;cursor:zoom-out}
#lb img{max-width:96vw;max-height:96vh}
nav{position:sticky;top:0;background:var(--bg);padding:8px 0 10px;border-bottom:1px solid var(--line);margin-bottom:4px;z-index:5}
nav a{color:var(--fg);margin-right:16px;font-size:13px;text-decoration:none;border-bottom:1px dotted var(--mut)}
</style>
<h1>FRC Toolkit expected-output renders</h1>
<p class="sub">Geometry computed from the shipped FeatureScript at the stated parameters, then drawn.
This is the expected half; hold it beside what Onshape actually builds after pasting.
Each sheet carries its own checks: a value the drawing measured against what the feature claims.
A check that failed is printed in bold orange at the foot of the sheet, so a wrong sheet is
visible without being read. Click any image to enlarge.</p>
"""

TAIL = """<div id="lb" onclick="this.style.display='none'"><img></div>
<script>
document.querySelectorAll('.grid img').forEach(function(i){
  i.onclick=function(){var b=document.getElementById('lb');
    b.querySelector('img').src=i.src;b.style.display='flex';};});
</script>
"""


def feature_of(name):
    """mech_armpivot_default -> armpivot"""
    parts = name.split("_")
    return parts[1] if len(parts) > 1 else parts[0]


def main():
    files = sorted(f for f in os.listdir(RENDERS)
                   if f.lower().endswith((".png", ".svg")) and not f.startswith("_"))
    used = set()
    out = [HEAD]

    anchors = []
    for pre, label in CATS:
        if any(f.startswith(pre + "_") for f in files):
            anchors.append((re.sub(r"[^A-Za-z0-9]", "", label), label))
    out.append("<nav>\n")
    for a, label in anchors:
        out.append('<a href="#%s">%s</a>\n' % (a, label))
    out.append("</nav>\n")

    total = 0
    for pre, label in CATS:
        mine = [f for f in files if f.startswith(pre + "_")]
        if not mine:
            continue
        anchor = re.sub(r"[^A-Za-z0-9]", "", label)
        out.append('<h2 id="%s">%s <span style="font-weight:400;color:#888">'
                   '(%d)</span></h2>\n' % (anchor, label, len(mine)))
        groups = {}
        for f in mine:
            groups.setdefault(feature_of(os.path.splitext(f)[0]), []).append(f)
        for feat in sorted(groups):
            g = sorted(groups[feat])
            out.append('<h3>%s <span style="font-weight:400">(%d)</span></h3>'
                       '<div class="grid">\n' % (feat, len(g)))
            for f in g:
                out.append('<figure><img loading="lazy" src="%s">'
                           '<figcaption>%s</figcaption></figure>\n' % (f, f))
            out.append("</div>\n")
            used.update(g)
            total += len(g)

    stray = [f for f in files if f not in used]
    if stray:
        out.append('<h2 id="Other">Other <span style="font-weight:400;color:#888">'
                   '(%d)</span></h2><div class="grid">\n' % len(stray))
        for f in stray:
            out.append('<figure><img loading="lazy" src="%s">'
                       '<figcaption>%s</figcaption></figure>\n' % (f, f))
        out.append("</div>\n")
        total += len(stray)

    out.append('<p class="sub" style="margin-top:34px">%d sheets, rebuilt %s.</p>\n'
               % (total, time.strftime("%Y-%m-%d %H:%M")))
    out.append(TAIL)

    path = os.path.join(RENDERS, "index.html")
    open(path, "w", encoding="utf-8").write("".join(out))
    print("wrote %s, %d sheets" % (path, total))
    for pre, label in CATS:
        n = len([f for f in files if f.startswith(pre + "_")])
        print("  %-30s %d" % (label, n))
    return total


if __name__ == "__main__":
    main()
