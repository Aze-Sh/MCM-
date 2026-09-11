import importlib.util
import math

import numpy as np
import pytest


def geometry():
    assert importlib.util.find_spec('b_geometry'), 'B geometry module is not implemented'
    import b_geometry
    return b_geometry


def test_triangle_diameter_is_not_a_safe_clearance_circle():
    g = geometry()
    vertices = np.array([[0., 0.], [40., 0.], [20., 20 * math.sqrt(3)]])
    # Three forward 2-degree wedges whose lower boundaries support the triangle.
    observations = []
    for vertex, angle in zip(vertices, [0, 120, 240]):
        u = np.array([math.cos(math.radians(angle)), math.sin(math.radians(angle))])
        observations.append((*(vertex - 1000 * u), angle + 1))
    region = g.bearing_region(observations)
    assert region.status == 'bounded'
    assert g.diameter(region.vertices) == pytest.approx(40)
    center, radius = g.enclosing_circle(region.vertices)
    assert center == pytest.approx([20, 20 / math.sqrt(3)])
    assert radius == pytest.approx(40 / math.sqrt(3))
    assert radius > 20


def test_unbounded_empty_and_degenerate_regions():
    g = geometry()
    assert g.bearing_region([(0, 0, 0)]).status == 'unbounded'
    assert g.bearing_region([(0, 0, 180), (10, 0, 0)]).status == 'empty'
    r = g.halfplane_region([[1, 0], [-1, 0], [0, 1], [0, -1]], [1, -1, 2, -2])
    assert r.status == 'bounded'
    assert g.diameter(r.vertices) == pytest.approx(0)
    assert g.enclosing_circle(r.vertices)[1] == pytest.approx(0)


def test_zero_wrap_and_true_position_containment():
    g = geometry()
    truth = np.array([900., 1.])
    observations = []
    for (x, y), error in zip([(0, 0), (0, 500), (400, -200)], [-1, 1, .35]):
        angle = math.degrees(math.atan2(truth[1] - y, truth[0] - x))
        observations.append((x, y, (angle + error) % 360))
    a, b = g.bearing_halfplanes(observations)
    assert np.max(a @ truth - b) <= 1e-7
    r = g.bearing_region(observations)
    c, rad = g.enclosing_circle(r.vertices)
    assert np.linalg.norm(c - truth) <= rad + 1e-6


def test_line_segment_circle_and_rectangle_diameter():
    g = geometry()
    assert g.diameter([[0, 0], [3, 0], [3, 4], [0, 4]]) == 5
    c, r = g.enclosing_circle([[0, 0], [2, 0], [4, 0]])
    assert c == pytest.approx([2, 0])
    assert r == 2


@pytest.mark.parametrize('obs', [[(0, 0, float('nan'))], [(0, float('inf'), 10)]])
def test_invalid_geometry_rejected(obs):
    with pytest.raises(ValueError):
        geometry().bearing_region(obs)


def test_second_detector_design_guarantees_minimum_receive_radius():
    g = geometry()
    points = g.recommended_second_detectors((0, 0), 0)
    assert points.shape == (2, 2)
    assert points[0] == pytest.approx([761.429453, 648.247783], abs=1e-6)
    assert points[1] == pytest.approx([761.429453, -648.247783], abs=1e-6)

    centers, radius = g.second_detector_candidate_disks((0, 0), 0)
    for point in points:
        assert g.second_detector_candidate(point, centers, radius)
        sector = g.first_bearing_sector((0, 0), 0, arc_samples=721)
        assert np.max(np.linalg.norm(sector - point, axis=1)) <= radius + 1e-9


def test_second_detector_design_is_rigid_motion_invariant():
    g = geometry()
    base = g.recommended_second_detectors((0, 0), 0)
    rotated = g.recommended_second_detectors((10, -20), 90)
    rotation = np.array([[0., -1.], [1., 0.]])
    assert rotated == pytest.approx(base @ rotation.T + [10, -20])


def test_recommended_detector_has_robust_crossing_angle():
    g = geometry()
    detector = g.recommended_second_detectors((0, 0), 0)[0]
    angles = np.linspace(-1, 1, 41)
    ranges = np.linspace(5.0001, 1500, 201)
    crossing_angles = []
    for angle in angles:
        direction = np.array([
            math.cos(math.radians(angle)), math.sin(math.radians(angle))])
        for distance in ranges:
            source = distance * direction
            crossing_angles.append(g.intersection_angle_deg(
                (0, 0), detector, source))
    assert min(crossing_angles) >= 39.5


def test_convex_polygon_can_be_clipped_by_halfplanes():
    g = geometry()
    square = np.array([[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]])
    clipped = g.clip_polygon_halfplanes(
        square, [[1, 0], [0, 1]], [0.5, 0.25])
    assert len(clipped) == 4
    assert np.max(clipped[:, 0]) == pytest.approx(0.5)
    assert np.max(clipped[:, 1]) == pytest.approx(0.25)
    assert g.diameter(clipped) == pytest.approx(math.hypot(1.5, 1.25))


def test_second_detector_rejects_uncoverable_sector():
    with pytest.raises(ValueError, match='cannot be covered'):
        geometry().recommended_second_detectors(
            (0, 0), 0, max_range=2100, minimum_receive_radius=1000)
