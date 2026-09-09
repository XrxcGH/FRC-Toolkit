"""Transliterations of the non-truss Lighten branches of the CURRENT
FRC Plate Geometry.txt: the rib lattices (isogrid / grid / diagonal), the
cell patterns (honeycomb / circles) with the loose-ring tie pass, and the
single pocket with its boss ties.  Inches, units stripped.

Source: FRC Plate Geometry.txt lines 705-2453.
"""
import math

from truss5 import (frc_auto_sizing, frc_min_corner_radius, island_centers,
                    sub, add, mul, dot, nrm)


def rib_angles(pattern, base):
    if pattern == "GRID":
        return [base, base + math.pi / 2]
    if pattern == "DIAGONAL":
        return [base + math.pi / 4, base + 3 * math.pi / 4]
    if pattern == "ISOGRID":
        return [base, base + math.pi / 3, base + 2 * math.pi / 3]
    return []


def _common(plate, holes, thickness, tool_dia, aggression, material, loading,
            auto_size=True, manual=None):
    if auto_size:
        s = frc_auto_sizing(thickness, aggression, tool_dia, material, loading)
    else:
        s = dict(manual)
        s.setdefault("holeFactor", 0.5)
        s["buckleCapped"] = False
    tool_rad = frc_min_corner_radius(tool_dia)
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
    span_x, span_y = rect[2] - rect[0], rect[3] - rect[1]
    size_cap = max(min(span_x, span_y) / 3.0, 0.3)
    pocket_used = min(s["pocket"], size_cap)
    reach = math.hypot(span_x, span_y) / 2.0 + pocket_used
    pitch = pocket_used + s["rib"]
    note = ""
    if size_cap < s["pocket"]:
        # The source names the capped value now, so the note is self-contained
        # even on the truss, whose panel deliberately suppresses the pocket
        # figure. Same "%.4g in" style the buckling note below already uses.
        note = " NOTE Pocket capped at %.4g in by the part size." % size_cap
    elif s.get("buckleCapped"):
        note = (" NOTE Pocket limited by rib buckling at %.4g in plate."
                % thickness)
    return {"s": s, "toolRad": tool_rad, "rect": rect, "islands": islands,
            "thickness": thickness,
            "c2": c2, "spanX": span_x, "spanY": span_y,
            "pocketUsed": pocket_used, "reach": reach, "pitch": pitch,
            "plate": plate, "holes": holes, "note": note}


def wall_held(isl, rect):
    near = min(isl["center"][0] - rect[0], rect[2] - isl["center"][0],
               isl["center"][1] - rect[1], rect[3] - isl["center"][1])
    return near <= isl["r"] + 0.02


def frc_rib_spans(pattern, base_angle, c2, pitch, rib_w, reach):
    """FRC Plate Geometry.txt lines 493-541."""
    angles = rib_angles(pattern, base_angle)
    n_each = int(math.ceil(reach / pitch)) + 1
    spans = []
    for ai, a in enumerate(angles):
        u = (math.cos(a), math.sin(a))
        v = (-math.sin(a), math.cos(a))
        for k in range(-n_each, n_each + 1):
            base = add(c2, mul(v, k * pitch))
            cuts = [(-reach, 0.0)]
            for bi, b in enumerate(angles):
                if bi == ai:
                    continue
                ub = (math.cos(b), math.sin(b))
                vb = (-math.sin(b), math.cos(b))
                den = dot(u, vb)
                if abs(den) < 1e-9:
                    continue
                sinab = max(abs(u[0] * ub[1] - u[1] * ub[0]), 1e-6)
                clear = (rib_w / 2.0) / sinab
                offv = dot(sub(base, c2), vb)
                for j in range(-n_each - 1, n_each + 2):
                    t = (j * pitch - offv) / den
                    if -reach <= t <= reach:
                        cuts.append((t, clear))
            cuts.append((reach, 0.0))
            cuts.sort(key=lambda x: x[0])
            for m in range(len(cuts) - 1):
                t0 = cuts[m][0] + cuts[m][1]
                t1 = cuts[m + 1][0] - cuts[m + 1][1]
                if t1 > t0:
                    spans.append({"start": add(base, mul(u, t0)), "u": u,
                                  "L": t1 - t0})
    return spans


