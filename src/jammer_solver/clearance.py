"""Nearest point from which an entire source polygon can be cleared."""
import math
from itertools import combinations
from .bearing_geometry import CLEAR_RADIUS, distance


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
