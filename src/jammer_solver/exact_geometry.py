from fractions import Fraction as fs
from functools import lru_cache as cache
import math

pilo = fs("3.14159265358979323846264338327950288419716939937510")
pihi = pilo + fs(1, 10**50)
eps = fs(201, 200)
domain = fs(1800)


def point(p):
    if len(p) != 2 or not all((math.isfinite(float(x)) for x in p)):
        raise ValueError("Non-finite point")
    return tuple((fs(x) for x in p))


def jlsx(a, b, scale=1000):
    v = ((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1])) * scale * scale
    k = math.isqrt(v.numerator // v.denominator)
    if fs(k * k) < v:
        k += 1
    return fs(k, scale)


def juxing(x0, y0, x1, y1):
    return [point(p) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def hull(points):
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts
    lo, hi = ([], [])
    for p in pts:
        while (
            len(lo) > 1
            and (lo[-1][0] - lo[-2][0]) * (p[1] - lo[-1][1])
            - (lo[-1][1] - lo[-2][1]) * (p[0] - lo[-1][0])
            <= 0
        ):
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while (
            len(hi) > 1
            and (hi[-1][0] - hi[-2][0]) * (p[1] - hi[-1][1])
            - (hi[-1][1] - hi[-2][1]) * (p[0] - hi[-1][0])
            <= 0
        ):
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def clip(poly, normal, bound):
    if not poly:
        return []
    out = []
    a = poly[-1]
    fa = normal[0] * a[0] + normal[1] * a[1] - bound
    for b in poly:
        fb = normal[0] * b[0] + normal[1] * b[1] - bound
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
        return (poly[1][0] - poly[0][0]) * (p[1] - poly[0][1]) - (
            poly[1][1] - poly[0][1]
        ) * (p[0] - poly[0][0]) == 0 and (p[0] - poly[0][0]) * (p[0] - poly[1][0]) + (
            p[1] - poly[0][1]
        ) * (p[1] - poly[1][1]) <= 0
    return all(
        (
            (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0
            for a, b in zip(poly, poly[1:] + poly[:1])
        )
    )


@cache(maxsize=4096)
def trig(degrees):
    degrees = fs(degrees)
    xq = int((degrees + 45) // 90)
    d = degrees - 90 * xq
    x = d * (pilo + pihi) / 360
    err = abs(d) * (pihi - pilo) / 360
    sin = sum(
        ((-1) ** j * x ** (2 * j + 1) / math.factorial(2 * j + 1) for j in range(10)),
        fs(0),
    )
    cos = sum(
        ((-1) ** j * x ** (2 * j) / math.factorial(2 * j) for j in range(10)), fs(0)
    )
    se = fs(1, math.factorial(20)) + err
    ce = fs(1, math.factorial(19)) + err
    c, s = ((cos - ce, cos + ce), (sin - se, sin + se))
    for _ in range(xq % 4):
        c, s = ((-s[1], -s[0]), c)
    scale = 10**12

    def outward(pair):
        a, b = pair
        return (fs(a * scale // 1, scale), fs(-(-b * scale // 1), scale))

    return (*outward(c), *outward(s))


def fangxiang(degrees):
    cl, ch, sl, sh = trig(fs(degrees))
    return (((cl + ch) / 2, (sl + sh) / 2), ((ch - cl) / 2, (sh - sl) / 2))


def bqdpm(poly, origin, normal, error, rhs=fs(0)):
    slack = error[0] * (domain + abs(origin[0])) + error[1] * (domain + abs(origin[1]))
    return clip(
        poly, normal, normal[0] * origin[0] + normal[1] * origin[1] + rhs + slack
    )


@cache(maxsize=1)
def yfw():
    poly = juxing(-1800, -1800, 1800, 1800)
    for angle in range(0, 360, 15):
        u, e = fangxiang(fs(angle))
        poly = bqdpm(poly, point((0, 0)), u, e, fs(1800))
    return tuple(poly)


def fwys(lo, hi=None):
    hi = lo if hi is None else hi
    if fs(hi) - fs(lo) + 2 * eps >= 180:
        return []
    ulo, elo = fangxiang(fs(lo) - eps)
    uhi, ehi = fangxiang(fs(hi) + eps)
    return [
        ((ulo[1], -ulo[0]), (elo[1], elo[0]), fs(0)),
        ((-uhi[1], uhi[0]), (ehi[1], ehi[0]), fs(0)),
    ]


def jcfw(poly, origin, bearing, radius=fs(1500), hi=None):
    ys = fwys(bearing, hi)
    if hi is None:
        u, e = fangxiang(fs(bearing))
        ce = trig(eps)[0]
        ys += [(u, e, radius), ((-u[0], -u[1]), e, -5 * ce)]
    for n, e, b in ys:
        poly = bqdpm(poly, origin, n, e, b)
    for n, b in (
        ((1, 0), origin[0] + 1500),
        ((-1, 0), 1500 - origin[0]),
        ((0, 1), origin[1] + 1500),
        ((0, -1), 1500 - origin[1]),
    ):
        poly = clip(poly, n, b)
    return poly


def xzqj(origin, bearing, bounds):
    u, e = fangxiang(fs(bearing))
    corners = juxing(*bounds)
    out = []
    for x, y in corners:
        center = (origin[0] + u[0] * x - u[1] * y, origin[1] + u[1] * x + u[0] * y)
        dx, dy = (e[0] * abs(x) + e[1] * abs(y), e[1] * abs(x) + e[0] * abs(y))
        out += juxing(center[0] - dx, center[1] - dy, center[0] + dx, center[1] + dy)
    return hull(out)


def xzd(origin, bearing, x, y):
    u, e = fangxiang(fs(bearing))
    mid = (origin[0] + u[0] * x - u[1] * y, origin[1] + u[1] * x + u[0] * y)
    p = point(tuple((float(x) for x in mid)))
    dx = abs(p[0] - mid[0]) + e[0] * abs(x) + e[1] * abs(y)
    dy = abs(p[1] - mid[1]) + e[1] * abs(x) + e[0] * abs(y)
    if dx * dx + dy * dy > 1:
        raise ArithmeticError("Rotation exceeds the certified 1 m allowance")
    return p


def ypbh(poly, center, radius):
    return bool(poly) and all(
        (
            (v[0] - center[0]) * (v[0] - center[0])
            + (v[1] - center[1]) * (v[1] - center[1])
            <= radius * radius
            for v in poly
        )
    )


def syxc(poly, pos, a, b):
    va, vb = ((a[0] - pos[0], a[1] - pos[1]), (b[0] - pos[0], b[1] - pos[1]))
    if va[0] * vb[1] - va[1] * vb[0] < 0:
        a, b, va, vb = (b, a, vb, va)
    if va[0] * vb[1] - va[1] * vb[0] == 0:
        return (poly, False)
    edge = (b[0] - a[0], b[1] - a[1])
    normal = (edge[1], -edge[0])
    bound = normal[0] * a[0] + normal[1] * a[1]
    if normal[0] * pos[0] + normal[1] * pos[1] > bound:
        normal = (-normal[0], -normal[1])
        bound = -bound
    outside = clip(poly, (-normal[0], -normal[1]), -bound)
    if not outside:
        return (poly, False)
    if not all(
        (
            va[0] * (s[1] - pos[1]) - va[1] * (s[0] - pos[0]) >= 0
            and (s[0] - pos[0]) * vb[1] - (s[1] - pos[1]) * vb[0] >= 0
            for s in outside
        )
    ):
        return (poly, False)
    if not ypbh(outside, a, fs(1000)) or not ypbh(outside, b, fs(1000)):
        return (poly, False)
    result = clip(poly, normal, bound)
    return (result, result != poly)


def sswd():
    return [
        point((600 * i, 600 * j))
        for j in range(-3, 4)
        for i in (range(-3, 4) if j % 2 else range(3, -4, -1))
    ]


@cache(maxsize=256)
def fgzm(radio, optical, problem, jdmax=2048, sdmax=12):
    radio, optical = (tuple(map(point, radio)), tuple(map(point, optical)))
    stack = [(juxing(-1800, -1800, 1800, 1800), 0)]
    nodes = 0
    leaves = []
    rf = [(q, tuple((float(x) for x in q))) for q in radio]
    while stack and nodes < jdmax:
        box, depth = stack.pop()
        nodes += 1
        x0, y0 = box[0]
        x1, y1 = box[2]
        dx, dy = (max(fs(0), x0, -x1), max(fs(0), y0, -y1))
        if dx * dx + dy * dy > domain**2:
            continue
        hit = next((q for q in optical if ypbh(box, q, fs(20))), None)
        if hit is not None:
            leaves.append(("optical", box, [hit]))
            continue
        bf = [tuple((float(x) for x in v)) for v in box]
        nearby = [
            q
            for q, qf in rf
            if all((math.dist(qf, v) < 1000.000001 for v in bf))
            and ypbh(box, q, fs(1000))
        ]
        if problem == 3 and nearby:
            leaves.append(("omni", box, nearby[:1]))
            continue
        if problem == 4 and len(nearby) >= 3:
            h = hull(nearby)
            if all((contains(h, v) for v in box)):
                leaves.append(("directional_hull", box, h))
                continue
        if depth >= sdmax:
            return (False, nodes, tuple(map(float, (x0, y0, x1, y1))), ())
        mx, my = ((x0 + x1) / 2, (y0 + y1) / 2)
        stack.extend(
            (
                (juxing(*v), depth + 1)
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
        return (
            False,
            nodes,
            (*tuple((float(x) for x in box[0])), *tuple((float(x) for x in box[2]))),
            (),
        )
    return (True, nodes, None, tuple(leaves))
