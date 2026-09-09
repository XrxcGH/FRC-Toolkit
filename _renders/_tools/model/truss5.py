"""Faithful transliteration of the CURRENT truss branch of
FRC Plate Geometry.txt (post the last-hour rewrite).

Differences from truss3.py, which is the pre-change snapshot:
  - frcAutoSizing is loading aware and uses frcBuckleSpan(material, rib, thk)
  - the boss merge no longer GROWS the keeper's radius
  - frcPerimeterStations walks the outline edge to edge (no bearing sort)
  - the opposite-inset-line test is present
  - arcCut, the circular segment correction, is computed

Everything is in inches with the units stripped, as the FS branch does
inside itself.
"""
import math

TAU = 2.0 * math.pi


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def nrm(a):
    return math.hypot(a[0], a[1])


# ------------------------------------------------------------------ core ----
SLENDER = {"AL_6061": 16.3, "AL_7075": 11.5, "POLYCARB": 5.9, "DELRIN": 6.4,
           "PLA": 8.2, "PETG": 6.2, "ONYX": 7.8, "STEEL": 20.9,
           "PLYWOOD": 17.3}

KMAP = {
    "CONSERVATIVE": {"wall": 1.5, "hole": 0.50, "rib": 1.25, "span": 8, "buckle": 0.75},
    "BALANCED":     {"wall": 1.0, "hole": 0.35, "rib": 0.90, "span": 12, "buckle": 0.90},
    "AGGRESSIVE":   {"wall": 0.75, "hole": 0.25, "rib": 0.70, "span": 18, "buckle": 1.00},
}


def frc_min_wall(tool_dia):          # CNC
    return max(0.090, tool_dia)


def frc_min_corner_radius(tool_dia):  # CNC
    return tool_dia / 2.0


def frc_min_floor():                  # CNC
    return 0.040


def frc_buckle_span(material, width, depth):
    return max(min(width, depth), 0.0) * SLENDER[material]


def frc_auto_sizing(thickness, aggression="BALANCED", tool_dia=0.25,
                    material="AL_6061", loading="EDGE_ON"):
    k = KMAP[aggression]
    floor_min = frc_min_wall(tool_dia)
    rib = min(max(k["rib"] * thickness, floor_min), 0.5)
    buckle_span = frc_buckle_span(material, rib, thickness)
    # the bound is on the unbraced length, which is the triangle side
    # 2 * (pocket + rib) / sqrt(3); invert it to get the pocket it allows
    buckle_pocket = max(0.05, (math.sqrt(3.0) / 2.0) * buckle_span - rib)
    beam_pocket = k["span"] * thickness
    want = beam_pocket
    if loading == "EDGE_ON":
        want = max(0.05, (math.sqrt(3.0) / 2.0) * (k["buckle"] * buckle_span) - rib)
    elif loading == "NON_STRUCTURAL":
        want = max(beam_pocket, buckle_pocket)
    want_pocket = min(max(want, 0.4), 4.0)
    buckle_binds = (buckle_pocket < want_pocket
                    or (loading == "EDGE_ON" and 0.4 <= want <= 4.0))
    return {"wall": min(max(k["wall"] * thickness, floor_min), 0.5),
            "rib": rib, "pocket": min(want_pocket, buckle_pocket),
            "buckleCapped": buckle_binds, "holeFactor": k["hole"],
            "floor": max(0.25 * thickness, frc_min_floor())}


# -------------------------------------------------------------- delaunay ----
def in_circumcircle(a, b, c, d):
    ax, ay = a[0] - d[0], a[1] - d[1]
    bx, by = b[0] - d[0], b[1] - d[1]
    cx, cy = c[0] - d[0], c[1] - d[1]
    det = ((ax * ax + ay * ay) * (bx * cy - cx * by)
           - (bx * bx + by * by) * (ax * cy - cx * ay)
           + (cx * cx + cy * cy) * (ax * by - bx * ay))
    orient = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
    return det > 0 if orient > 0 else det < 0


