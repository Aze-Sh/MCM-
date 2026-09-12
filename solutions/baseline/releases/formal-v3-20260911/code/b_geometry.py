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
