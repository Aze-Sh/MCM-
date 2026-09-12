"""Forward bearing wedges, exact polyhedral region classification, and cover circles.

Floating point tolerance is in metres after unit-normal normalization. No artificial
bounding box is used to turn an unbounded intersection into a bounded answer.
"""
from dataclasses import dataclass
from itertools import combinations
import math

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull


@dataclass
class Region:
    status: str
    vertices: np.ndarray


def bearing_halfplanes(observations, error_deg=1.0):
    if not math.isfinite(error_deg) or not 0 < error_deg < 90:
        raise ValueError('Bearing half-width must be between 0 and 90 degrees')
    a, b = [], []
    for obs in observations:
        if len(obs) != 3 or not np.isfinite(obs).all():
            raise ValueError('Each observation must be finite (x, y, bearing_deg)')
        x, y, theta = obs
        lo, hi = np.deg2rad([(theta - error_deg) % 360, (theta + error_deg) % 360])
        # cross(u_lo, p-s)>=0, cross(u_hi, p-s)<=0.
        for normal in ([math.sin(lo), -math.cos(lo)], [-math.sin(hi), math.cos(hi)]):
            a.append(normal)
            b.append(normal[0] * x + normal[1] * y)
    return np.asarray(a, dtype=float).reshape(-1, 2), np.asarray(b, dtype=float)


def halfplane_region(a, b, tolerance=1e-7):
    a, b = np.asarray(a, float).reshape(-1, 2), np.asarray(b, float)
    empty = np.empty((0, 2))
    if b.shape != (len(a),) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Finite A(m,2) and b(m) required')
    norms = np.linalg.norm(a, axis=1)
    if np.any((norms == 0) & (b < 0)):
        return Region('empty', empty)
    keep = norms > 0
    a, b = a[keep] / norms[keep, None], b[keep] / norms[keep]
    if not len(a):
        return Region('unbounded', empty)
    bounds = [(None, None), (None, None)]
    feasible = linprog([0., 0.], A_ub=a, b_ub=b, bounds=bounds, method='highs')
    if feasible.status == 2:
        return Region('empty', empty)
    if not feasible.success:
        raise ArithmeticError('Feasibility solver could not certify region')
    for objective in ([1, 0], [-1, 0], [0, 1], [0, -1]):
        result = linprog(objective, A_ub=a, b_ub=b, bounds=bounds, method='highs')
        if result.status == 3:
            return Region('unbounded', empty)
        if not result.success:
            raise ArithmeticError('Boundedness solver could not certify region')
    vertices = []
    for i, j in combinations(range(len(a)), 2):
        matrix = a[[i, j]]
        if abs(np.linalg.det(matrix)) < 1e-12:
            continue
        point = np.linalg.solve(matrix, b[[i, j]])
        if np.max(a @ point - b) <= tolerance:
            if not any(np.linalg.norm(point - old) <= tolerance for old in vertices):
                vertices.append(point)
    if not vertices:
        raise ArithmeticError('Bounded region has no numerically resolved vertices')
    points = np.asarray(vertices)
    if len(points) >= 3 and np.linalg.matrix_rank(points - points[0], tol=tolerance) == 2:
        points = points[ConvexHull(points).vertices]
    return Region('bounded', points)


def bearing_region(observations, error_deg=1.0):
    return halfplane_region(*bearing_halfplanes(observations, error_deg))


def _points(points):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) == 0 or not np.isfinite(points).all():
        raise ValueError('Nonempty finite (n,2) points required')
    return points


def diameter(points):
    p = _points(points)
    return float(np.max(np.linalg.norm(p[:, None, :] - p[None, :, :], axis=2)))


def enclosing_circle(points):
    """Enumerate circles defined by 1/2/3 support vertices; intended for small regions.

    Evaluate actual max distance for every candidate centre so containment is never
    understated by a tolerance. Worst-case O(n^4), suitable as a verified baseline.
    """
    p = _points(points)
    best_center, best_radius = p[0].copy(), float('inf')
    def consider(center):
        nonlocal best_center, best_radius
        radius = float(np.max(np.linalg.norm(p - center, axis=1)))
        if radius < best_radius:
            best_center, best_radius = center, radius
    for point in p:
        consider(point)
    for i, j in combinations(range(len(p)), 2):
        consider((p[i] + p[j]) / 2)
    for i, j, k in combinations(range(len(p)), 3):
        # Translate to reduce cancellation for coordinates far from the origin.
        u, v = p[j] - p[i], p[k] - p[i]
        matrix = 2 * np.array([u, v])
        if abs(np.linalg.det(matrix)) <= 1e-12 * max(1., np.linalg.norm(u) * np.linalg.norm(v)):
            continue
        consider(p[i] + np.linalg.solve(matrix, [u @ u, v @ v]))
    return best_center, best_radius


def _point(point, name='point'):
    value = np.asarray(point, dtype=float)
    if value.shape != (2,) or not np.isfinite(value).all():
        raise ValueError(f'{name} must be a finite 2D point')
    return value


def _unit_vector(bearing_deg):
    if not math.isfinite(bearing_deg):
        raise ValueError('Bearing must be finite')
    angle = math.radians(bearing_deg)
    return np.array([math.cos(angle), math.sin(angle)])