def tri_holds(a, b, c, d):
    s1 = (b[0] - a[0]) * (d[1] - a[1]) - (d[0] - a[0]) * (b[1] - a[1])
    s2 = (c[0] - b[0]) * (d[1] - b[1]) - (d[0] - b[0]) * (c[1] - b[1])
    s3 = (a[0] - c[0]) * (d[1] - c[1]) - (d[0] - c[0]) * (a[1] - c[1])
    return (s1 >= 0 and s2 >= 0 and s3 >= 0) or (s1 <= 0 and s2 <= 0 and s3 <= 0)


def share_edge(t1, t2):
    for a in range(3):
        u, v = t1[a], t1[(a + 1) % 3]
        for b in range(3):
            x, y = t2[b], t2[(b + 1) % 3]
            if (u == x and v == y) or (u == y and v == x):
                return True
    return False


def frc_delaunay(pin):
    n = len(pin)
    if n < 3:
        return []
    p = list(pin)
    minx = maxx = p[0][0]
    miny = maxy = p[0][1]
    for q in p:
        minx, maxx = min(minx, q[0]), max(maxx, q[0])
        miny, maxy = min(miny, q[1]), max(maxy, q[1])
    dm = max(maxx - minx, maxy - miny) * 1000 + 1
    mx, my = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    p.append((mx - 2 * dm, my - dm))
    p.append((mx, my + 2 * dm))
    p.append((mx + 2 * dm, my - dm))
    tris = [[n, n + 1, n + 2]]
    for i in range(n):
        cand, keep = [], []
        for t in tris:
            if in_circumcircle(p[t[0]], p[t[1]], p[t[2]], p[i]):
                cand.append(t)
            else:
                keep.append(t)
        nc = len(cand)
        if nc == 0:
            continue
        in_cav = [False] * nc
        stack = []
        for k in range(nc):
            if tri_holds(p[cand[k][0]], p[cand[k][1]], p[cand[k][2]], p[i]):
                in_cav[k] = True
                stack.append(k)
        if not stack:
            in_cav = [True] * nc
        while stack:
            cur = stack.pop()
            for k in range(nc):
                if in_cav[k]:
                    continue
                if share_edge(cand[cur], cand[k]):
                    in_cav[k] = True
                    stack.append(k)
        bad = []
        for k in range(nc):
            t = cand[k]
            if in_cav[k]:
                bad.append([t[0], t[1]])
                bad.append([t[1], t[2]])
                bad.append([t[2], t[0]])
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
    out = []
    for t in tris:
        if t[0] < n and t[1] < n and t[2] < n:
            out.append(t)
    return out


# -------------------------------------------------------------- stations ----
def perimeter_stations(rect, max_edge):
    """The FS walk: edges in boundary order, each edge stationed from its own
    start and stopping short of its end."""
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
        for j in range(int(nsub)):
            q = add(a, mul(d, L * j / nsub))
            if any(nrm(sub(o["point"], q)) < 0.02 for o in out):
                continue
            out.append({"point": q, "direction": d})
    return out


def island_centers(centre, reach, pitch, angle, phase=(0.0, 0.0)):
    row = pitch * math.sqrt(3.0) / 2.0
    n_row = int(math.ceil(reach / row)) + 1
    n_col = int(math.ceil(reach / pitch)) + 1
    u = (math.cos(angle), math.sin(angle))
    v = (-math.sin(angle), math.cos(angle))
    out = []
    for r in range(-n_row, n_row + 1):
        off = 0.0 if r % 2 == 0 else pitch / 2.0
        for c in range(-n_col, n_col + 1):
            out.append(add(centre, add(mul(u, (c + phase[0]) * pitch + off),
                                       mul(v, (r + phase[1]) * row))))
    return out


