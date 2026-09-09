"""Transliteration of frcLightenOneFace's TRUSS branch, in inches.

Same formulas, same constants, same order, same clamps and guards as
FRC Plate Geometry.txt.  No Onshape call is made.
"""
import math
import numpy as np

INCH = 1.0
TOOL_DIA = 0.25
PROC_CNC = "CNC"


# ----------------------------------------------------------------- core ----
def frc_min_wall(tool_dia):          # CNC
    return max(0.090, tool_dia)


def frc_min_corner_radius(tool_dia):  # CNC
    return tool_dia / 2


def frc_min_floor():                  # CNC
    return 0.040


def frc_slenderness_limit():          # AL_6061
    return 20.1


def frc_auto_sizing(thickness, tool_dia=TOOL_DIA):
    """BALANCED preset, CNC, 6061."""
    k = {"wall": 1.0, "hole": 0.35, "rib": 0.90, "span": 12}
    floor_min = frc_min_wall(tool_dia)
    rib = min(max(k["rib"] * thickness, floor_min), 0.5)
    want_pocket = min(max(k["span"] * thickness, 0.4), 4.0)
    buckle_pocket = rib * frc_slenderness_limit()
    return {
        "wall": min(max(k["wall"] * thickness, floor_min), 0.5),
        "rib": rib,
        "pocket": min(want_pocket, buckle_pocket),
        "holeFactor": k["hole"],
        "floor": max(0.25 * thickness, frc_min_floor()),
    }


def in_circumcircle(a, b, c, d):
    ax, ay = a[0] - d[0], a[1] - d[1]
    bx, by = b[0] - d[0], b[1] - d[1]
    cx, cy = c[0] - d[0], c[1] - d[1]
    det = ((ax * ax + ay * ay) * (bx * cy - cx * by)
           - (bx * bx + by * by) * (ax * cy - cx * ay)
           + (cx * cx + cy * cy) * (ax * by - bx * ay))
    orient = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
    return det > 0 if orient > 0 else det < 0


def frc_delaunay(pin):
    """Bowyer-Watson, ported literally."""
    n = len(pin)
    if n < 3:
        return []
    p = list(pin)
    minx = maxx = p[0][0]
    miny = maxy = p[0][1]
    for q in p:
        minx, maxx = min(minx, q[0]), max(maxx, q[0])
        miny, maxy = min(miny, q[1]), max(maxy, q[1])
    dm = max(maxx - minx, maxy - miny) * 10 + 1
    mx, my = (minx + maxx) / 2, (miny + maxy) / 2
    p.append((mx - 2 * dm, my - dm))
    p.append((mx, my + 2 * dm))
    p.append((mx + 2 * dm, my - dm))
    tris = [[n, n + 1, n + 2]]
    for i in range(n):
        bad, keep = [], []
        for t in tris:
            if in_circumcircle(p[t[0]], p[t[1]], p[t[2]], p[i]):
                bad += [[t[0], t[1]], [t[1], t[2]], [t[2], t[0]]]
            else:
                keep.append(t)
        for e in range(len(bad)):
            shared = False
            for f in range(len(bad)):
                if e == f:
                    continue
                if ((bad[e][0] == bad[f][0] and bad[e][1] == bad[f][1])
                        or (bad[e][0] == bad[f][1] and bad[e][1] == bad[f][0])):
                    shared = True
                    break
            if not shared:
                keep.append([bad[e][0], bad[e][1], i])
        tris = keep
    return [t for t in tris if t[0] < n and t[1] < n and t[2] < n]


def frc_wall_extension(grow, rib_dir, wall_dir, cap_multiple):
    sin_arrival = abs(rib_dir[0] * wall_dir[1] - rib_dir[1] * wall_dir[0])
    if sin_arrival < 1e-6:
        return {"anchored": False, "extension": 0.0}
    if 1 / sin_arrival > cap_multiple:
        return {"anchored": False, "extension": 0.0}
    return {"anchored": True, "extension": grow / sin_arrival}


