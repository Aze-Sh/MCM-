"""History-aware outer regions and minimum-travel robust clearance.

Independent implementation inspired by the supplied repository's region idea.
No simulator, third-party runtime, probability model, or network dependency.
"""
from dataclasses import replace
from itertools import combinations
import math
from strategy import CLEAR_RADIUS, distance, terminal_clear_point, annular_clear_point

MARGIN = 1e-7  # Metres; relax halfplanes outward before clipping.
EPSILON = math.radians(1.005)


def clip(polygon, nx, ny, bound):
    """Intersect an ordered convex polygon with a relaxed unit-normal plane."""
    if not polygon:
        return []
    bound += MARGIN
    out = []
    previous = polygon[-1]
    dp = nx*previous[0]+ny*previous[1]-bound
    for point in polygon:
        dq = nx*point[0]+ny*point[1]-bound
        if (dp <= 0) != (dq <= 0):
            ratio = dp/(dp-dq)
            out.append((previous[0]+ratio*(point[0]-previous[0]),
                        previous[1]+ratio*(point[1]-previous[1])))
        if dq <= 0:
            out.append(point)
        previous, dp = point, dq
    return out


def constrain(polygon, anchor, annular=False):
    angle = math.radians(anchor.bearing)
    lo, hi = angle-EPSILON, angle+EPSILON
    # A truncated forward wedge is an outer approximation of the range sector.
    for nx,ny,offset in ((math.sin(lo),-math.cos(lo),0),
                         (-math.sin(hi),math.cos(hi),0),
                         (math.cos(angle),math.sin(angle),anchor.bound)):
        polygon = clip(polygon,nx,ny,nx*anchor.point[0]+ny*anchor.point[1]+offset)
    if annular:
        nx,ny = -math.cos(angle),-math.sin(angle)
        polygon = clip(polygon,nx,ny,nx*anchor.point[0]+ny*anchor.point[1]-5*math.cos(EPSILON))
    if not polygon or not all(math.isfinite(x) for p in polygon for x in p):
        raise ArithmeticError("History region is empty or numerically unresolved")
    return polygon


def initial_region(anchor, annular=False):
    # This box comes from the specified 1800 m source disk, not arbitrary clipping.
    r = 1800+MARGIN
    polygon = [(-r,-r),(r,-r),(r,r),(-r,r)]
    for k in range(16):
        t = 2*math.pi*k/16
        polygon = clip(polygon,math.cos(t),math.sin(t),1800)
    return constrain(polygon,anchor,annular)


def omni_negative_cuts(polygon, positive, negatives):
    """Use only pre-clear, same-channel, omnidirectional observations."""
    for negative in negatives:
        d = distance(positive,negative)
        if d == 0:
            raise ArithmeticError("Same position has incompatible positive and negative responses")
        nx,ny = (negative[0]-positive[0])/d,(negative[1]-positive[1])/d
        midpoint = ((positive[0]+negative[0])/2,(positive[1]+negative[1])/2)
        polygon = clip(polygon,nx,ny,nx*midpoint[0]+ny*midpoint[1])
    if not polygon:
        raise ArithmeticError("Omnidirectional positive/negative history is inconsistent")
    return polygon


def tighten_anchor(anchor, polygon):
    # Norm is convex: maximum over a polygon occurs at a vertex.
    history_bound = max(distance(anchor.point,v) for v in polygon)+MARGIN
    return replace(anchor,bound=min(anchor.bound,history_bound))


def nearest_clear_point(polygon, current):
    """Project current onto intersection_v B(v, r); O(m^3), small convex regions.

    A projection is current itself, a projection onto one active circle, or an
    intersection of two active circles. An inward radius margin handles roundoff.
    """
    if not polygon:
        return None
    radius = CLEAR_RADIUS-1e-6
    def feasible(p):
        return all(distance(p,v) <= radius+1e-10 for v in polygon)
    if feasible(current):
        return current
    if any(distance(a,b) > 2*radius for a,b in combinations(polygon,2)):
        return None
    best, best_distance = None, float("inf")
    def consider(p):
        nonlocal best, best_distance
        travel = distance(current,p)
        if travel < best_distance and feasible(p):
            best,best_distance = p,travel
    for a in polygon:
        d = distance(current,a)
        if d > radius:
            consider((a[0]+radius*(current[0]-a[0])/d,
                      a[1]+radius*(current[1]-a[1])/d))
    for a,b in combinations(polygon,2):
        d = distance(a,b)
        if d <= 1e-12 or d > 2*radius:
            continue
        midpoint = ((a[0]+b[0])/2,(a[1]+b[1])/2)
        h = math.sqrt(max(0.0,radius*radius-d*d/4))
        dx,dy = -(b[1]-a[1])/d*h,(b[0]-a[0])/d*h
        consider((midpoint[0]+dx,midpoint[1]+dy))
        consider((midpoint[0]-dx,midpoint[1]-dy))
    return best


def clear_choice(anchor, polygon, current, annular=False):
    # The independent anchor certificate remains available even if a relaxed
    # outer polygon is slightly too wide to admit a history-based clear.
    baseline = annular_clear_point(anchor,current) if annular else terminal_clear_point(anchor,current)
    history = nearest_clear_point(polygon,current)
    if history is not None and (baseline is None or distance(current,history) < distance(current,baseline)):
        return history,"history_projection"
    return baseline,"anchor_certificate"
