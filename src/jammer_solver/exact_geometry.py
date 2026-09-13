from fractions import Fraction as F
from functools import lru_cache
import math

PI_LO = F("3.14159265358979323846264338327950288419716939937510")
PI_HI = PI_LO + F(1, 10**50)
EPS = F(201, 200)
DOMAIN = F(1800)


def point(p):
    if len(p) != 2 or not all((math.isfinite(float(x)) for x in p)):
        raise ValueError("Non-finite point")
    return tuple((F(x) for x in p))


def floating(p):
    return tuple((float(x) for x in p))


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def squared(a, b):
    return dot(sub(a, b), sub(a, b))


def ceil_distance(a, b, scale=1000):
    v = squared(a, b) * scale * scale
    k = math.isqrt(v.numerator // v.denominator)
    if F(k * k) < v:
        k += 1
    return F(k, scale)


def floor_distance(a, b, scale=1000):
    v = squared(a, b) * scale * scale
    return F(math.isqrt(v.numerator // v.denominator), scale)


def rectangle(x0, y0, x1, y1):
    return [point(p) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def hull(points):
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts
    lo, hi = ([], [])
    for p in pts:
        while len(lo) > 1 and cross(sub(lo[-1], lo[-2]), sub(p, lo[-1])) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) > 1 and cross(sub(hi[-1], hi[-2]), sub(p, hi[-1])) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def clip(poly, normal, bound):
    if not poly:
        return []
    out = []
    a = poly[-1]
    fa = dot(normal, a) - bound
    for b in poly:
        fb = dot(normal, b) - bound
        if (fa > 0) != (fb > 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        if fb <= 0:
            out.append(b)
        a, fa = (b, fb)
    result = []
    for p in out:
        if not result or result[-1] != p:
            result.append(p)
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()
    return result


def contains(poly, p):
    if not poly:
        return False
    if len(poly) == 1:
        return p == poly[0]
    if len(poly) == 2:
        return (
            cross(sub(poly[1], poly[0]), sub(p, poly[0])) == 0
            and dot(sub(p, poly[0]), sub(p, poly[1])) <= 0
        )
    return all(
        (cross(sub(b, a), sub(p, a)) >= 0 for a, b in zip(poly, poly[1:] + poly[:1]))
    )


@lru_cache(maxsize=4096)
def trig(degrees):
    degrees = F(degrees)
    quadrant = int((degrees + 45) // 90)
    d = degrees - 90 * quadrant
    x = d * (PI_LO + PI_HI) / 360
    err = abs(d) * (PI_HI - PI_LO) / 360
    sin = sum(
        ((-1) ** j * x ** (2 * j + 1) / math.factorial(2 * j + 1) for j in range(10)),
        F(0),
    )
    cos = sum(
        ((-1) ** j * x ** (2 * j) / math.factorial(2 * j) for j in range(10)), F(0)
    )
    se = F(1, math.factorial(20)) + err
    ce = F(1, math.factorial(19)) + err
    c, s = ((cos - ce, cos + ce), (sin - se, sin + se))
    for _ in range(quadrant % 4):
        c, s = ((-s[1], -s[0]), c)
    scale = 10**12

    def outward(pair):
        a, b = pair
        return (F(a * scale // 1, scale), F(-(-b * scale // 1), scale))

    return (*outward(c), *outward(s))


def direction(degrees):
    cl, ch, sl, sh = trig(F(degrees))
    return (((cl + ch) / 2, (sl + sh) / 2), ((ch - cl) / 2, (sh - sl) / 2))


def uncertain_plane(poly, origin, normal, error, rhs=F(0)):
    slack = error[0] * (DOMAIN + abs(origin[0])) + error[1] * (DOMAIN + abs(origin[1]))
    return clip(poly, normal, dot(normal, origin) + rhs + slack)


@lru_cache(maxsize=1)
def source_domain():
    poly = rectangle(-1800, -1800, 1800, 1800)
    for angle in range(0, 360, 15):
        u, e = direction(F(angle))
        poly = uncertain_plane(poly, point((0, 0)), u, e, F(1800))
    return tuple(poly)


def bearing_constraints(origin, lo, hi=None):
    hi = lo if hi is None else hi
    if F(hi) - F(lo) + 2 * EPS >= 180:
        return []
    ulo, elo = direction(F(lo) - EPS)
    uhi, ehi = direction(F(hi) + EPS)
    return [
        ((ulo[1], -ulo[0]), (elo[1], elo[0]), F(0)),
        ((-uhi[1], uhi[0]), (ehi[1], ehi[0]), F(0)),
    ]


def apply_bearing(poly, origin, bearing, radius=F(1500), hi=None):
    constraints = bearing_constraints(origin, bearing, hi)
    if hi is None:
        u, e = direction(F(bearing))
        ce = trig(EPS)[0]
        constraints += [(u, e, radius), ((-u[0], -u[1]), e, -5 * ce)]
    for n, e, b in constraints:
        poly = uncertain_plane(poly, origin, n, e, b)
    for n, b in (
        ((1, 0), origin[0] + 1500),
        ((-1, 0), 1500 - origin[0]),
        ((0, 1), origin[1] + 1500),
        ((0, -1), 1500 - origin[1]),
    ):
        poly = clip(poly, n, b)
    return poly


def transformed_box(origin, bearing, bounds):
    u, e = direction(F(bearing))
    corners = rectangle(*bounds)
    out = []
    for x, y in corners:
        center = (origin[0] + u[0] * x - u[1] * y, origin[1] + u[1] * x + u[0] * y)
        dx, dy = (e[0] * abs(x) + e[1] * abs(y), e[1] * abs(x) + e[0] * abs(y))
        out += rectangle(center[0] - dx, center[1] - dy, center[0] + dx, center[1] + dy)
    return hull(out)


def rotated_point(origin, bearing, x, y):
    u, e = direction(F(bearing))
    ideal_mid = (origin[0] + u[0] * x - u[1] * y, origin[1] + u[1] * x + u[0] * y)
    p = point(floating(ideal_mid))
    dx = abs(p[0] - ideal_mid[0]) + e[0] * abs(x) + e[1] * abs(y)
    dy = abs(p[1] - ideal_mid[1]) + e[1] * abs(x) + e[0] * abs(y)
    if dx * dx + dy * dy > 1:
        raise ArithmeticError("Rotation exceeds the certified 1 m allowance")
    return p


def disk_contains(poly, center, radius):
    return bool(poly) and all((squared(v, center) <= radius * radius for v in poly))


def verified_pair_cut(poly, positive, a, b):
    va, vb = (sub(a, positive), sub(b, positive))
    if cross(va, vb) < 0:
        a, b, va, vb = (b, a, vb, va)
    if cross(va, vb) == 0:
        return (poly, False)
    edge = sub(b, a)
    normal = (edge[1], -edge[0])
    bound = dot(normal, a)
    if dot(normal, positive) > bound:
        normal = (-normal[0], -normal[1])
        bound = -bound
    outside = clip(poly, (-normal[0], -normal[1]), -bound)
    if not outside:
        return (poly, False)
    if not all(
        (
            cross(va, sub(s, positive)) >= 0 and cross(sub(s, positive), vb) >= 0
            for s in outside
        )
    ):
        return (poly, False)
    if not disk_contains(outside, a, F(1000)) or not disk_contains(outside, b, F(1000)):
        return (poly, False)
    result = clip(poly, normal, bound)
    return (result, result != poly)


def search_grid():
    return [
        point((600 * i, 600 * j))
        for j in range(-3, 4)
        for i in (range(-3, 4) if j % 2 else range(3, -4, -1))
    ]


@lru_cache(maxsize=256)
def coverage_certificate(radio, optical, problem, max_nodes=2048, max_depth=12):
    radio, optical = (tuple(map(point, radio)), tuple(map(point, optical)))
    stack = [(rectangle(-1800, -1800, 1800, 1800), 0)]
    nodes = 0
    leaves = []
    r_float = [(q, floating(q)) for q in radio]
    while stack and nodes < max_nodes:
        box, depth = stack.pop()
        nodes += 1
        x0, y0 = box[0]
        x1, y1 = box[2]
        dx, dy = (max(F(0), x0, -x1), max(F(0), y0, -y1))
        if dx * dx + dy * dy > DOMAIN**2:
            continue
        optical_hit = next((q for q in optical if disk_contains(box, q, F(20))), None)
        if optical_hit is not None:
            leaves.append(("optical", box, [optical_hit]))
            continue
        bf = [floating(v) for v in box]
        nearby = [
            q
            for q, qf in r_float
            if all((math.dist(qf, v) < 1000.000001 for v in bf))
            and disk_contains(box, q, F(1000))
        ]
        if problem == 3 and nearby:
            leaves.append(("omni", box, nearby[:1]))
            continue
        if problem == 4 and len(nearby) >= 3:
            h = hull(nearby)
            if all((contains(h, v) for v in box)):
                leaves.append(("directional_hull", box, h))
                continue
        if depth >= max_depth:
            return (False, nodes, tuple(map(float, (x0, y0, x1, y1))), ())
        mx, my = ((x0 + x1) / 2, (y0 + y1) / 2)
        stack.extend(
            (
                (rectangle(*v), depth + 1)
                for v in (
                    (x0, y0, mx, my),
                    (mx, y0, x1, my),
                    (x0, my, mx, y1),
                    (mx, my, x1, y1),
                )
            )
        )
    if stack:
        box, _ = stack[-1]
        return (False, nodes, (*floating(box[0]), *floating(box[2])), ())
    return (True, nodes, None, tuple(leaves))