def in_poly(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        if (a[1] > p[1]) != (b[1] > p[1]):
            t = (p[1] - a[1]) / (b[1] - a[1])
            if p[0] < a[0] + t * (b[0] - a[0]):
                inside = not inside
    return inside


def side2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def crosses_seg(p1, p2, p3, p4):
    d1 = side2(p3, p4, p1)
    d2 = side2(p3, p4, p2)
    d3 = side2(p1, p2, p3)
    d4 = side2(p1, p2, p4)
    return (((d1 > 1e-12 and d2 < -1e-12) or (d1 < -1e-12 and d2 > 1e-12))
            and ((d3 > 1e-12 and d4 < -1e-12) or (d3 < -1e-12 and d4 > 1e-12)))


def seg_dist(p, a, b):
    ab = sub(b, a)
    L2 = dot(ab, ab)
    if L2 < 1e-18:
        return nrm(sub(p, a))
    t = max(0.0, min(1.0, dot(sub(p, a), ab) / L2))
    return nrm(sub(p, add(a, mul(ab, t))))


# --------------------------------------------------------------- builder ----
def build_truss5(plate, holes, thickness=0.125, tool_dia=0.25,
                 aggression="BALANCED", material="AL_6061", loading="EDGE_ON",
                 round_corners=True, pattern_angle=0.0, node_cap=240,
                 pocket_scale=1.0, arc_steps=64):
    """One pass of the truss branch at pocket = s.pocket * pocket_scale."""
    s = frc_auto_sizing(thickness, aggression, tool_dia, material, loading)
    tool_rad = frc_min_corner_radius(tool_dia) if round_corners else 0.0
    eff_tool = tool_dia
    W, H = plate
    off = s["wall"] + tool_rad
    rect = (off, off, W - off, H - off)

    islands = []
    for (cx, cy, dia) in holes:
        prot = dia / 2.0 + s["wall"]
        need = min(max(s["holeFactor"] * dia, s["wall"]), 0.5)
        if need > s["wall"] + 1e-6:
            prot = dia / 2.0 + need
        islands.append({"center": (cx, cy), "r": prot, "d": dia})

    c2 = ((rect[0] + rect[2]) / 2.0, (rect[1] + rect[3]) / 2.0)
    span_x = rect[2] - rect[0]
    span_y = rect[3] - rect[1]
    size_cap = max(min(span_x, span_y) / 3.0, 0.3)
    pocket_used = min(s["pocket"] * pocket_scale, size_cap)
    reach = math.hypot(span_x, span_y) / 2.0 + pocket_used

    u_inset = s["rib"] / 2.0 + tool_rad
    u_slv_w = max(0.02, eff_tool - 2 * tool_rad)
    u_min_inr = u_inset + max(0.6 * tool_rad, u_slv_w)
    u_min_tri = 2.0 * math.sqrt(3.0) * u_min_inr
    u_want = 2.0 * (pocket_used + s["rib"]) / math.sqrt(3.0)
    u_edge_max = max(u_want, 1.3 * u_min_tri)
    u_space = 0.66 * u_edge_max
    u_wall_clear = 0.45 * u_edge_max
    u_boss_clear = 0.50 * u_edge_max
    u_slv_area = (0.6 * s["rib"]) ** 2
    u_min_run = max(0.02, u_slv_w)

    stations = perimeter_stations(rect, u_edge_max / 1.15)
    if len(islands) + len(stations) > 140:
        raise ValueError("too many nodes to mesh")
    if len(stations) < 3:
        raise ValueError("outline could not be followed")

    base = [st["point"] for st in stations]
    u_gap = min(0.01, s["wall"] / 20.0)
    u_push = max(0.0, min(u_inset - u_gap, s["wall"] + tool_rad))
    ring_area2 = 0.0
    nb = len(base)
    for i in range(nb):
        q = base[(i + 1) % nb]
        ring_area2 += base[i][0] * q[1] - q[0] * base[i][1]
    ring_sgn = 1.0 if ring_area2 > 0 else -1.0
    outer = []
    for i in range(nb):
        p0 = base[(i + nb - 1) % nb]
        p1 = base[i]
        p2 = base[(i + 1) % nb]
        if nrm(sub(p1, p0)) < 1e-9 or nrm(sub(p2, p1)) < 1e-9:
            outer.append(p1)
            continue
        u0 = mul(sub(p1, p0), 1.0 / nrm(sub(p1, p0)))
        u1 = mul(sub(p2, p1), 1.0 / nrm(sub(p2, p1)))
        n0 = (u0[1] * ring_sgn, -u0[0] * ring_sgn)
        n1 = (u1[1] * ring_sgn, -u1[0] * ring_sgn)
        bis = add(n0, n1)
        if nrm(bis) < 1e-9:
            outer.append(add(p1, mul(n0, u_push)))
            continue
        bh = mul(bis, 1.0 / nrm(bis))
        cos_half = dot(bh, n0)
        outer.append(add(p1, mul(bh, u_push / cos_half if cos_half > 0.34
                                 else u_push * 2.9)))

    # --- bosses. NO growth on merge, which is the current FS behaviour. ---
    boss_order = sorted(range(len(islands)), key=lambda i: (-islands[i]["r"], i))
    boss_at, boss_rad, boss_idx = [], [], []
    boss_merged = 0
    for j in boss_order:
        isl = islands[j]
        cq = isl["center"]
        rq = isl["r"] + tool_rad
        hit = -1
        for k in range(len(boss_at)):
            if nrm(sub(cq, boss_at[k])) < rq + boss_rad[k]:
                hit = k
                break
        if hit >= 0:
            boss_merged += 1
            continue
        boss_at.append(cq)
        boss_rad.append(rq)
        boss_idx.append(j)

    nodes = list(outer)
    node_r = [0.0] * len(outer)
    for (_hi, k) in sorted([(boss_idx[k], k) for k in range(len(boss_at))]):
        nodes.append(boss_at[k])
        node_r.append(boss_rad[k])

    def wall_dist(q):
        return min(seg_dist(q, outer[i], outer[(i + 1) % len(outer)])
                   for i in range(len(outer)))

    def room_for(q, nds, rds):
        if not in_poly(q, outer):
            return False
        if wall_dist(q) < u_wall_clear:
            return False
        for i in range(len(nds)):
            lim = u_space if rds[i] <= 0 else max(u_space, rds[i] + u_boss_clear)
            if nrm(sub(q, nds[i])) < lim:
                return False
        return True

    seed_order = []
    for cp in island_centers(c2, reach, u_edge_max, pattern_angle):
        rel = sub(cp, c2)
        seed_order.append((nrm(rel), math.degrees(math.atan2(rel[1], rel[0])), cp))
    seed_order.sort(key=lambda e: (e[0], e[1]))
    capped = False
    for e in seed_order:
        if len(nodes) >= node_cap:
            capped = True
            break
        if room_for(e[2], nodes, node_r):
            nodes.append(e[2])
            node_r.append(0.0)

    def keep_tri(nds, t):
        a, b, c = nds[t[0]], nds[t[1]], nds[t[2]]
        cen = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)
        if not in_poly(cen, outer):
            return False
        for (q0, q1, w) in ((a, b, c), (b, c, a), (c, a, b)):
            m = ((q0[0] + q1[0]) / 2.0, (q0[1] + q1[1]) / 2.0)
            if not in_poly((m[0] + (w[0] - m[0]) * 0.15,
                            m[1] + (w[1] - m[1]) * 0.15), outer):
                return False
            for i in range(len(outer)):
                if crosses_seg(q0, q1, outer[i], outer[(i + 1) % len(outer)]):
                    return False
        return True

    def mesh_of(nds):
        out, key = [], set()
        for t in frc_delaunay(nds):
            lo, hi = min(t), max(t)
            mid = t[0] + t[1] + t[2] - lo - hi
            if lo == mid or mid == hi:
                continue
            if (lo, mid, hi) in key:
                continue
            key.add((lo, mid, hi))
            if keep_tri(nds, t):
                out.append(t)
        return out

    tris = mesh_of(nodes)
    for _p in range(4):
        want = []
        for t in tris:
            a, b, c = nodes[t[0]], nodes[t[1]], nodes[t[2]]
            longest = max(nrm(sub(b, a)), nrm(sub(c, b)), nrm(sub(a, c)))
            if longest > u_edge_max:
                want.append((-longest, ((a[0] + b[0] + c[0]) / 3.0,
                                        (a[1] + b[1] + c[1]) / 3.0)))
        if not want:
            break
        want.sort(key=lambda e: e[0])
        added = 0
        for e in want:
            if len(nodes) >= node_cap:
                capped = True
                break
            if room_for(e[1], nodes, node_r):
                nodes.append(e[1])
                node_r.append(0.0)
                added += 1
        if added == 0:
            break
        tris = mesh_of(nodes)

    # --- one pocket per triangle -----------------------------------------
    cell_loops = []
    cell_tri = []
    cell_area = []
    solid_left = 0
    metric = 0.0
    for t in tris:
        p = [nodes[t[0]], nodes[t[1]], nodes[t[2]]]
        rr = [node_r[t[0]], node_r[t[1]], node_r[t[2]]]
        if side2(p[0], p[1], p[2]) < 0:
            p = [p[0], p[2], p[1]]
            rr = [rr[0], rr[2], rr[1]]
        ar2 = abs(side2(p[0], p[1], p[2]))
        per = nrm(sub(p[1], p[0])) + nrm(sub(p[2], p[1])) + nrm(sub(p[0], p[2]))
        if per < 1e-9 or ar2 / per <= u_inset:
            solid_left += 1
            continue
        blocked = False
        for i in range(len(nodes)):
            if node_r[i] <= 0 or i in (t[0], t[1], t[2]):
                continue
            cq = nodes[i]
            near = min(seg_dist(cq, p[0], p[1]), seg_dist(cq, p[1], p[2]),
                       seg_dist(cq, p[2], p[0]))
            if (side2(p[0], p[1], cq) > 0 and side2(p[1], p[2], cq) > 0
                    and side2(p[2], p[0], cq) > 0):
                near = 0.0
            if near < node_r[i]:
                blocked = True
                break
        if blocked:
            solid_left += 1
            continue

        us, line_n, line_k = [], [], []
        for i in range(3):
            u = mul(sub(p[(i + 1) % 3], p[i]),
                    1.0 / nrm(sub(p[(i + 1) % 3], p[i])))
            nv = (-u[1], u[0])
            us.append(u)
            line_n.append(nv)
            line_k.append(dot(p[i], nv) + u_inset)
        corner = []
        ok = True
        for i in range(3):
            n0, k0 = line_n[(i + 2) % 3], line_k[(i + 2) % 3]
            n1, k1 = line_n[i], line_k[i]
            det = n0[0] * n1[1] - n0[1] * n1[0]
            if abs(det) < 1e-12:
                ok = False
                break
            corner.append(((k0 * n1[1] - n0[1] * k1) / det,
                           (n0[0] * k1 - k0 * n1[0]) / det))
        if not ok:
            solid_left += 1
            continue

        t_start = [0.0, 0.0, 0.0]
        t_stop = [0.0, 0.0, 0.0]
        for i in range(3):
            t_stop[i] = dot(sub(corner[(i + 1) % 3], corner[i]), us[i])
        arc_a = [None, None, None]
        arc_b = [None, None, None]
        for i in range(3):
            if rr[i] <= 0 or nrm(sub(corner[i], p[i])) >= rr[i] - 0.02:
                continue
            jj = (i + 1) % 3
            if rr[i] >= dot(line_n[jj], p[i]) - line_k[jj]:
                ok = False
                break
            prev = (i + 2) % 3
            w1 = sub(corner[i], p[i])
            b1 = 2 * dot(w1, us[i])
            c1 = dot(w1, w1) - rr[i] * rr[i]
            d1 = b1 * b1 - 4 * c1
            w0 = sub(corner[prev], p[i])
            b0 = 2 * dot(w0, us[prev])
            c0 = dot(w0, w0) - rr[i] * rr[i]
            d0 = b0 * b0 - 4 * c0
            if d1 <= 0 or d0 <= 0:
                ok = False
                break
            t_start[i] = (-b1 + math.sqrt(d1)) / 2
            t_stop[prev] = (-b0 - math.sqrt(d0)) / 2
            arc_a[i] = add(corner[prev], mul(us[prev], t_stop[prev]))
            arc_b[i] = add(corner[i], mul(us[i], t_start[i]))
        if not ok:
            solid_left += 1
            continue
        for i in range(3):
            if t_stop[i] - t_start[i] < u_min_run:
                ok = False
        if not ok:
            solid_left += 1
            continue

        loop = []
        arc_cut = 0.0
        for i in range(3):
            s_pt = add(corner[i], mul(us[i], t_start[i]))
            e_pt = add(corner[i], mul(us[i], t_stop[i]))
            if arc_a[i] is not None:
                bis = add(sub(arc_a[i], p[i]), sub(arc_b[i], p[i]))
                if nrm(bis) < 1e-9:
                    ok = False
                    break
                th = 2 * math.asin(min(1.0, nrm(sub(arc_b[i], arc_a[i]))
                                       / (2 * rr[i])))
                arc_cut += (rr[i] * rr[i] / 2.0) * (th - math.sin(th))
                loop.append({"kind": "arc", "start": arc_a[i], "end": arc_b[i],
                             "centre": p[i], "r": rr[i],
                             "mid": add(p[i], mul(mul(bis, 1.0 / nrm(bis)), rr[i]))})
            loop.append({"kind": "line", "start": s_pt, "end": e_pt})
        if not ok:
            solid_left += 1
            continue
        poly = [sg["start"] for sg in loop]
        area2 = 0.0
        for i in range(len(poly)):
            q = poly[(i + 1) % len(poly)]
            area2 += poly[i][0] * q[1] - q[0] * poly[i][1]
        pocket_area = abs(area2) / 2.0 - arc_cut
        if pocket_area < u_slv_area:
            solid_left += 1
            continue
        cell_loops.append(loop)
        cell_tri.append(t)
        cell_area.append(pocket_area)
        metric += pocket_area

    if not cell_loops:
        raise ValueError("no triangle large enough to pocket")
    if len(cell_loops) > 2 * node_cap:
        raise ValueError("too many pockets")

    # ribs: a mesh edge with a pocket on each side
    count = {}
    for t in cell_tri:
        for (i, j) in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            key = (min(i, j), max(i, j))
            count[key] = count.get(key, 0) + 1
    drawn = sum(1 for k, c in count.items() if c == 2)

    # polygon approximation of each pocket, for the rasteriser
    pockets = []
    for loop in cell_loops:
        pts = []
        for sg in loop:
            if sg["kind"] == "arc":
                cen = sg["centre"]
                r = sg["r"]
                a0 = math.atan2(sg["start"][1] - cen[1], sg["start"][0] - cen[0])
                a1 = math.atan2(sg["end"][1] - cen[1], sg["end"][0] - cen[0])
                dd = a1 - a0
                while dd > 0:
                    dd -= TAU
                while dd < -TAU:
                    dd += TAU
                n = max(2, int(math.ceil(abs(dd) / (TAU / arc_steps))))
                for j in range(n + 1):
                    a = a0 + dd * (j / float(n))
                    pts.append((cen[0] + r * math.cos(a), cen[1] + r * math.sin(a)))
            else:
                pts.append(sg["start"])
                pts.append(sg["end"])
        clean = []
        for q in pts:
            if not clean or nrm(sub(q, clean[-1])) > 1e-9:
                clean.append(q)
        if len(clean) > 1 and nrm(sub(clean[0], clean[-1])) < 1e-9:
            clean.pop()
        pockets.append({"poly": clean})

    return {"plate": plate, "holes": holes, "s": s, "toolRad": tool_rad,
            "islands": islands, "outer": outer, "nodes": nodes,
            "radius": node_r, "stations": stations, "tris": cell_tri,
            "pockets": pockets, "cellArea": cell_area, "metric": metric,
            "ribs": drawn, "solidLeft": solid_left, "merged": boss_merged,
            "capped": capped, "pocketUsed": pocket_used,
            "edgeMax": u_edge_max, "nNodes": len(nodes)}