def build_lattice(plate, holes, pattern, thickness=0.25, tool_dia=0.25,
                  aggression="AGGRESSIVE", material="AL_6061",
                  loading="EDGE_ON", pattern_angle=0.0,
                  auto_size=True, manual=None):
    g = _common(plate, holes, thickness, tool_dia, aggression, material,
                loading, auto_size, manual)
    s, tool_rad = g["s"], g["toolRad"]
    c2, pitch, reach = g["c2"], g["pitch"], g["reach"]
    span_x, span_y = g["spanX"], g["spanY"]
    islands = g["islands"]
    angles = rib_angles(pattern, pattern_angle)

    # --- lattice offset search (lines 2249-2291) -------------------------
    c_lat = c2
    if islands:
        e0 = (-math.sin(angles[0]), math.cos(angles[0]))
        e1 = (-math.sin(angles[1]), math.cos(angles[1]))
        hw = s["rib"] / 2.0 + tool_rad
        best_bad, best_off = -1, 0.0
        for ia in range(12):
            for ib in range(12):
                cand = add(c2, add(mul(e0, ia * pitch / 12.0),
                                   mul(e1, ib * pitch / 12.0)))
                if nrm(sub(cand, c2)) > 0.75 * pitch:
                    continue
                bad = 0
                for a in angles:
                    v = (-math.sin(a), math.cos(a))
                    for isl in islands:
                        so = dot(sub(isl["center"], cand), v)
                        e_off = abs(so - round(so / pitch) * pitch)
                        if abs(e_off - isl["r"]) < hw:
                            bad += 1
                off = nrm(sub(cand, c2))
                if best_bad < 0 or bad < best_bad or (bad == best_bad
                                                     and off < best_off):
                    best_bad, best_off, c_lat = bad, off, cand

    n_each = int(math.ceil(reach / pitch)) + 1
    if len(angles) * (2 * n_each + 1) > 400:
        raise ValueError("too many ribs")
    bars = 0
    bands = []       # (angle a, v, offset from c_lat along v)
    for a in angles:
        u = (math.cos(a), math.sin(a))
        v = (-math.sin(a), math.cos(a))
        v_half = abs(v[0]) * span_x / 2.0 + abs(v[1]) * span_y / 2.0
        v_shift = dot(sub(c_lat, c2), v)
        for k in range(-n_each, n_each + 1):
            bands.append((v, dot(c_lat, v) + k * pitch,
                          s["rib"] / 2.0 + tool_rad))
            if abs(v_shift + k * pitch) <= v_half + s["rib"] / 2.0:
                bars += 1
    rib_count = bars
    spans = frc_rib_spans(pattern, pattern_angle, c_lat, pitch, s["rib"],
                          reach)

    # --- boss spoke pass (lines 2391-2453) -------------------------------
    needy = []
    for isl in islands:
        touched = False
        for a in angles:
            v = (-math.sin(a), math.cos(a))
            s_off = dot(sub(isl["center"], c_lat), v)
            if (abs(s_off - round(s_off / pitch) * pitch) - s["rib"] / 2.0
                    - isl["r"]) <= 0.0:
                touched = True
                break
        if not touched and not wall_held(isl, g["rect"]):
            needy.append(isl)
    spokes = []       # (center, u, length, halfwidth)
    if needy:
        k_span = min(int(math.ceil(2 * reach / pitch)) + 2, 60)
        for d in range(3):
            a = math.radians([10.0, 130.0, 250.0][d]) + pattern_angle
            u = (math.cos(a), math.sin(a))
            for isl in needy:
                L = 2 * reach
                for ra in angles:
                    v = (-math.sin(ra), math.cos(ra))
                    uv = dot(u, v)
                    if abs(uv) < 1e-6:
                        continue
                    s0 = dot(sub(isl["center"], c_lat), v)
                    for kk in range(-k_span, k_span + 1):
                        dd = (kk * pitch - s0) / uv
                        if isl["r"] < dd < L:
                            L = dd
                # The bar ends ON the rib centre line. It used to run a rib
                # width past it, which pushed the leading corner of its square
                # end rib*cos + half*sin beyond the line and left a stub
                # standing in the next pocket at every setting.
                spokes.append((isl["center"], u, L,
                               s["rib"] / 2.0 + tool_rad))

    detail = "%d ribs" % bars
    n_holes = len(islands)
    msg = ("%s, %d hole%s. Wall %.4g in, rib %.4g in, pocket %.4g in."
           % (detail, n_holes, "" if n_holes == 1 else "s",
              s["wall"], s["rib"], g["pocketUsed"]))
    g.update({"pattern": pattern, "angles": angles, "cLat": c_lat,
              "bands": bands, "spokes": spokes, "ribs": rib_count,
              "ribSpans": spans, "needy": len(needy), "detail": detail,
              "panel": msg})
    return g