# ------------------------------------------------------------ geometry ----
def nrm(v):
    return math.hypot(v[0], v[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def perimeter_stations(rect, max_edge):
    """frcPerimeterStations on the wall-offset outer loop.

    A rectangular prism's four side faces stay planar under opOffsetFace, so
    the outer loop is the plate rectangle inset by wall + toolRad.  Edges are
    traversed consistently, which is the case D5 in render_plate.md flags as
    the one that comes out mirror symmetric.
    """
    x0, y0, x1, y1 = rect
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    out = []
    for i in range(4):
        a = corners[i]
        b = corners[(i + 1) % 4]
        L = nrm(sub(b, a))
        if L < 1e-6:
            continue
        d = mul(sub(b, a), 1.0 / L)
        nsub = max(math.floor(L / max_edge + 1e-9), 1)
        for j in range(nsub):
            p = add(a, mul(d, L * j / nsub))
            if any(nrm(sub(q["point"], p)) < 0.02 for q in out):
                continue
            out.append({"point": p, "direction": d})
    return out


def tri_angles(a, b, c):
    """Interior angles in degrees at a, b, c."""
    ab, ac = nrm(sub(b, a)), nrm(sub(c, a))
    bc = nrm(sub(c, b))
    if min(ab, ac, bc) < 1e-9:
        return (0.0, 0.0, 0.0)

    def ang(o, p, q):
        u = mul(sub(p, o), 1.0 / nrm(sub(p, o)))
        v = mul(sub(q, o), 1.0 / nrm(sub(q, o)))
        return math.degrees(math.acos(max(-1.0, min(1.0, dot(u, v)))))
    return (ang(a, b, c), ang(b, a, c), ang(c, a, b))


def seg_cross(p1, p2, p3, p4):
    """True when the open segments p1p2 and p3p4 properly cross."""
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
    d1, d2 = o(p3, p4, p1), o(p3, p4, p2)
    d3, d4 = o(p1, p2, p3), o(p1, p2, p4)
    return ((d1 > 1e-12 and d2 < -1e-12) or (d1 < -1e-12 and d2 > 1e-12)) and \
           ((d3 > 1e-12 and d4 < -1e-12) or (d3 < -1e-12 and d4 > 1e-12))


def point_in_tri(p, a, b, c):
    def o(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (w[0] - u[0]) * (v[1] - u[1])
    d1, d2, d3 = o(a, b, p), o(b, c, p), o(c, a, p)
    neg = (d1 < -1e-9) or (d2 < -1e-9) or (d3 < -1e-9)
    pos = (d1 > 1e-9) or (d2 > 1e-9) or (d3 > 1e-9)
    return not (neg and pos)


# --------------------------------------------------------------- builder ----
def build_truss(plate, holes, thickness=0.25, tool_dia=TOOL_DIA,
                fixed=False, nn_multiple=1.7, sliver_deg=20.0,
                cap_walls=True, abs_cap=None, locality=False, local_scale=True,
                use_cross=False):
    """One face of frcLightenOneFace, TRUSS branch.

    plate  = (W, H) with the lower left corner at the origin.
    holes  = [(cx, cy, diameter), ...]
    fixed  = False runs the shipped code, True runs the spacing cap plus the
             sliver filter plus the boss connectivity guarantee.
    """
    s = frc_auto_sizing(thickness, tool_dia)
    tool_rad = frc_min_corner_radius(tool_dia)
    W, H = plate

    # opOffsetFace(-(wall + toolRad)) on every side wall: the outline shrinks
    # by that much and every hole grows by it.
    inset = s["wall"] + tool_rad
    rect = (inset, inset, W - inset, H - inset)

    # cls.inner -> islands, with the keep ring an existing round hole earns.
    islands = []
    for (cx, cy, d) in holes:
        prot = d / 2 + s["wall"]
        need = min(max(s["holeFactor"] * d, s["wall"]), 0.5)
        if need > s["wall"] + 1e-6:
            prot = d / 2 + need
        islands.append({"center": (cx, cy), "r": prot, "d": d})

    bb_lo = (rect[0], rect[1])
    bb_hi = (rect[2], rect[3])
    c2 = ((bb_lo[0] + bb_hi[0]) / 2, (bb_lo[1] + bb_hi[1]) / 2)
    span_x = bb_hi[0] - bb_lo[0]
    span_y = bb_hi[1] - bb_lo[1]
    size_cap = max(min(span_x, span_y) / 3, 0.3)
    pocket_used = min(s["pocket"], size_cap)
    pitch = pocket_used + s["rib"]

    max_edge = min(max(pocket_used * 2.5, 3.0), max(span_x, span_y) / 4)
    stations = perimeter_stations(rect, max_edge)

    pts, radii, is_hole, wall_dir = [], [], [], []
    for isl in islands:
        pts.append(isl["center"])
        radii.append(isl["r"])
        is_hole.append(True)
        wall_dir.append((0.0, 0.0))
    for st in stations:
        pts.append(st["point"])
        radii.append(0.0)
        is_hole.append(False)
        wall_dir.append(st["direction"])

    grow = s["wall"] + s["rib"]
    rib_half = s["rib"] / 2
    n_hole = len(islands)
    stats = {"capRejected": set(), "sliverRejected": 0, "reconnected": 0}

    # --- the spacing cap ------------------------------------------------
    # Nearest other node for every node in the combined set, then a robust
    # central value of those.  The median rather than the mean, so one
    # isolated boss cannot drag the limit up.
    nn = []
    for i in range(len(pts)):
        best = None
        for j in range(len(pts)):
            if i == j:
                continue
            dd = nrm(sub(pts[j], pts[i]))
            if best is None or dd < best:
                best = dd
        if best is not None:
            nn.append(best)
    nn_median = sorted(nn)[len(nn) // 2] if nn else 0.0
    nn_cap = nn_median * nn_multiple if abs_cap is None else abs_cap

    def blocked(a, b):
        L = nrm(sub(pts[b], pts[a]))
        if L < 1e-9:
            return True
        u = mul(sub(pts[b], pts[a]), 1.0 / L)
        v = (-u[1], u[0])
        for c in range(len(pts)):
            if c == a or c == b or radii[c] <= 0:
                continue
            rel = sub(pts[c], pts[a])
            along = dot(rel, u)
            if along <= radii[a] or along >= L - radii[b]:
                continue
            if abs(dot(rel, v)) < radii[c] + rib_half:
                return True
        return False

    def keep(a, b, cap):
        L = nrm(sub(pts[b], pts[a]))
        if L - radii[a] - radii[b] <= rib_half:
            return False
        lim = cap
        if cap > 0 and local_scale and nn:
            # The median is the floor, not the whole answer.  A node with
            # nothing near it is entitled to reach as far as its own
            # neighbourhood, or an isolated boss on an otherwise crowded
            # plate loses every rib it has.
            lim = cap * max(1.0, max(nn[a], nn[b]) / max(nn_median, 1e-9))
        if lim > 0 and L > lim:
            stats["capRejected"].add(tuple(sorted((a, b))))
            return False
        return not blocked(a, b)

    def in_pocket(p):
        """qContainsPoint(tool, ...) before any rib is cut."""
        if not (rect[0] <= p[0] <= rect[2] and rect[1] <= p[1] <= rect[3]):
            return False
        for isl in islands:
            if nrm(sub(p, isl["center"])) <= isl["r"] + tool_rad:
                return False
        return True

    chord_probe = max(0.03, s["rib"] / 4)

    def crosses_pocket(a, b):
        L = nrm(sub(pts[b], pts[a]))
        if L < 1e-9:
            return False
        u = mul(sub(pts[b], pts[a]), 1.0 / L)
        v = (-u[1], u[0])
        for frac in (0.25, 0.5, 0.75):
            q = add(pts[a], mul(u, L * frac))
            for sgn in (-1, 1):
                if not in_pocket(add(q, mul(v, sgn * chord_probe))):
                    return False
        return True

    ext_cap = 3.0

    def reach_of(frm, at):
        d = sub(pts[at], frm)
        d_len = nrm(d)
        if d_len < 1e-9:
            return {"anchored": False, "extension": 0.0}
        return frc_wall_extension(grow, mul(d, 1.0 / d_len), wall_dir[at], ext_cap)

    def median_of(vals):
        if not vals:
            return 0.0
        srt = sorted(vals)
        return srt[len(srt) // 2]

    def edges_of(idx):
        local = [pts[i] for i in idx]
        seen, third = [], []
        for t in frc_delaunay(local):
            for pr in ([t[0], t[1], t[2]], [t[1], t[2], t[0]], [t[2], t[0], t[1]]):
                lo, hi = min(idx[pr[0]], idx[pr[1]]), max(idx[pr[0]], idx[pr[1]])
                at = -1
                for k in range(len(seen)):
                    if seen[k][0] == lo and seen[k][1] == hi:
                        at = k
                if at < 0:
                    seen.append([lo, hi])
                    third.append([idx[pr[2]]])
                else:
                    third[at].append(idx[pr[2]])
        return {"seen": seen, "third": third}

    all_idx = list(range(len(pts)))
    mg = edges_of(all_idx)
    mg_set = {(sv[0], sv[1]) for sv in mg["seen"]}

    all_pairs = []

    def add_pair(lst, a, b):
        lo, hi = min(a, b), max(a, b)
        for sv in lst:
            if sv[0] == lo and sv[1] == hi:
                return lst
        return lst + [[lo, hi]]

    # Two bosses are neighbours only if they stay neighbours once the wall
    # stations are in the set.  The boss only triangulation has to exist, or
    # the middle of the plate gets no bracing at all, but on a plate with few
    # bosses it also joins bosses that have a wall anchor between them, and
    # those are the spans that read as ribs between holes far apart.
    def local_ok(a, b):
        if not (fixed and locality):
            return True
        return (min(a, b), max(a, b)) in mg_set

    # --- bosses on their own -------------------------------------------
    boss_idx = list(range(n_hole))
    b_cap = 0.0
    if n_hole == 2:
        cap2 = nn_cap if fixed else 0.0
        if keep(0, 1, cap2):
            all_pairs = add_pair(all_pairs, 0, 1)
    elif n_hole >= 3:
        bg = edges_of(boss_idx)
        b_lens = [nrm(sub(pts[sv[1]], pts[sv[0]])) for sv in bg["seen"]]
        b_cap = nn_cap if fixed else median_of(b_lens) * 2.4
        for sv in bg["seen"]:
            if local_ok(sv[0], sv[1]) and keep(sv[0], sv[1], b_cap):
                all_pairs = add_pair(all_pairs, sv[0], sv[1])
        for k in range(len(bg["seen"])):
            if len(bg["third"][k]) != 2:
                continue
            lo2, hi2 = min(bg["third"][k]), max(bg["third"][k])
            d_this = nrm(sub(pts[bg["seen"][k][1]], pts[bg["seen"][k][0]]))
            d_that = nrm(sub(pts[hi2], pts[lo2]))
            if d_that > d_this * 1.35 or d_this > d_that * 1.35:
                continue
            if local_ok(lo2, hi2) and keep(lo2, hi2, b_cap):
                all_pairs = add_pair(all_pairs, lo2, hi2)

    # --- boss to wall ---------------------------------------------------
    m_lens = [nrm(sub(pts[sv[1]], pts[sv[0]])) for sv in mg["seen"]
              if is_hole[sv[0]] != is_hole[sv[1]]]
    m_cap = nn_cap if (fixed and cap_walls) else median_of(m_lens) * 2.2
    wall = []
    for sv in mg["seen"]:
        if is_hole[sv[0]] == is_hole[sv[1]]:
            continue
        if not keep(sv[0], sv[1], m_cap):
            continue
        h = sv[0] if is_hole[sv[0]] else sv[1]
        w = sv[1] if is_hole[sv[0]] else sv[0]
        if not reach_of(pts[h], w)["anchored"]:
            continue
        wall.append([nrm(sub(pts[w], pts[h])), h, w])
    wall.sort(key=lambda t: t[0])
    per_boss = [0] * len(pts)
    for t in wall:
        h = t[1]
        if per_boss[h] >= 4:
            continue
        per_boss[h] += 1
        all_pairs = add_pair(all_pairs, h, t[2])

    # --- wall to wall across an empty region -----------------------------
    if n_hole > 0:
        spanning = []
        for sv in mg["seen"]:
            if is_hole[sv[0]] or is_hole[sv[1]]:
                continue
            if not keep(sv[0], sv[1], 0.0):
                continue
            if nrm(sub(pts[sv[1]], pts[sv[0]])) < pocket_used:
                continue
            if (not reach_of(pts[sv[1]], sv[0])["anchored"]
                    or not reach_of(pts[sv[0]], sv[1])["anchored"]):
                continue
            spanning.append([nrm(sub(pts[sv[1]], pts[sv[0]])), sv[0], sv[1]])
        spanning.sort(key=lambda t: t[0])
        span_budget = max(6, len(stations))
        spanned = 0
        for t in spanning:
            if spanned >= span_budget:
                break
            if not crosses_pocket(t[1], t[2]):
                continue
            all_pairs = add_pair(all_pairs, t[1], t[2])
            spanned += 1

    # --- the sliver filter and the boss connectivity guarantee ------------
    # Regions a rib bounds, each with its smallest interior angle.
    #
    # Two shapes matter.  A graph triangle is three ribs.  A wall wedge is two
    # ribs leaving one node for two stations that are neighbours among the
    # stations that carry ribs, closed by the run of wall between them: that
    # is the long thin triangle a boss makes against the outline, and it does
    # not exist as a triangle in the rib graph at all.
    n_st = len(stations)

    def regions(pairs):
        adj = {i: set() for i in range(len(pts))}
        for a, b in pairs:
            adj[a].add(b)
            adj[b].add(a)
        segs_l = [(pts[a], pts[b]) for a, b in pairs]

        def uncrossed(poly):
            if not use_cross:
                return True
            for (p1, p2) in segs_l:
                for i in range(len(poly)):
                    if seg_cross(p1, p2, poly[i], poly[(i + 1) % len(poly)]):
                        return False
            return True

        out = []
        seen = set()
        for a, b in pairs:
            for c in adj[a] & adj[b]:
                key = tuple(sorted((a, b, c)))
                if key in seen:
                    continue
                seen.add(key)
                A, B, C = pts[key[0]], pts[key[1]], pts[key[2]]
                if abs((B[0] - A[0]) * (C[1] - A[1])
                       - (C[0] - A[0]) * (B[1] - A[1])) < 1e-9:
                    continue
                if any(m not in key and point_in_tri(pts[m], A, B, C)
                       for m in range(len(pts))):
                    continue
                if not uncrossed([A, B, C]):
                    continue
                sides = [(key[0], key[1]), (key[1], key[2]), (key[0], key[2])]
                out.append((min(tri_angles(A, B, C)), sides))

        ribbed = [n_hole + i for i in range(n_st) if adj[n_hole + i]]
        for k in range(len(ribbed)):
            b = ribbed[k]
            c = ribbed[(k + 1) % len(ribbed)]
            if b == c:
                continue
            nb = (b - n_hole + 1) % n_st + n_hole
            pc = (c - n_hole - 1) % n_st + n_hole
            for a in adj[b] & adj[c]:
                A, B, C = pts[a], pts[b], pts[c]
                if abs((B[0] - A[0]) * (C[1] - A[1])
                       - (C[0] - A[0]) * (B[1] - A[1])) < 1e-9:
                    continue
                if not uncrossed([A, B, C]):
                    continue

                def ang(o, p, q):
                    du = sub(p, o)
                    dv = sub(q, o)
                    if nrm(du) < 1e-9 or nrm(dv) < 1e-9:
                        return 180.0
                    du = mul(du, 1.0 / nrm(du))
                    dv = mul(dv, 1.0 / nrm(dv))
                    return math.degrees(math.acos(max(-1.0, min(1.0, dot(du, dv)))))
                # The wall leaves b heading for its own next station and
                # leaves c heading back, so the corners of the region are
                # measured against the outline, not against a chord that
                # would cut straight across the pocket.
                worst = min(ang(A, B, C), ang(B, A, pts[nb]), ang(C, A, pts[pc]))
                out.append((worst, [(a, b), (a, c)]))
        return out

    def boss_degree(pairs):
        deg = {}
        for a, b in pairs:
            for i in (a, b):
                if i < n_hole:
                    deg[i] = deg.get(i, 0) + 1
        return deg

    if fixed:
        # A rib is dropped only if the region it bounds is a sliver and it is
        # the longest side that can go.  Every side tied for longest goes
        # together, so a mirrored pair of slivers is resolved the same way on
        # both sides of a symmetric plate.
        for _ in range(40):
            doomed = set()
            for ang, sides in regions(all_pairs):
                if ang >= sliver_deg:
                    continue
                deg = boss_degree(all_pairs)
                cand = [sd for sd in sides
                        if not (sd[0] < n_hole and deg.get(sd[0], 0) <= 2)
                        and not (sd[1] < n_hole and deg.get(sd[1], 0) <= 2)]
                if not cand:
                    continue
                longest = max(nrm(sub(pts[x], pts[y])) for x, y in cand)
                for x, y in cand:
                    if nrm(sub(pts[x], pts[y])) > longest - 1e-9:
                        doomed.add(tuple(sorted((x, y))))
            if not doomed:
                break
            all_pairs = [q for q in all_pairs
                         if tuple(sorted(q)) not in doomed]
            stats["sliverRejected"] += len(doomed)

        # A boss the cap or the filter has stripped is worse than a long rib.
        # Two ribs is the least that holds a ring against a turning tool, and
        # the nearest wall anchors are the right two for an isolated boss.
        # A candidate that would open a new sliver is passed over first, so
        # this pass cannot undo the one above; if none will do, the boss is
        # connected anyway, because a ring cut loose is worse than a sliver.
        for h in range(n_hole):
            # Three tries, each giving up one condition.  A clean rib to a
            # near anchor first, then one that opens a sliver, then one that
            # crosses another rib, because a ring the cut leaves loose in the
            # plate is worse than either.
            for fussy, planar in [(True, True), (False, True), (False, False)]:
                cands = []
                for w in range(n_hole, len(pts)):
                    if not keep(h, w, 0.0):
                        continue
                    if not reach_of(pts[h], w)["anchored"]:
                        continue
                    if planar and any(seg_cross(pts[h], pts[w],
                                                pts[q[0]], pts[q[1]])
                                      for q in all_pairs):
                        continue
                    cands.append((nrm(sub(pts[w], pts[h])), w))
                cands.sort()
                tried = 0
                for _, w in cands:
                    if len([q for q in all_pairs
                            if q[0] == h or q[1] == h]) >= 2:
                        break
                    if fussy and tried >= 8:
                        break
                    tried += 1
                    trial = add_pair(all_pairs, h, w)
                    if len(trial) == len(all_pairs):
                        continue
                    if fussy and min([a for a, _ in regions(trial)],
                                     default=180.0) < sliver_deg:
                        continue
                    all_pairs = trial
                    stats["reconnected"] += 1

    # --- extensions and the bar list -------------------------------------
    segs = []
    for pr in all_pairs:
        r0 = {"anchored": True, "extension": 0.0}
        r1 = {"anchored": True, "extension": 0.0}
        if not is_hole[pr[0]]:
            r0 = reach_of(pts[pr[1]], pr[0])
        if not is_hole[pr[1]]:
            r1 = reach_of(pts[pr[0]], pr[1])
        if not r0["anchored"] or not r1["anchored"]:
            continue
        segs.append({"a": pts[pr[0]], "b": pts[pr[1]],
                     "e0": r0["extension"], "e1": r1["extension"],
                     "ia": pr[0], "ib": pr[1]})

    reg = regions([[sg["ia"], sg["ib"]] for sg in segs])
    min_ang = min([t[0] for t in reg], default=float("nan"))

    free_ends = 0
    for sg in segs:
        L = nrm(sub(sg["b"], sg["a"]))
        u = mul(sub(sg["b"], sg["a"]), 1.0 / L)
        for tip in (add(sg["a"], mul(u, -sg["e0"])),
                    add(sg["b"], mul(u, sg["e1"]))):
            if in_pocket(tip):
                free_ends += 1

    return {
        "s": s, "toolRad": tool_rad, "rect": rect, "islands": islands,
        "stations": stations, "pts": pts, "isHole": is_hole,
        "segs": segs, "nnMedian": nn_median, "nnCap": nn_cap,
        "bCap": b_cap, "mCap": m_cap, "stats": stats,
        "minAngle": min_ang, "freeEnds": free_ends,
        "longest": max((nrm(sub(sg["b"], sg["a"])) for sg in segs), default=0.0),
        "pocketUsed": pocket_used, "plate": plate, "holes": holes,
    }
