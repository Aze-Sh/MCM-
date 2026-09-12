"""Bearing-wedge intersection without an artificial bounding box."""
import math
from itertools import combinations


def cross(a, b):
    return a[0]*b[1] - a[1]*b[0]


def hull(points):
    points = sorted(set(points))
    if len(points) <= 1:
        return points
    def chain(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and cross((out[-1][0]-out[-2][0], out[-1][1]-out[-2][1]),
                                         (p[0]-out[-1][0], p[1]-out[-1][1])) <= 0:
                out.pop()
            out.append(p)
        return out
    return chain(points)[:-1] + chain(points[::-1])[:-1]


def farthest_pair(vertices):
    """Rotating calipers on a counterclockwise convex hull."""
    n = len(vertices)
    if n == 1:
        return vertices[0], vertices[0]
    if n == 2:
        return tuple(vertices)
    best = (vertices[0], vertices[1])
    best_d = math.dist(*best)
    j = 1
    for i in range(n):
        nxt = (i+1) % n
        edge = (vertices[nxt][0]-vertices[i][0], vertices[nxt][1]-vertices[i][1])
        def area(k):
            return abs(cross(edge, (vertices[k][0]-vertices[i][0], vertices[k][1]-vertices[i][1])))
        steps = 0
        while area((j+1) % n) > area(j) and steps < n:
            j = (j+1) % n
            steps += 1
        for a in (i, nxt):
            for b in (j, (j+1) % n):
                d = math.dist(vertices[a], vertices[b])
                if d > best_d:
                    best, best_d = (vertices[a], vertices[b]), d
    return best


def solve_wedges(observations, epsilon_deg=1.005):
    """Each observation is {x,y,bearing_deg}; all units are metres/degrees.

    Boundary intersections plus feasibility filtering cost O(n^3). This small-n
    implementation prioritizes explicit degeneracy states over hidden clipping.
    Floating-point results are numerical estimates, not exact certificates.
    """
    if not math.isfinite(epsilon_deg) or not 0 < epsilon_deg < 90:
        raise ValueError("epsilon_deg must lie in (0, 90)")
    planes = []
    for obs in observations:
        x, y, angle = (float(obs[k]) for k in ("x", "y", "bearing_deg"))
        if not all(math.isfinite(v) for v in (x, y, angle)):
            raise ValueError("Observations must be finite")
        lo, hi = math.radians(angle-epsilon_deg), math.radians(angle+epsilon_deg)
        for nx, ny in ((math.sin(lo), -math.cos(lo)), (-math.sin(hi), math.cos(hi))):
            planes.append((nx, ny, nx*x+ny*y))
    base = dict(epsilon_deg=epsilon_deg, diameter=None, vertices=[],
                numerical_method="float64; relative feasibility tolerance 1e-10")
    if not planes:
        return dict(base, state="UNBOUNDED")
    def feasible(x, y):
        return all(a*x+b*y-c <= 1e-10*(1+abs(a*x)+abs(b*y)+abs(c)) for a,b,c in planes)
    candidates = []
    for (a,b,c), (d,e,f) in combinations(planes, 2):
        det = a*e-b*d
        if abs(det) <= 1e-14:
            continue
        x, y = (c*e-b*f)/det, (a*f-c*d)/det
        if not math.isfinite(x) or not math.isfinite(y):
            return dict(base, state="NUMERICALLY_UNRESOLVED")
        if feasible(x, y):
            candidates.append((x,y))
    if not candidates:
        return dict(base, state="EMPTY_OR_NUMERICALLY_UNRESOLVED")
    # A nonzero recession ray makes the intersection unbounded.
    for a,b,_ in planes:
        for dx,dy in ((b,-a),(-b,a)):
            if all(u*dx+v*dy <= 1e-14 for u,v,_ in planes):
                return dict(base, state="UNBOUNDED", feasible_point=candidates[0])
    vertices = hull(candidates)
    p,q = farthest_pair(vertices)
    diameter = math.dist(p,q)
    center = ((p[0]+q[0])/2, (p[1]+q[1])/2)
    radius = diameter/2
    return dict(base, state={1:"POINT",2:"SEGMENT"}.get(len(vertices),"POLYGON"),
                vertices=vertices, diameter=diameter, farthest_pair=(p,q),
                diameter_circle_center=center, diameter_circle_radius=radius,
                diameter_circle_covers=all(math.dist(v,center) <= radius+1e-9*(1+radius) for v in vertices))