def build_cells6(plate, holes, kind, thickness=0.25, tool_dia=0.25,
                 aggression="AGGRESSIVE", material="AL_6061",
                 loading="EDGE_ON", pattern_angle=0.0,
                 auto_size=True, manual=None):
    """Honeycomb / circles, including the loose-ring tie pass
    (lines 1946-2227)."""
    g = _common(plate, holes, thickness, tool_dia, aggression, material,
                loading, auto_size, manual)
    s, tool_rad = g["s"], g["toolRad"]
    c2, pitch, reach = g["c2"], g["pitch"], g["reach"]
    span_x, span_y = g["spanX"], g["spanY"]
    islands = g["islands"]
    pocket_used = g["pocketUsed"]
    is_hex = kind == "HONEYCOMB"
    # The source takes the cutter radius off in the same measure the grow-back
    # puts it on. A hexagon grows on its INRADIUS while cell_r is a
    # CIRCUMradius, so subtracting there shrank the inradius by only
    # tool_rad sqrt(3)/2 against a full tool_rad of grow-back, finishing
    # (2 - sqrt 3) tool_rad oversize across the flats.
    cell_r = ((pocket_used - 2.0 * tool_rad) / math.sqrt(3.0) if is_hex
              else pocket_used / 2.0 - tool_rad)

    def on_part(c):
        return (abs(c[0] - c2[0]) <= span_x / 2 + cell_r
                and abs(c[1] - c2[1]) <= span_y / 2 + cell_r)

    best_centers, best_on = [], -1
    for ph in ((0.0, 0.0), (0.5, 0.0), (0.25, 0.5), (0.5, 0.5)):
        cand = island_centers(c2, reach, pitch, pattern_angle, ph)
        on = sum(1 for c in cand if on_part(c))
        if on > best_on:
            best_on, best_centers = on, cand
    if len(best_centers) > 900:
        raise ValueError("too many cells")
    cell_at = []
    for c in best_centers:
        if not on_part(c):
            continue
        grazed = False
        for isl in islands:
            if (nrm(sub(c, isl["center"])) + cell_r - (isl["r"] + tool_rad)
                    < s["rib"] - 2 * tool_rad):
                grazed = True
                break
        if not grazed:
            cell_at.append(c)
    detail = "%d cells" % len(cell_at)

    # --- the loose-ring tie pass ----------------------------------------
    cull_r = cell_r + 2 * tool_rad
    fin_r = cell_r + tool_rad
    fin_in = cell_r * math.sqrt(3.0) / 2.0 + tool_rad
    hex_n = [(math.cos(pattern_angle + k * math.pi / 3.0),
              math.sin(pattern_angle + k * math.pi / 3.0)) for k in range(3)]

    def covered(q, cs):
        for c in cs:
            if abs(q[0] - c[0]) > cull_r or abs(q[1] - c[1]) > cull_r:
                continue
            if is_hex:
                if all(abs(dot(sub(q, c), nv)) <= fin_in for nv in hex_n):
                    return True
            elif nrm(sub(q, c)) <= fin_r:
                return True
        return False

    hold_w = max(0.6 * s["rib"], 0.08)
    link_w = max(0.4 * s["rib"], 0.05)
    n_dir = 36
    scan_cap = 2 * pitch + 2 * cell_r
    scan_step = 0.05
    n_step = min(int(math.ceil(scan_cap / scan_step)), 300)
    ties = []          # (center, u, tieLen, halfwidth)
    tie_spans = []
    loose_refused = 0
    for isl in islands:
        if wall_held(isl, g["rect"]):
            continue
        near_at = [c for c in cell_at
                   if nrm(sub(c, isl["center"])) <= isl["r"] + scan_cap
                   + cull_r]
        free = []
        for j in range(n_dir):
            a = 2 * math.pi * j / n_dir
            free.append(not covered(add(isl["center"],
                                        mul((math.cos(a), math.sin(a)),
                                            isl["r"] + 0.01)), near_at))
        best = run = 0
        for j in range(2 * n_dir):
            if free[j % n_dir]:
                run += 1
                best = max(best, run)
            else:
                run = 0
        best = min(best, n_dir)
        if isl["r"] * (2 * math.pi * best / n_dir) >= hold_w:
            continue
        order = []
        for j in range(n_dir):
            a = 2 * math.pi * j / n_dir
            u = (math.cos(a), math.sin(a))
            seen = -1.0
            hit = -1.0
            for kk in range(n_step + 1):
                dd = isl["r"] + kk * scan_step
                if covered(add(isl["center"], mul(u, dd)), near_at):
                    seen = -1.0
                else:
                    if seen < 0.0:
                        seen = dd
                    if dd - seen >= link_w:
                        hit = dd
                        break
            if hit > 0.0:
                order.append((hit, j))
        order.sort(key=lambda e: (e[0], e[1]))
        used = []
        for e in order:
            if len(used) >= 2:
                break
            a = 2 * math.pi * e[1] / n_dir
            u = (math.cos(a), math.sin(a))
            if any(dot(u, w) > math.cos(math.radians(50)) for w in used):
                continue
            used.append(u)
            tie_len = e[0]
            tie_spans.append({"start": add(isl["center"], mul(u, isl["r"])),
                              "u": u, "L": tie_len - isl["r"]})
            ties.append((isl["center"], u, tie_len,
                         s["rib"] / 2.0 + tool_rad))
        if not used:
            loose_refused += 1
    rib_count = 0
    if ties:
        detail += ", %d ties" % len(ties)
        rib_count = len(ties)

    n_holes = len(islands)
    msg = ("%s, %d hole%s. Wall %.4g in, rib %.4g in, pocket %.4g in."
           % (detail, n_holes, "" if n_holes == 1 else "s",
              s["wall"], s["rib"], pocket_used))
    g.update({"kind": kind, "isHex": is_hex, "cellR": cell_r,
              "cellAt": cell_at, "angle": pattern_angle, "ties": ties,
              "ribSpans": tie_spans, "ribs": rib_count,
              "looseRefused": loose_refused, "detail": detail, "panel": msg})
    return g


