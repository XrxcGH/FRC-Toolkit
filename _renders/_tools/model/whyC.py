"""Transliteration of the truss pocket loop as it stands in FRC Plate
Geometry.txt today, with a reason recorded for every triangle dropped."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truss import (frc_min_corner_radius, frc_delaunay, perimeter_stations,
                   nrm, sub, add, mul, dot, seg_cross, frc_min_wall)
from truss2 import in_polygon, poly_area2, push_outward, seg_dist
from flips import cocircular_flips, mirror_axes
_raw_delaunay = frc_delaunay
def frc_delaunay(nds):
    if not FLIPS:
        return _raw_delaunay(nds)
    return cocircular_flips(nds, _raw_delaunay(nds))


SLEND = {"AL_6061": 16.3}
REFINE = "cocirc"
MERGE_MODE = "none"
MERGE_R = 1.0
PULL = True
COTOL = 1e-6
COST = [0, 0]
FLIPS = True
AXIS = True
AXIS_STEP = 1.0
AXIS_WALL = 1.0
BLOCKED_MINUS_INSET = False


def sizing(thickness, tool_dia=0.25, aggression="BALANCED",
           loading="ACROSS_FACE", material="AL_6061"):
    """Tracks frcLightenSizes in FRC Plate Geometry.txt as of this session."""
    K = {"CONSERVATIVE": dict(wall=1.5, hole=.50, rib=1.25, span=8, buckle=.75),
         "BALANCED": dict(wall=1.0, hole=.35, rib=.90, span=12, buckle=.90),
         "AGGRESSIVE": dict(wall=.75, hole=.25, rib=.70, span=18, buckle=1.0)}[aggression]
    floor_min = frc_min_wall(tool_dia)
    rib = min(max(K["rib"] * thickness, floor_min), 0.5)
    buckle_span = max(min(rib, thickness), 0.0) * SLEND[material]
    buckle_pocket = max(0.05, (math.sqrt(3) / 2) * buckle_span - rib)
    beam_pocket = K["span"] * thickness
    want = beam_pocket
    if loading == "EDGE_ON":
        want = max(0.05, (math.sqrt(3) / 2) * (K["buckle"] * buckle_span) - rib)
    elif loading == "NON_STRUCTURAL":
        want = max(beam_pocket, buckle_pocket)
    want_pocket = min(max(want, 0.4), 4.0)
    return dict(wall=min(max(K["wall"] * thickness, floor_min), 0.5), rib=rib,
                pocket=min(want_pocket, buckle_pocket), holeFactor=K["hole"],
                buckleSpan=buckle_span, bucklePocket=buckle_pocket,
                beam=beam_pocket)


def side2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def build(plate, holes, thickness=0.125, tool_dia=0.25, aggression="BALANCED",
          loading="ACROSS_FACE", node_cap=240, boss_clear=0.50,
          space_mult=0.66, wall_clear=0.45, station_mult=1.15, merge=True,
          blocked_test=True, opp_test=True, pattern_angle=0.0,
          boss_ring_nodes=0, merge_grow=True, plain_fallback=False):
    s = sizing(thickness, tool_dia, aggression, loading)
    tool_rad = frc_min_corner_radius(tool_dia)
    W, H = plate
    off = s["wall"] + tool_rad
    rect = (off, off, W - off, H - off)
    islands = []
    for (cx, cy, dia) in holes:
        prot = dia / 2 + s["wall"]
        need = min(max(s["holeFactor"] * dia, s["wall"]), 0.5)
        if need > s["wall"] + 1e-6:
            prot = dia / 2 + need
        islands.append({"center": (cx, cy), "r": prot})
    c2 = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
    span_x, span_y = rect[2] - rect[0], rect[3] - rect[1]
    size_cap = max(min(span_x, span_y) / 3, 0.3)
    pocket_used = min(s["pocket"], size_cap)
    reach = math.hypot(span_x, span_y) / 2 + pocket_used
    u_inset = s["rib"] / 2 + tool_rad
    slv_w = max(0.02, tool_dia - 2 * tool_rad)
    min_inr = u_inset + max(0.6 * tool_rad, slv_w)
    min_tri = 2 * math.sqrt(3) * min_inr
    want = 2 * (pocket_used + s["rib"]) / math.sqrt(3)
    edge_max = max(want, 1.3 * min_tri)
    space = space_mult * edge_max
    wclear = wall_clear * edge_max
    bclear = boss_clear * edge_max
    slv_area = (0.6 * s["rib"]) ** 2
    min_run = max(0.02, slv_w)

    stations = perimeter_stations(rect, edge_max / station_mult)
    gap = min(0.01, s["wall"] / 20)
    push = max(0.0, min(u_inset - gap, s["wall"] + tool_rad))
    outer = push_outward([st["point"] for st in stations], push)

    order = sorted(range(len(islands)), key=lambda j: (-islands[j]["r"], j))
    boss_at, boss_rad, boss_idx, merged = [], [], [], 0
    for j in order:
        cq = islands[j]["center"]
        rq = islands[j]["r"] + tool_rad
        hit = -1
        for k in range(len(boss_at)):
            if merge and nrm(sub(cq, boss_at[k])) < rq + boss_rad[k]:
                hit = k
                break
        if hit >= 0:
            if merge_grow:
                boss_rad[hit] = max(boss_rad[hit], nrm(sub(cq, boss_at[hit])) + rq)
            merged += 1
            continue
        boss_at.append(cq)
        boss_rad.append(rq)
        boss_idx.append(j)
    nodes = list(outer)
    radius = [0.0] * len(outer)
    for (_, k) in sorted([(boss_idx[k], k) for k in range(len(boss_at))]):
        nodes.append(boss_at[k])
        radius.append(boss_rad[k])

    def wall_dist(q):
        return min(seg_dist(q, outer[i], outer[(i + 1) % len(outer)])
                   for i in range(len(outer)))

    def room_for(q):
        if not in_polygon(q, outer):
            return False
        if wall_dist(q) < wclear:
            return False
        for i in range(len(nodes)):
            lim = space if radius[i] <= 0 else max(space, radius[i] + bclear)
            if nrm(sub(q, nodes[i])) < lim:
                return False
        return True

    naxis = [0]
    if AXIS:
        sym = mirror_axes(nodes)
        xs = [n[0] for n in nodes]
        ys = [n[1] for n in nodes]
        step = AXIS_STEP * edge_max
        def offer(q):
            if len(nodes) >= node_cap:
                return
            if not in_polygon(q, outer):
                return
            if wall_dist(q) < AXIS_WALL * wclear:
                return
            for i in range(len(nodes)):
                lim = space if radius[i] <= 0 else max(space, radius[i] + bclear)
                if nrm(sub(q, nodes[i])) < lim:
                    return
            nodes.append(q)
            radius.append(0.0)
            naxis[0] += 1
        runs = []
        if sym["useX"]:
            runs.append(("v", sym["ax"], min(ys), max(ys),
                         sym["ay"] if sym["useY"] else (min(ys) + max(ys)) / 2.0))
        if sym["useY"]:
            runs.append(("h", sym["ay"], min(xs), max(xs),
                         sym["ax"] if sym["useX"] else (min(xs) + max(xs)) / 2.0))
        for (kind, at, lo, hi, mid) in runs:
            n = int(math.ceil((hi - lo) / step)) + 2
            seq = [0.0]
            for k in range(1, n + 1):
                seq.append(k * step)
                seq.append(-k * step)
            for d in seq:
                t = mid + d
                if t < lo - 1e-9 or t > hi + 1e-9:
                    continue
                offer((at, t) if kind == "v" else (t, at))

    # optional: ring nodes around each big boss, the experiment for the fix
    if boss_ring_nodes > 0:
        nb = len(nodes)
        for i in range(nb):
            if radius[i] <= 0:
                continue
            rr0 = radius[i] + max(space, radius[i] + bclear) * 0.0
            for j in range(boss_ring_nodes):
                a = 2 * math.pi * j / boss_ring_nodes
                q = (nodes[i][0] + (radius[i] + u_inset * 2 + 0.35 * edge_max) * math.cos(a),
                     nodes[i][1] + (radius[i] + u_inset * 2 + 0.35 * edge_max) * math.sin(a))
                if room_for(q):
                    nodes.append(q)
                    radius.append(0.0)

    def lattice(centre, rch, pitch, angle):
        row = pitch * math.sqrt(3) / 2
        nr = int(math.ceil(rch / row)) + 1
        nc = int(math.ceil(rch / pitch)) + 1
        u = (math.cos(angle), math.sin(angle))
        v = (-math.sin(angle), math.cos(angle))
        out = []
        for rr in range(-nr, nr + 1):
            o = 0.0 if rr % 2 == 0 else pitch / 2
            for cc in range(-nc, nc + 1):
                out.append(add(centre, add(mul(u, cc * pitch + o), mul(v, rr * row))))
        return out

    capped = False
    nlat = 0
    nste = 0
    cand = lattice(c2, reach, edge_max, pattern_angle)
    cand.sort(key=lambda q: (round(nrm(sub(q, c2)), 6),
                             round(math.atan2(q[1] - c2[1], q[0] - c2[0]), 6)))
    for q in cand:
        if len(nodes) >= node_cap:
            capped = True
            break
        if room_for(q):
            nodes.append(q)
            radius.append(0.0)
            nlat += 1

    def keep_tri(nds, t):
        a, b, c = nds[t[0]], nds[t[1]], nds[t[2]]
        cen = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3)
        if not in_polygon(cen, outer):
            return False
        for (q0, q1, w) in ((a, b, c), (b, c, a), (c, a, b)):
            m = ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2)
            if not in_polygon((m[0] + 0.15 * (w[0] - m[0]),
                               m[1] + 0.15 * (w[1] - m[1])), outer):
                return False
            for i in range(len(outer)):
                if seg_cross(q0, q1, outer[i], outer[(i + 1) % len(outer)]):
                    return False
        return True

    def mesh(nds):
        out, seen = [], set()
        for t in frc_delaunay(nds):
            key = tuple(sorted(t))
            if len(set(key)) < 3 or key in seen:
                continue
            seen.add(key)
            if keep_tri(nds, t):
                out.append(t)
        return out

    tris = mesh(nodes)
    for _p in range(4):
        want_l = []
        for t in tris:
            a, b, c = nodes[t[0]], nodes[t[1]], nodes[t[2]]
            lg = max(nrm(sub(b, a)), nrm(sub(c, b)), nrm(sub(a, c)))
            if lg > edge_max:
                if REFINE == "cocirc":
                    d = 2.0 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1])
                               + c[0] * (a[1] - b[1]))
                    q = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)
                    if abs(d) > 1e-12:
                        ua = a[0] * a[0] + a[1] * a[1]
                        ub = b[0] * b[0] + b[1] * b[1]
                        uc = c[0] * c[0] + c[1] * c[1]
                        cc = ((ua * (b[1] - c[1]) + ub * (c[1] - a[1]) + uc * (a[1] - b[1])) / d,
                              (ua * (c[0] - b[0]) + ub * (a[0] - c[0]) + uc * (b[0] - a[0])) / d)
                        R2 = (a[0]-cc[0])**2 + (a[1]-cc[1])**2
                        tol2 = 1e-6 * max(1.0, R2)
                        COST[0] += 1
                        for i in range(len(nodes)):
                            COST[1] += 1
                            if i in t:
                                continue
                            if abs((nodes[i][0]-cc[0])**2 + (nodes[i][1]-cc[1])**2 - R2) < tol2:
                                q = cc
                                break
                    want_l.append((-lg, q))
                elif REFINE in ("circum", "circumc", "circumm"):
                    d = 2.0 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1])
                               + c[0] * (a[1] - b[1]))
                    cen = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)
                    if abs(d) < 1e-12:
                        q = cen
                    else:
                        ua = a[0] * a[0] + a[1] * a[1]
                        ub = b[0] * b[0] + b[1] * b[1]
                        uc = c[0] * c[0] + c[1] * c[1]
                        q = ((ua * (b[1] - c[1]) + ub * (c[1] - a[1]) + uc * (a[1] - b[1])) / d,
                             (ua * (c[0] - b[0]) + ub * (a[0] - c[0]) + uc * (b[0] - a[0])) / d)
                        if REFINE in ("circumc", "circumm"):
                            # clamp toward the centroid if the circumcentre is
                            # outside the triangle
                            s0 = side2(a, b, q); s1 = side2(b, c, q); s2 = side2(c, a, q)
                            sg = side2(a, b, c)
                            if not ((s0 >= 0) == (sg >= 0) and (s1 >= 0) == (sg >= 0)
                                    and (s2 >= 0) == (sg >= 0)):
                                if REFINE == "circumc":
                                    q = cen
                                else:
                                    if nrm(sub(b, a)) >= nrm(sub(c, b)) and nrm(sub(b, a)) >= nrm(sub(a, c)):
                                        z0, z1 = a, b
                                    elif nrm(sub(c, b)) >= nrm(sub(a, c)):
                                        z0, z1 = b, c
                                    else:
                                        z0, z1 = c, a
                                    q = ((z0[0] + z1[0]) / 2, (z0[1] + z1[1]) / 2)
                    want_l.append((-lg, q))
                elif REFINE == "midlong":
                    if nrm(sub(b, a)) >= nrm(sub(c, b)) and nrm(sub(b, a)) >= nrm(sub(a, c)):
                        q0, q1 = a, b
                    elif nrm(sub(c, b)) >= nrm(sub(a, c)):
                        q0, q1 = b, c
                    else:
                        q0, q1 = c, a
                    want_l.append((-lg, ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2)))
                else:
                    want_l.append((-lg, ((a[0] + b[0] + c[0]) / 3,
                                         (a[1] + b[1] + c[1]) / 3)))
        if not want_l:
            break
        want_l.sort(key=lambda e: round(e[0], 9))
        if MERGE_MODE != "none":
            uniq = []
            for (sc, q) in want_l:
                dup = False
                for u in uniq:
                    if abs(u[1][0] - q[0]) < 1e-6 and abs(u[1][1] - q[1]) < 1e-6:
                        dup = True
                        break
                if not dup:
                    uniq.append((sc, q))
            merged_l = []
            for (sc, q) in uniq:
                sx = sy = 0.0; n = 0
                for (s2, q2) in uniq:
                    if MERGE_MODE == "tie" and abs(s2 - sc) > 1e-9:
                        continue
                    if nrm(sub(q, q2)) < MERGE_R * space:
                        sx += q2[0]; sy += q2[1]; n += 1
                merged_l.append((sc, (sx / n, sy / n)))
            want_l = merged_l
        added = 0
        pass_start = len(nodes)
        pass_score = {}
        for (_sc, q) in want_l:
            if len(nodes) >= node_cap:
                capped = True
                break
            if room_for(q):
                pass_score[len(nodes)] = _sc
                nodes.append(q)
                radius.append(0.0)
                added += 1
                nste += 1
            elif PULL:
                # Rejected. If exactly one node blocks it, and that node was
                # placed in this same pass with the same score, the two are a
                # tie the scan could only break by order. Move that node to the
                # mean of the pair instead, which is where a mirrored pair puts
                # it on the axis.
                if not in_polygon(q, outer) or wall_dist(q) < wclear:
                    continue
                blk = -1
                nblk = 0
                for i in range(len(nodes)):
                    lim = space if radius[i] <= 0 else max(space, radius[i] + bclear)
                    if nrm(sub(q, nodes[i])) < lim:
                        nblk += 1
                        blk = i
                if nblk != 1 or blk < pass_start or radius[blk] > 0:
                    continue
                if abs(pass_score.get(blk, 1e9) - _sc) > 1e-9:
                    continue
                m = ((q[0] + nodes[blk][0]) / 2, (q[1] + nodes[blk][1]) / 2)
                if not in_polygon(m, outer) or wall_dist(m) < wclear:
                    continue
                bad = False
                for i in range(len(nodes)):
                    if i == blk:
                        continue
                    lim = space if radius[i] <= 0 else max(space, radius[i] + bclear)
                    if nrm(sub(m, nodes[i])) < lim:
                        bad = True
                        break
                if not bad:
                    nodes[blk] = m
        if added == 0:
            break
        tris = mesh(nodes)

    reasons = {}
    drops = []
    kept = []
    polys = []
    for t in tris:
        p = [nodes[t[0]], nodes[t[1]], nodes[t[2]]]
        rr = [radius[t[0]], radius[t[1]], radius[t[2]]]
        raw = abs(poly_area2(p)) / 2
        cen = ((p[0][0] + p[1][0] + p[2][0]) / 3,
               (p[0][1] + p[1][1] + p[2][1]) / 3)

        def drop(w):
            reasons[w] = reasons.get(w, 0) + 1
            drops.append((w, raw, cen))
        if side2(p[0], p[1], p[2]) < 0:
            p = [p[0], p[2], p[1]]
            rr = [rr[0], rr[2], rr[1]]
        ar2 = abs(side2(p[0], p[1], p[2]))
        per = nrm(sub(p[1], p[0])) + nrm(sub(p[2], p[1])) + nrm(sub(p[0], p[2]))
        if per < 1e-9 or ar2 / per <= u_inset:
            drop("inradius")
            continue
        blocked = False
        if blocked_test:
            for i in range(len(nodes)):
                if radius[i] <= 0 or i in t:
                    continue
                cq = nodes[i]
                near = min(seg_dist(cq, p[0], p[1]), seg_dist(cq, p[1], p[2]),
                           seg_dist(cq, p[2], p[0]))
                if (side2(p[0], p[1], cq) > 0 and side2(p[1], p[2], cq) > 0
                        and side2(p[2], p[0], cq) > 0):
                    near = 0.0
                thr = radius[i] - u_inset if BLOCKED_MINUS_INSET else radius[i]
                if near < thr:
                    blocked = True
                    break
        if blocked:
            drop("blockedBoss")
            continue
        us, lineN, lineK = [], [], []
        for i in range(3):
            u = mul(sub(p[(i + 1) % 3], p[i]), 1.0 / nrm(sub(p[(i + 1) % 3], p[i])))
            nv = (-u[1], u[0])
            us.append(u)
            lineN.append(nv)
            lineK.append(dot(p[i], nv) + u_inset)
        corner = []
        ok = True
        for i in range(3):
            n0, k0 = lineN[(i + 2) % 3], lineK[(i + 2) % 3]
            n1, k1 = lineN[i], lineK[i]
            det = n0[0] * n1[1] - n0[1] * n1[0]
            if abs(det) < 1e-12:
                ok = False
                break
            corner.append(((k0 * n1[1] - n0[1] * k1) / det,
                           (n0[0] * k1 - k0 * n1[0]) / det))
        if not ok:
            drop("degenCorner")
            continue
        tStart = [0.0] * 3
        tStop = [0.0] * 3
        for i in range(3):
            tStop[i] = dot(sub(corner[(i + 1) % 3], corner[i]), us[i])
        arcA = [None] * 3
        why = None
        for i in range(3):
            if rr[i] <= 0 or nrm(sub(corner[i], p[i])) >= rr[i] - 0.02:
                continue
            jj = (i + 1) % 3
            if opp_test and rr[i] >= dot(lineN[jj], p[i]) - lineK[jj]:
                ok = False
                why = "oppositeLine"
                break
            prev = (i + 2) % 3
            w1 = sub(corner[i], p[i])
            b1 = 2 * dot(w1, us[i])
            c1 = dot(w1, w1) - rr[i] ** 2
            d1 = b1 * b1 - 4 * c1
            w0 = sub(corner[prev], p[i])
            b0 = 2 * dot(w0, us[prev])
            c0 = dot(w0, w0) - rr[i] ** 2
            d0 = b0 * b0 - 4 * c0
            if d1 <= 0 or d0 <= 0:
                ok = False
                why = "noCrossing"
                break
            tStart[i] = (-b1 + math.sqrt(d1)) / 2
            tStop[prev] = (-b0 - math.sqrt(d0)) / 2
            arcA[i] = (add(corner[prev], mul(us[prev], tStop[prev])),
                       add(corner[i], mul(us[i], tStart[i])), rr[i], p[i])
        plain = False
        if not ok:
            if not plain_fallback:
                drop(why)
                continue
            plain = True
            ok = True
            arcA = [None] * 3
            tStart = [0.0] * 3
            for i in range(3):
                tStop[i] = dot(sub(corner[(i + 1) % 3], corner[i]), us[i])
        if not plain:
            for i in range(3):
                if tStop[i] - tStart[i] < min_run:
                    ok = False
            if not ok:
                if not plain_fallback:
                    drop("shortRun")
                    continue
                plain = True
                ok = True
                arcA = [None] * 3
                tStart = [0.0] * 3
                for i in range(3):
                    tStop[i] = dot(sub(corner[(i + 1) % 3], corner[i]), us[i])
        pl = []
        poly = []
        arc_cut = 0.0
        for i in range(3):
            if arcA[i] is not None:
                a_pt, b_pt, ri, pi = arcA[i]
                bis = add(sub(a_pt, pi), sub(b_pt, pi))
                if nrm(bis) < 1e-9:
                    ok = False
                    break
                th = 2 * math.asin(min(1.0, nrm(sub(b_pt, a_pt)) / (2 * ri)))
                arc_cut += (ri * ri / 2) * (th - math.sin(th))
                pl.append(a_pt)
                a0 = math.atan2(a_pt[1] - pi[1], a_pt[0] - pi[0])
                a1 = math.atan2(b_pt[1] - pi[1], b_pt[0] - pi[0])
                dd = a1 - a0
                while dd > 0:
                    dd -= 2 * math.pi
                while dd < -2 * math.pi:
                    dd += 2 * math.pi
                nseg = max(2, int(abs(dd) / 0.08))
                for j in range(nseg + 1):
                    a = a0 + dd * j / nseg
                    poly.append((pi[0] + ri * math.cos(a), pi[1] + ri * math.sin(a)))
            sPt = add(corner[i], mul(us[i], tStart[i]))
            ePt = add(corner[i], mul(us[i], tStop[i]))
            pl.append(sPt)
            pl.append(ePt)
            poly.append(sPt)
            poly.append(ePt)
        if not ok:
            drop("bisector")
            continue
        area2 = 0.0
        for i in range(len(pl)):
            q = pl[(i + 1) % len(pl)]
            area2 += pl[i][0] * q[1] - q[0] * pl[i][1]
        boss_cut = 0.0
        if plain:
            # the ring at each corner takes a wedge of the inset triangle
            for i in range(3):
                if rr[i] <= 0:
                    continue
                e0 = sub(corner[(i + 1) % 3], corner[i])
                e1 = sub(corner[(i + 2) % 3], corner[i])
                if nrm(e0) < 1e-9 or nrm(e1) < 1e-9:
                    continue
                ca = max(-1.0, min(1.0, dot(e0, e1) / (nrm(e0) * nrm(e1))))
                boss_cut += 0.5 * rr[i] * rr[i] * math.acos(ca)
        net = abs(area2) / 2 - arc_cut - boss_cut
        if net < slv_area:
            drop("tooSmall" if not plain else "swallowed")
            continue
        kept.append((t, net))
        polys.append(poly)
    return dict(polys=polys, s=s, nodes=nodes, radius=radius, outer=outer, tris=tris,
                kept=kept, reasons=reasons, drops=drops, edge_max=edge_max,
                capped=capped, nlat=nlat, naxis=naxis[0], nste=nste, merged=merged,
                islands=islands, pocket_used=pocket_used, plate=plate,
                tool_rad=tool_rad, u_inset=u_inset)


def report(tag, plate, holes, **kw):
    r = build(plate, holes, **kw)
    W, H = plate
    tot = W * H
    da = sum(d[1] for d in r["drops"])
    ka = sum(k[1] for k in r["kept"])
    print("%-30s edge %.2f nodes %3d(lat %2d st %2d) tri %3d kept %3d "
          "drop %2d dropArea %5.2f in2 (%4.1f%%) pocketArea %5.2f (%4.1f%%) "
          "merged %d capped %s"
          % (tag, r["edge_max"], len(r["nodes"]), r["nlat"], r["nste"],
             len(r["tris"]), len(r["kept"]), len(r["drops"]), da,
             100 * da / tot, ka, 100 * ka / tot, r["merged"], r["capped"]))
    if r["reasons"]:
        print("     reasons: " + ", ".join("%s=%d" % kv
                                           for kv in sorted(r["reasons"].items())))
        for (w, a, c) in sorted(r["drops"], key=lambda d: -d[1])[:6]:
            print("        %-13s %6.2f in2 at (%5.2f, %5.2f)" % (w, a, c[0], c[1]))
    return r
