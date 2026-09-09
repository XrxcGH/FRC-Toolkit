"""The new TRUSS construction, transliterated ahead of the FeatureScript.

Instead of choosing bars and letting the pockets fall out, the domain to be
lightened is meshed and every triangle of the mesh becomes one pocket.

Domain  = the part outline pushed in by the wall, minus each boss ring.
Mesh    = Bowyer-Watson Delaunay over the domain boundary rings plus Steiner
          points, refined until no triangle is larger than a target and none
          has an interior angle below a floor.
Pocket  = each mesh triangle inset by half a rib on every edge.

Same constants and the same order the FeatureScript will use.
"""
import math

from truss import (frc_auto_sizing, frc_min_corner_radius, frc_delaunay,
                   perimeter_stations, nrm, sub, add, mul, dot, seg_cross)

DEG = math.pi / 180.0


# --------------------------------------------------------------- geometry --
def poly_area2(p):
    a = 0.0
    for i in range(len(p)):
        q = p[(i + 1) % len(p)]
        a += p[i][0] * q[1] - q[0] * p[i][1]
    return a


def in_polygon(p, poly):
    """Crossing number, so a non-convex outline answers correctly too."""
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


def seg_dist(p, a, b):
    L2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    if L2 < 1e-18:
        return nrm(sub(p, a))
    t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / L2
    t = max(0.0, min(1.0, t))
    return nrm(sub(p, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))))


def tri_min_angle(a, b, c):
    def ang(o, p, q):
        u, v = sub(p, o), sub(q, o)
        nu, nv = nrm(u), nrm(v)
        if nu < 1e-12 or nv < 1e-12:
            return 0.0
        return math.degrees(math.acos(max(-1.0, min(1.0, dot(u, v) / (nu * nv)))))
    return min(ang(a, b, c), ang(b, a, c), ang(c, a, b))


def circumcentre(a, b, c):
    d = 2.0 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-14:
        return None
    aa = a[0] * a[0] + a[1] * a[1]
    bb = b[0] * b[0] + b[1] * b[1]
    cc = c[0] * c[0] + c[1] * c[1]
    return ((aa * (b[1] - c[1]) + bb * (c[1] - a[1]) + cc * (a[1] - b[1])) / d,
            (aa * (c[0] - b[0]) + bb * (a[0] - c[0]) + cc * (b[0] - a[0])) / d)


def inset_triangle(a0, b0, c0, d):
    """frcInsetTriangle, ported literally."""
    a, b, c = a0, b0, c0
    area2 = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
    if abs(area2) < 1e-10:
        return None
    if area2 < 0:
        b, c = c, b
        area2 = -area2
    per = nrm(sub(b, a)) + nrm(sub(c, b)) + nrm(sub(a, c))
    if 2 * (area2 / 2) / per <= d:
        return None
    pts = [a, b, c]
    ns, cs = [], []
    for i in range(3):
        pp, qq = pts[i], pts[(i + 1) % 3]
        u = mul(sub(qq, pp), 1.0 / nrm(sub(qq, pp)))
        nv = (-u[1], u[0])
        ns.append(nv)
        cs.append(dot(pp, nv) + d)
    res = []
    for i in range(3):
        n0, k0 = ns[i], cs[i]
        n1, k1 = ns[(i + 1) % 3], cs[(i + 1) % 3]
        det = n0[0] * n1[1] - n0[1] * n1[0]
        if abs(det) < 1e-12:
            return None
        res.append(((k0 * n1[1] - n0[1] * k1) / det,
                    (n0[0] * k1 - k0 * n1[0]) / det))
    return [res[2], res[0], res[1]]


