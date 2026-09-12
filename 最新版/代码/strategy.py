"""Frozen midpoint strategy. Pure functions: no network, simulator, or randomness."""
from dataclasses import dataclass, replace
import math

Point = tuple[float, float]
INITIAL_BOUND = 1500.0
CLEAR_RADIUS = 19.8
POSITIVE_FACTOR = 0.502
NEGATIVE_FACTOR = 0.501
EPSILON_RAD = math.radians(1.005)
ANNULAR_STOP = 44.5


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


def offset(anchor: Anchor, forward: float, sideways: float) -> Point:
    angle = math.radians(anchor.bearing)
    ux, uy = math.cos(angle), math.sin(angle)
    return (anchor.point[0] + anchor.bound * (forward * ux - sideways * uy),
            anchor.point[1] + anchor.bound * (forward * uy + sideways * ux))


def paired_points(anchor: Anchor, current: Point) -> tuple[Point, Point]:
    plus, minus = offset(anchor, .5, .02), offset(anchor, .5, -.02)
    return (plus, minus) if distance(current, plus) <= distance(current, minus) else (minus, plus)


def terminal_clear_point(anchor: Anchor, current: Point) -> Point | None:
    slack = CLEAR_RADIUS - NEGATIVE_FACTOR * anchor.bound
    if slack < 0:
        return None
    midpoint = offset(anchor, .5, 0)
    d = distance(current, midpoint)
    if d <= slack:
        return current
    # A tiny inward margin avoids rounding outside the certified clearance disk.
    ratio = max(0.0, slack - 1e-8) / d
    return (midpoint[0] + ratio * (current[0] - midpoint[0]),
            midpoint[1] + ratio * (current[1] - midpoint[1]))


def positive_update(anchor: Anchor, point: Point, bearing: float) -> Anchor:
    return Anchor(point, bearing, POSITIVE_FACTOR * anchor.bound, anchor.rounds + 1)


def negative_pair_update(anchor: Anchor) -> Anchor:
    return replace(anchor, bound=NEGATIVE_FACTOR * anchor.bound, rounds=anchor.rounds + 1)


def search_points(problem: int) -> list[Point]:
    if problem == 3:
        return [(0.0, 0.0)] + [
            (1200 * math.cos(math.radians(60*k)), 1200 * math.sin(math.radians(60*k)))
            for k in range(6)]
    if problem == 4:
        return [(990.0 * (i + j/2), 990 * math.sqrt(3) * j/2)
                for i in range(-4, 5) for j in range(-4, 5) if i*i + i*j + j*j <= 7]
    raise ValueError("problem must be 3 or 4")


def next_search_point(current: Point, remaining: list[Point]) -> Point:
    return min(remaining, key=lambda q: (distance(current, q), q[0], q[1]))


def channel_order(current_channel: int, unknown: set[int]) -> list[int]:
    return sorted(unknown, key=lambda c: (c != current_channel, c))


def preview_source_action(anchor: Anchor, current: Point, tuned: int, channel: int):
    clear_point = terminal_clear_point(anchor, current)
    if clear_point is not None:
        return "/clear", clear_point, distance(current, clear_point)/5 + 5
    point = paired_points(anchor, current)[0]
    return "/measure", point, distance(current, point)/5 + 5 + int(tuned != channel)


def second_point(first: Point, bearing: float, current: Point | None = None) -> Point:
    anchor = Anchor(first, bearing)
    plus, minus = offset(anchor, .5, .4), offset(anchor, .5, -.4)
    return plus if current is None or distance(current, plus) <= distance(current, minus) else minus


def annular_points(anchor: Anchor, current: Point) -> tuple[Point, Point]:
    """Only for a normal direction response, hence source distance > 5 m."""
    forward = (anchor.bound+5)/(2*anchor.bound)
    plus,minus = offset(anchor,forward,.02),offset(anchor,forward,-.02)
    return (plus,minus) if distance(current,plus) <= distance(current,minus) else (minus,plus)


def annular_update(anchor: Anchor, point=None, bearing=None) -> Anchor:
    if anchor.bound <= ANNULAR_STOP:
        raise ValueError("The source should already be cleared; do not start another round")
    if point is None:
        return replace(anchor,bound=.501*anchor.bound+2.505,rounds=anchor.rounds+1)
    return Anchor(tuple(point),bearing,.502*anchor.bound-2.4,anchor.rounds+1)


def annular_clear_disk(anchor: Anchor):
    if anchor.bound <= 5:
        raise ValueError("A normal bearing must have source distance greater than 5 m")
    if anchor.bound > ANNULAR_STOP:
        return None
    L = anchor.bound
    cover = math.sqrt((L-5)**2/4+L*(L+5)*(1-math.cos(EPSILON_RAD)))
    return offset(anchor,(L+5)/(2*L),0),max(0.0,CLEAR_RADIUS-cover-1e-7)


def point_in_disk_nearest(center, radius, current):
    d = distance(center,current)
    if d <= radius:
        return current
    t = radius/d
    return center[0]+t*(current[0]-center[0]),center[1]+t*(current[1]-center[1])


def annular_clear_point(anchor: Anchor,current: Point):
    disk = annular_clear_disk(anchor)
    return None if disk is None else point_in_disk_nearest(*disk,current)


def second_point_region(first: Point, bearing: float, query=None):
    """Three-disk description after eliminating R >= max(1000, r)."""
    anchor = Anchor(first,bearing)
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
