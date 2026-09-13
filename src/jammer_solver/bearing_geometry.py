"""Shared distances, tolerances and the Q2 feasible observation region."""
import math
from dataclasses import dataclass

Point = tuple[float, float]
INITIAL_BOUND = 1500.0
CLEAR_RADIUS = 19.8
EPSILON_RAD = math.radians(1.005)


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


@dataclass(frozen=True)
class Anchor:
    point: Point
    bearing: float
    bound: float = INITIAL_BOUND
    rounds: int = 0

    def __post_init__(self):
        if (not all(math.isfinite(v) for v in (*self.point, self.bearing, self.bound))
                or not 0 <= self.bearing < 360 or not 0 < self.bound <= INITIAL_BOUND
                or self.rounds < 0):
            raise ValueError("Invalid anchor")


def second_point_region(first: Point, bearing: float, query=None):
    """Three-disk description after eliminating R >= max(1000, r)."""
    Anchor(first,bearing)
    centers = [tuple(first)]
    for sign in (1,-1):
        angle = math.radians(bearing)+sign*EPSILON_RAD
        centers.append((first[0]+1000*math.cos(angle),first[1]+1000*math.sin(angle)))
    normal = math.cos(math.radians(bearing)),math.sin(math.radians(bearing))
    result = dict(disk_centers=centers,disk_radii=[1000]*3,
                  forward_halfplane=dict(normal=normal,origin=first,relation="dot(normal, q-origin) >= 0"),
                  epsilon_deg=1.005,
                  scope="Exact for relaxed radial prior [0,1500] within forward halfplane; conservative for actual r>5 and source domain")
    if query is not None:
        if len(query)!=2 or not all(math.isfinite(v) for v in query):
            raise ValueError("Query must contain two finite coordinates")
        result["query_in_region"] = (all(distance(query,c)<=1000 for c in centers)
            and sum(normal[k]*(query[k]-first[k]) for k in (0,1))>=0)
    return result