def frc_wall_extension(grow, rib_dir, wall_dir, cap_multiple):
    sin_arrival = abs(rib_dir[0] * wall_dir[1] - rib_dir[1] * wall_dir[0])
    if sin_arrival < 1e-6:
        return None
    if 1 / sin_arrival > cap_multiple:
        return None
    return grow / sin_arrival


def build_none6(plate, holes, thickness=0.25, tool_dia=0.25,
                aggression="AGGRESSIVE", material="AL_6061",
                loading="EDGE_ON", auto_size=True, manual=None):
    """The single pocket with its boss ties (lines 836-950)."""
    from truss5 import perimeter_stations
    g = _common(plate, holes, thickness, tool_dia, aggression, material,
                loading, auto_size, manual)
    s, tool_rad = g["s"], g["toolRad"]
    span_x, span_y = g["spanX"], g["spanY"]
    islands = g["islands"]
    loose = [isl for isl in islands if not wall_held(isl, g["rect"])]
    ties = []
    tie_spans = []
    if loose:
        st_n = perimeter_stations(g["rect"],
                                  max(min(span_x, span_y) / 6.0, 0.5))
        if len(st_n) < 2:
            raise ValueError("outline could not be followed")
        for isl in loose:
            order = sorted(range(len(st_n)),
                           key=lambda k: (nrm(sub(st_n[k]["point"],
                                                  isl["center"])), k))
            used = []
            for k in order:
                if len(used) >= 2:
                    break
                st = st_n[k]
                away = sub(st["point"], isl["center"])
                L = nrm(away)
                if L < isl["r"] + s["rib"]:
                    continue
                u = mul(away, 1.0 / L)
                if any(dot(u, w) > math.cos(math.radians(50)) for w in used):
                    continue
                ext = frc_wall_extension(s["wall"] + s["rib"] + tool_rad, u,
                                         st["direction"], 4)
                if ext is None:
                    continue
                used.append(u)
                tie_spans.append({"start": add(isl["center"],
                                               mul(u, isl["r"])),
                                  "u": u, "L": L - isl["r"]})
                ties.append((isl["center"], u, L + ext,
                             s["rib"] / 2.0 + tool_rad))
            if not used:
                raise ValueError("boss cannot be tied back")
    detail = ("1 pocket, %d ties" % len(ties)) if ties else "1 pocket"
    n_holes = len(islands)
    # NB the FS panel appends ", pocket X in" for every pattern that is not
    # the truss, the single pocket included, although NONE never uses the
    # pocket size for anything it cuts.
    msg = ("%s, %d hole%s. Wall %.4g in, rib %.4g in, pocket %.4g in."
           % (detail, n_holes, "" if n_holes == 1 else "s",
              s["wall"], s["rib"], g["pocketUsed"]))
    g.update({"ties": ties, "ribSpans": tie_spans, "ribs": len(ties),
              "loose": len(loose), "detail": detail, "panel": msg})
    return g
