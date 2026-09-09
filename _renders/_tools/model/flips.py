"""Transliteration of frcMirrorAxes / frcCocircularFlips as they now stand in
FRC Core.txt, so the node work is tested against the triangulator that will
actually run."""
import math


def mirror_axes(p):
    none = {"useX": False, "ax": 0.0, "useY": False, "ay": 0.0, "tol": 0.0}
    if len(p) == 0:
        return none
    minx = maxx = p[0][0]
    miny = maxy = p[0][1]
    for q in p:
        minx = min(minx, q[0]); maxx = max(maxx, q[0])
        miny = min(miny, q[1]); maxy = max(maxy, q[1])
    ext = max(maxx - minx, maxy - miny)
    if ext <= 0:
        return none
    tol = 1e-9 * ext
    ax = (minx + maxx) / 2.0
    ay = (miny + maxy) / 2.0
    okx = True
    for q in p:
        if not any(abs(2 * ax - q[0] - r[0]) <= tol and abs(q[1] - r[1]) <= tol for r in p):
            okx = False
            break
    oky = True
    for q in p:
        if not any(abs(q[0] - r[0]) <= tol and abs(2 * ay - q[1] - r[1]) <= tol for r in p):
            oky = False
            break
    return {"useX": okx, "ax": ax, "useY": oky, "ay": ay, "tol": tol}


def sym_key(qx, qy, sym):
    return [abs(qx - sym["ax"]) if sym["useX"] else qx,
            abs(qy - sym["ay"]) if sym["useY"] else qy]


def key_compare(a, b, tol):
    if abs(a[0] - b[0]) > tol:
        return -1 if a[0] < b[0] else 1
    if abs(a[1] - b[1]) > tol:
        return -1 if a[1] < b[1] else 1
    return 0


def diag_key(a, b, tol):
    return [a[0], a[1], b[0], b[1]] if key_compare(a, b, tol) <= 0 else [b[0], b[1], a[0], a[1]]


def diag_compare(d1, d2, tol):
    c = key_compare([d1[0], d1[1]], [d2[0], d2[1]], tol)
    if c != 0:
        return c
    return key_compare([d1[2], d1[3]], [d2[2], d2[3]], tol)


def cocircular_flips(p, tin):
    tris = [list(t) for t in tin]
    if len(tris) < 2:
        return tris
    sym = mirror_axes(p)
    usekey = sym["useX"] or sym["useY"]
    ktol = sym["tol"]
    for _sweep in range(64):
        nt = len(tris)
        ed = []
        for t in range(nt):
            for k in range(3):
                u0 = tris[t][k]; v0 = tris[t][(k + 1) % 3]
                ed.append([min(u0, v0), max(u0, v0), t])
        ed.sort(key=lambda a: (a[0], a[1], a[2]))
        cands = []
        e = 0
        while e < len(ed):
            f = e + 1
            while f < len(ed) and ed[f][0] == ed[e][0] and ed[f][1] == ed[e][1]:
                f += 1
            if f - e != 2:
                e = f
                continue
            ti = ed[e][2]; tj = ed[e + 1][2]
            sa = ed[e][0]; sb = ed[e][1]
            e = f
            if ti == tj:
                continue
            oi = -1; oj = -1
            for k in range(3):
                if tris[ti][k] != sa and tris[ti][k] != sb:
                    oi = tris[ti][k]
                if tris[tj][k] != sa and tris[tj][k] != sb:
                    oj = tris[tj][k]
            if oi < 0 or oj < 0 or oi == oj:
                continue
            pa = p[sa]; pb = p[sb]; pu = p[oi]; pv = p[oj]
            orient = (pb[0] - pa[0]) * (pu[1] - pa[1]) - (pu[0] - pa[0]) * (pb[1] - pa[1])
            if orient == 0:
                continue
            qx = pa[0] - pv[0]; qy = pa[1] - pv[1]
            rx = pb[0] - pv[0]; ry = pb[1] - pv[1]
            sx = pu[0] - pv[0]; sy = pu[1] - pv[1]
            det = ((qx * qx + qy * qy) * (rx * sy - sx * ry)
                   - (rx * rx + ry * ry) * (qx * sy - sx * qy)
                   + (sx * sx + sy * sy) * (qx * ry - rx * qy))
            dx1 = pa[0] - pb[0]; dy1 = pa[1] - pb[1]
            dx2 = pu[0] - pv[0]; dy2 = pu[1] - pv[1]
            dx3 = pa[0] - pu[0]; dy3 = pa[1] - pu[1]
            dx4 = pb[0] - pv[0]; dy4 = pb[1] - pv[1]
            scale = max(max(dx1 * dx1 + dy1 * dy1, dx2 * dx2 + dy2 * dy2),
                        max(dx3 * dx3 + dy3 * dy3, dx4 * dx4 + dy4 * dy4))
            if scale <= 0 or abs(det / orient) > 1e-9 * scale:
                continue
            s1 = (pv[0] - pu[0]) * (pa[1] - pu[1]) - (pa[0] - pu[0]) * (pv[1] - pu[1])
            s2 = (pv[0] - pu[0]) * (pb[1] - pu[1]) - (pb[0] - pu[0]) * (pv[1] - pu[1])
            if not ((s1 > 0 and s2 < 0) or (s1 < 0 and s2 > 0)):
                continue
            lc = math.sqrt(dx1 * dx1 + dy1 * dy1)
            la = math.sqrt(dx2 * dx2 + dy2 * dy2)
            if lc - la > 1e-12 * lc:
                cands.append([1, lc - la, ti, tj, sa, sb, oi, oj])
                continue
            if (not usekey) or abs(lc - la) > 1e-12 * lc:
                continue
            kc = diag_key(sym_key(pa[0], pa[1], sym), sym_key(pb[0], pb[1], sym), ktol)
            ka = diag_key(sym_key(pu[0], pu[1], sym), sym_key(pv[0], pv[1], sym), ktol)
            if diag_compare(ka, kc, ktol) < 0:
                cands.append([0, 0, ti, tj, sa, sb, oi, oj])
        if len(cands) == 0:
            break
        cands.sort(key=lambda a: (-a[0], -a[1], a[2], a[3]))
        used = [False] * nt
        did = 0
        for c in cands:
            if used[c[2]] or used[c[3]]:
                continue
            used[c[2]] = True
            used[c[3]] = True
            tris[c[2]] = [c[6], c[7], c[4]]
            tris[c[3]] = [c[6], c[7], c[5]]
            did += 1
        if did == 0:
            break
    return tris