# ---------------------------------------------------------------- builder --
def build_truss2(plate, holes, thickness=0.25, tool_dia=0.25,
                 ang_floor=22.0, node_cap=240, max_pass=16,
                 size_slack=1.0, round_corners=True, inr_mult=0.6,
                 split=True, split_min=2.0, space_mult=0.95,
                 ring_mult=3.4, boss_centre=True, sliver_guard=True):
    s = frc_auto_sizing(thickness, tool_dia)
    tool_rad = frc_min_corner_radius(tool_dia) if round_corners else 0.0
    W, H = plate
    inset = s["wall"] + tool_rad
    rect = (inset, inset, W - inset, H - inset)

    islands = []
    for (cx, cy, dia) in holes:
        prot = dia / 2 + s["wall"]
        need = min(max(s["holeFactor"] * dia, s["wall"]), 0.5)
        if need > s["wall"] + 1e-6:
            prot = dia / 2 + need
        islands.append({"center": (cx, cy), "r": prot, "d": dia})

    c2 = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
    span_x = rect[2] - rect[0]
    span_y = rect[3] - rect[1]
    size_cap = max(min(span_x, span_y) / 3, 0.3)
    pocket_used = min(s["pocket"], size_cap)
    max_edge = min(max(pocket_used * 2.5, 3.0), max(span_x, span_y) / 4)
    stations = perimeter_stations(rect, max_edge)

    # Half a rib plus the end mill radius. Everything is cut oversize by the
    # cutter radius and opened back out at the end, so a pocket inset by this
    # leaves exactly one rib between it and its neighbour.
    d = s["rib"] / 2 + tool_rad
    # The pocket stops this far short of the wall face rather than landing on
    # it, so the boolean never has to cut along a coincident plane.
    wall_gap = min(0.01, s["wall"] / 20.0)
    ring_push = max(0.0, min(d - wall_gap, s["wall"] + tool_rad))
    # The size bound is the cell an isogrid would make from the same pocket
    # size: three rib families spaced pocket + rib apart tile the plane with
    # equilateral triangles of that height, so their side is this. The truss
    # and the lattice patterns then mean the same thing by pocket size.
    edge_max = size_slack * 2.0 * (pocket_used + s["rib"]) / math.sqrt(3.0)
    # The smallest triangle that can still hold a pocket: inset by d it must
    # leave room for the cutter to turn, and an equilateral of this side has
    # exactly that inradius.
    slv_w0 = max(0.02, tool_dia - 2 * tool_rad)
    min_inr = d + max(inr_mult * tool_rad, slv_w0)
    min_tri = 2.0 * math.sqrt(3.0) * min_inr
    tiny_pocket = edge_max < 1.3 * min_tri
    edge_max = max(edge_max, 1.3 * min_tri)
    # A triangle standing on a boundary edge of length e can have an inradius
    # of at most e / 2, so a ring edge shorter than twice the smallest useful
    # inradius guarantees a collar of triangles too small to pocket.
    ring_edge = min(ring_mult * min_inr, 0.45 * edge_max)

    # --- the domain boundary --------------------------------------------
    ring = sorted(stations, key=lambda st: math.atan2(st["point"][1] - c2[1],
                                                      st["point"][0] - c2[0]))
    base = [st["point"] for st in ring]
    outer = push_outward(base, ring_push)

    # A boss ring is a polygon circumscribing the keep-out circle, and its
    # edges have to be long enough that the triangles beside them can still
    # hold a pocket. A ring sampled finely enough to hug a small boss makes a
    # collar of triangles too small to inset, which is why the ring is as
    # coarse as the boss allows and is grown when even four sides are short.
    boss_rings = []
    for isl in islands:
        rb = isl["r"] + tool_rad
        k = 4
        for kk in (6, 8, 10, 12, 16, 20, 24):
            if 2 * rb * math.tan(math.pi / kk) >= ring_edge:
                k = kk
        q = max(rb, ring_edge / (2 * math.tan(math.pi / k)))
        rp = q / math.cos(math.pi / k)
        boss_rings.append([(isl["center"][0] + rp * math.cos(2 * math.pi * i / k),
                            isl["center"][1] + rp * math.sin(2 * math.pi * i / k))
                           for i in range(k)])
    boss_centres = [isl["center"] for isl in islands] if boss_centre else []

    nodes = list(outer)
    segs = [[i, (i + 1) % len(outer), -1] for i in range(len(outer))]
    for j, br in enumerate(boss_rings):
        b0 = len(nodes)
        nodes += br
        segs += [[b0 + i, b0 + (i + 1) % len(br), j] for i in range(len(br))]
    # The centre of each boss goes in too. Without it the triangulation is
    # free to run an edge straight across a boss from one side to the other,
    # and every triangle carrying such an edge has to be thrown away, which
    # is what left whole bands of the plate unmeshed.
    nodes += boss_centres

    n_fixed = len(nodes)
    stats = {"passes": 0, "steiner": 0, "splits": 0,
             "capped": False, "gaveUp": 0}

    boss_inr = [nrm(sub(br[0], islands[j]["center"])) * math.cos(math.pi / len(br))
                for j, br in enumerate(boss_rings)]

    def in_domain(p):
        if not in_polygon(p, outer):
            return False
        for j in range(len(islands)):
            if in_polygon(p, boss_rings[j]):
                return False
        return True

    def crosses_boundary(nds, p, q):
        """True when this edge cuts a boundary rather than lying on one.

        The Delaunay is not constrained, so an edge is free to run straight
        across a boss or out through the outline. A triangle carrying one is
        not in the domain however its centroid reads, and it is the test that
        keeps a pocket from being clipped into something that is not a
        triangle.
        """
        for sg in segs:
            if seg_cross(p, q, nds[sg[0]], nds[sg[1]]):
                return True
        return False

    def keep_tri(nds, t):
        a, b, c = nds[t[0]], nds[t[1]], nds[t[2]]
        cen = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)
        if not in_domain(cen):
            return False
        # Each edge is probed a little way inside the triangle rather than at
        # the midpoint itself. An edge lying along the boundary has its
        # midpoint on the boundary, where inside and outside are not decided,
        # and testing there rejected every triangle that touched a wall.
        for (p, q, w) in ((a, b, c), (b, c, a), (c, a, b)):
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            if not in_domain((m[0] + 0.15 * (w[0] - m[0]),
                              m[1] + 0.15 * (w[1] - m[1]))):
                return False
            if crosses_boundary(nds, p, q):
                return False
        return True

    def mesh(nds):
        out = []
        seen = set()
        for t in frc_delaunay(nds):
            key = tuple(sorted(t))
            if len(set(key)) < 3 or key in seen:
                continue
            seen.add(key)
            if keep_tri(nds, t):
                out.append(t)
        return out

    def encroached(nds, sgs):
        hit = []
        for si, sg in enumerate(sgs):
            p, q = nds[sg[0]], nds[sg[1]]
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            rr = nrm(sub(q, p)) / 2
            for i, v in enumerate(nds):
                if i == sg[0] or i == sg[1]:
                    continue
                if nrm(sub(v, m)) < rr - 1e-9:
                    hit.append(si)
                    break
        return hit

    def split(nds, sgs, which):
        """Midpoint of each named segment; a boss segment lands on its ring."""
        nds = list(nds)
        sgs = list(sgs)
        for si in sorted(which, reverse=True):
            sg = sgs[si]
            p, q = nds[sg[0]], nds[sg[1]]
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            if sg[2] >= 0:
                ctr = islands[sg[2]]["center"]
                rp = nrm(sub(boss_rings[sg[2]][0], ctr))
                v = sub(m, ctr)
                if nrm(v) > 1e-9:
                    m = add(ctr, mul(v, rp / nrm(v)))
            ni = len(nds)
            nds.append(m)
            sgs[si] = [sg[0], ni, sg[2]]
            sgs.append([ni, sg[1], sg[2]])
        return nds, sgs

    # Below this a new node only buys a triangle too small to inset into a
    # pocket, so it would spend the budget for nothing.
    min_space = space_mult * min_tri

    for p_i in range(max_pass):
        stats["passes"] = p_i + 1
        if len(nodes) >= node_cap:
            stats["capped"] = True
            break
        # A segment already down to the shortest useful triangle edge is left
        # alone: halving it again only buys triangles too small to pocket.
        enc = [si for si in encroached(nodes, segs) if segs[si][2] < 0
               and nrm(sub(nodes[segs[si][0]], nodes[segs[si][1]]))
               > split_min * ring_edge] if split else []
        if enc:
            if len(nodes) + len(enc) > node_cap:
                stats["capped"] = True
                break
            nodes, segs = split(nodes, segs, enc)
            stats["splits"] += len(enc)
            continue
        tris = mesh(nodes)
        bad = []
        for t in tris:
            a, b, c = nodes[t[0]], nodes[t[1]], nodes[t[2]]
            longest = max(nrm(sub(a, b)), nrm(sub(b, c)), nrm(sub(c, a)))
            ang = tri_min_angle(a, b, c)
            if longest > edge_max or ang < ang_floor:
                bad.append((-(longest / edge_max) - (ang_floor - ang) / 90.0, t))
        if not bad:
            break
        bad.sort(key=lambda z: (z[0], min(nodes[z[1][0]], nodes[z[1][1]],
                                          nodes[z[1][2]])))
        want = []
        mark = set()
        for score, t in bad:
            cc = circumcentre(nodes[t[0]], nodes[t[1]], nodes[t[2]])
            if cc is None:
                continue
            hit = [si for si, sg in enumerate(segs)
                   if seg_encroaches(nodes[sg[0]], nodes[sg[1]], cc)]
            if hit:
                # A boss ring is never split: its edges are already as short
                # as a pocket-bearing triangle can stand, so a point that
                # encroaches one is passed over instead.
                mark.update(si for si in hit if segs[si][2] < 0 and split
                            and nrm(sub(nodes[segs[si][0]], nodes[segs[si][1]]))
                            > split_min * ring_edge)
                continue
            if not in_domain(cc):
                continue
            want.append((score, cc))
        if mark:
            if len(nodes) + len(mark) > node_cap:
                stats["capped"] = True
                break
            nodes, segs = split(nodes, segs, sorted(mark))
            stats["splits"] += len(mark)
            continue
        # Kept in worst-first order and accepted unless something strictly
        # worse already sits too close. A mirrored pair scores the same, so
        # neither blocks the other and a symmetric plate stays symmetric.
        fixed_now = list(nodes)
        taken = []
        added = 0
        for score, cc in want:
            if len(nodes) >= node_cap:
                stats["capped"] = True
                break
            if any(nrm(sub(cc, v)) < min_space for v in fixed_now):
                continue
            # Two triangles that share a circumcircle share a circumcentre
            # exactly, and they score the same, so the rule above would insert
            # the same point twice and the triangulation would come back with
            # a duplicate triangle. Anything this close is the same point.
            if any(nrm(sub(cc, v)) < 0.02 * min_tri for sc, v in taken):
                continue
            if any(sc < score - 1e-9 and nrm(sub(cc, v)) < min_space
                   for sc, v in taken):
                continue
            taken.append((score, cc))
            nodes.append(cc)
            added += 1
        stats["steiner"] += added
        if added == 0:
            stats["gaveUp"] = len(bad)
            break

    tris = mesh(nodes)

    # --- pockets ---------------------------------------------------------
    min_area = (2.0 * s["rib"]) ** 2
    # frcDropSlivers runs on the pocket as drawn, undersize by the end mill
    # radius. The truss tests the pocket that survives instead, so it hands
    # that pass a threshold below anything it emits and meets the width test
    # itself. What is left for that pass to catch is scrap the boolean made.
    slv_width = max(0.02, tool_dia - 2 * tool_rad)
    slv_area = (0.6 * s["rib"]) ** 2
    pockets = []
    dropped = 0
    for t in tris:
        a, b, c = nodes[t[0]], nodes[t[1]], nodes[t[2]]
        if tri_min_angle(a, b, c) < ang_floor - 1e-9:
            dropped += 1
            continue
        ar = abs(poly_area2([a, b, c])) / 2
        per = nrm(sub(a, b)) + nrm(sub(b, c)) + nrm(sub(c, a))
        inr = 2 * ar / per
        if inr < min_inr:
            dropped += 1
            continue
        # The pocket that survives is the one the cutter radius grows back, so
        # the area test is on that and not on the undersize triangle drawn.
        grown = (inr - s["rib"] / 2) / inr
        if ar * grown * grown < min_area:
            dropped += 1
            continue
        ins = inset_triangle(a, b, c, d)
        if ins is None:
            dropped += 1
            continue
        # frcDropSlivers runs later on the pocket as drawn, before the cutter
        # radius is opened back out, so a pocket has to clear its two tests
        # there as well or it is deleted after the fact and the region ends up
        # solid without anything here knowing.
        if sliver_guard:
            da = abs(poly_area2(ins)) / 2
            dp = sum(nrm(sub(ins[i], ins[(i + 1) % 3])) for i in range(3))
            if da < slv_area or 2 * da / dp < slv_width:
                dropped += 1
                continue
        pockets.append({"poly": ins, "tri": [a, b, c],
                        "idx": tuple(sorted(t))})
    kept = set(p["idx"] for p in pockets)

    # A rib is an edge with a pocket on each side. Boundary edges carry wall
    # or boss material, not a rib, and an edge beside a dropped triangle is
    # wider than a rib.
    face_of = {}
    for p in pockets:
        t = p["idx"]
        for e in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2])):
            face_of.setdefault(e, []).append(p)
    ribs = [e for e, v in face_of.items() if len(v) == 2]

    return {
        "s": s, "toolRad": tool_rad, "rect": rect, "islands": islands,
        "plate": plate, "holes": holes, "stations": stations,
        "outer": outer, "bossRings": boss_rings, "nodes": nodes,
        "tris": tris, "pockets": pockets, "ribs": ribs, "segs": segs,
        "dropped": dropped, "stats": stats, "d": d, "edgeMax": edge_max,
        "pocketUsed": pocket_used, "angFloor": ang_floor,
        "minTri": min_tri, "minInr": min_inr, "tinyPocket": tiny_pocket,
        "nFixed": n_fixed, "wallGap": wall_gap, "ringPush": ring_push,
        "minArea": min_area,
    }