def first_bearing_sector(
        sensor, bearing_deg, error_deg=1.0, max_range=1500.0,
        arc_samples=181):
    """Return a counter-clockwise polygonal sampling of the first feasible sector.

    The received direction value implies an unknown source lies within the bearing
    wedge and no farther than the largest possible receive radius.  The first point
    is included conservatively; a ``direction`` response in fact excludes the inner
    five-metre ``near`` disc.
    """
    sensor = _point(sensor, 'sensor')
    if not math.isfinite(error_deg) or not 0 < error_deg < 90:
        raise ValueError('Bearing half-width must be between 0 and 90 degrees')
    if not math.isfinite(max_range) or max_range <= 0:
        raise ValueError('Maximum range must be positive and finite')
    if not isinstance(arc_samples, int) or arc_samples < 2:
        raise ValueError('arc_samples must be an integer of at least 2')
    angles = np.deg2rad(np.linspace(
        bearing_deg - error_deg, bearing_deg + error_deg, arc_samples))
    arc = sensor + max_range * np.column_stack((np.cos(angles), np.sin(angles)))
    return np.vstack((sensor, arc))


def second_detector_candidate_disks(
        sensor, bearing_deg, error_deg=1.0, max_range=1500.0,
        minimum_receive_radius=1000.0):
    """Return the three discs whose intersection guarantees a second reception.

    For a sector narrower than 180 degrees, the farthest sector point from a fixed
    detector is the apex or one of the two far arc endpoints.  Covering these three
    points by the guaranteed receive radius therefore covers the whole sector.
    """
    sensor = _point(sensor, 'sensor')
    if not math.isfinite(error_deg) or not 0 < error_deg < 90:
        raise ValueError('Bearing half-width must be between 0 and 90 degrees')
    if not math.isfinite(max_range) or max_range <= 0:
        raise ValueError('Maximum range must be positive and finite')
    if not math.isfinite(minimum_receive_radius) or minimum_receive_radius <= 0:
        raise ValueError('Minimum receive radius must be positive and finite')
    lower = sensor + max_range * _unit_vector(bearing_deg - error_deg)
    upper = sensor + max_range * _unit_vector(bearing_deg + error_deg)
    return np.vstack((sensor, lower, upper)), float(minimum_receive_radius)


def second_detector_candidate(point, centers, radius, tolerance=1e-9):
    point = _point(point)
    centers = np.asarray(centers, dtype=float)
    if centers.ndim != 2 or centers.shape[1] != 2 or not len(centers):
        raise ValueError('centers must be a nonempty finite (n,2) array')
    if not np.isfinite(centers).all() or not math.isfinite(radius) or radius <= 0:
        raise ValueError('Finite centers and a positive radius are required')
    return bool(np.max(np.linalg.norm(centers - point, axis=1)) <= radius + tolerance)


def recommended_second_detectors(
        sensor, bearing_deg, error_deg=1.0, max_range=1500.0,
        minimum_receive_radius=1000.0):
    """Return the two symmetric robust second-detection points.

    Each point is the outer intersection of the guaranteed-radius disc about the
    first sensor and the disc about the opposite far-sector endpoint.  This uses
    the largest available transverse baseline while retaining guaranteed reception
    for every source position in the first feasible sector.
    """
    sensor = _point(sensor, 'sensor')
    if max_range > 2 * minimum_receive_radius:
        raise ValueError('The first feasible sector cannot be covered at this radius')
    centers, radius = second_detector_candidate_disks(
        sensor, bearing_deg, error_deg, max_range, minimum_receive_radius)
    half_range = max_range / 2
    height = math.sqrt(max(0.0, radius ** 2 - half_range ** 2))
    eps = math.radians(error_deg)
    along = half_range * math.cos(eps) + height * math.sin(eps)
    transverse = -half_range * math.sin(eps) + height * math.cos(eps)
    forward = _unit_vector(bearing_deg)
    left = np.array([-forward[1], forward[0]])
    points = np.vstack((
        sensor + along * forward + transverse * left,
        sensor + along * forward - transverse * left,
    ))
    if not all(second_detector_candidate(point, centers, radius) for point in points):
        raise ValueError('No symmetric robust recommendation for these parameters')
    return points


def intersection_angle_deg(sensor1, sensor2, source):
    """Return the acute crossing angle between the two bearing lines."""
    sensor1 = _point(sensor1, 'sensor1')
    sensor2 = _point(sensor2, 'sensor2')
    source = _point(source, 'source')
    first = source - sensor1
    second = source - sensor2
    scale = np.linalg.norm(first) * np.linalg.norm(second)
    if scale == 0:
        raise ValueError('Source must differ from both detector positions')
    cosine = abs(float(first @ second)) / scale
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def clip_polygon_halfplanes(points, a, b, tolerance=1e-9):
    """Clip a convex polygon by normalized or unnormalized ``A x <= b`` rows."""
    polygon = _points(points).copy()
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.ndim != 2 or a.shape[1] != 2 or b.shape != (len(a),):
        raise ValueError('A(m,2) and b(m) are required')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Halfplanes must be finite')
    for normal, bound in zip(a, b):
        if np.linalg.norm(normal) == 0:
            if bound < -tolerance:
                return np.empty((0, 2))
            continue
        output = []
        previous = polygon[-1]
        previous_inside = normal @ previous <= bound + tolerance
        for current in polygon:
            current_inside = normal @ current <= bound + tolerance
            if current_inside != previous_inside:
                edge = current - previous
                denominator = normal @ edge
                if abs(denominator) > 1e-15:
                    fraction = (bound - normal @ previous) / denominator
                    output.append(previous + fraction * edge)
            if current_inside:
                output.append(current)
            previous, previous_inside = current, current_inside
        if not output:
            return np.empty((0, 2))
        polygon = np.asarray(output, dtype=float)
    if len(polygon) > 1 and np.linalg.norm(polygon[0] - polygon[-1]) <= tolerance:
        polygon = polygon[:-1]
    return polygon