def seg_encroaches(p, q, v):
    m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    return nrm(sub(v, m)) < nrm(sub(q, p)) / 2 - 1e-9


def push_outward(poly, dist):
    """The ring moved out by dist, mitred at each corner.

    The pockets are inset from this ring, so pushing it out by the inset
    distance less a hair is what lets a pocket run up to the wall face and
    leaves the wall exactly as thick as the dialog says.
    """
    if dist <= 0:
        return list(poly)
    n = len(poly)
    a2 = poly_area2(poly)
    sgn = 1.0 if a2 > 0 else -1.0
    out = []
    for i in range(n):
        p0 = poly[(i - 1) % n]
        p1 = poly[i]
        p2 = poly[(i + 1) % n]
        u0 = sub(p1, p0)
        u1 = sub(p2, p1)
        if nrm(u0) < 1e-12 or nrm(u1) < 1e-12:
            out.append(p1)
            continue
        u0 = mul(u0, 1.0 / nrm(u0))
        u1 = mul(u1, 1.0 / nrm(u1))
        # Outward normal of each edge, for a ring wound the way this one is.
        n0 = (u0[1] * sgn, -u0[0] * sgn)
        n1 = (u1[1] * sgn, -u1[0] * sgn)
        bis = add(n0, n1)
        if nrm(bis) < 1e-9:
            out.append(add(p1, mul(n0, dist)))
            continue
        bis = mul(bis, 1.0 / nrm(bis))
        cosh = dot(bis, n0)
        # A very sharp corner would throw the mitre a long way out, so it is
        # clamped and the vertex just moves along the bisector instead.
        m = dist / cosh if cosh > 0.34 else dist * 2.9
        out.append(add(p1, mul(bis, m)))
    return out
