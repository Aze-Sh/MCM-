"""Deterministic evidence builder for CUMCM 2026 problem B, questions 1 and 2."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import b_geometry as geometry


ERROR_DEG = 1.0
MAX_RANGE_M = 1500.0
MIN_RECEIVE_RADIUS_M = 1000.0
MIN_DIRECTION_RANGE_M = 5.0001


def _rounded(value, digits=9):
    return round(float(value), digits)


def _q1_counterexample():
    target_vertices = np.array([
        [0.0, 0.0],
        [40.0, 0.0],
        [20.0, 20.0 * math.sqrt(3.0)],
    ])
    boundary_angles = [0.0, 120.0, 240.0]
    observations = []
    for vertex, angle in zip(target_vertices, boundary_angles):
        unit = np.array([
            math.cos(math.radians(angle)), math.sin(math.radians(angle))])
        sensor = vertex - 1000.0 * unit
        observations.append([*sensor, angle + ERROR_DEG])
    region = geometry.bearing_region(observations, ERROR_DEG)
    if region.status != 'bounded':
        raise ArithmeticError('Constructed counterexample must be bounded')
    center, radius = geometry.enclosing_circle(region.vertices)
    diameter = geometry.diameter(region.vertices)
    return {
        'observations_x_y_bearing_deg': [
            [_rounded(value) for value in row] for row in observations],
        'region_status': region.status,
        'vertices_m': [
            [_rounded(value) for value in row] for row in region.vertices],
        'diameter_m': _rounded(diameter),
        'diameter_circle_radius_m': _rounded(diameter / 2.0),
        'minimum_enclosing_center_m': [_rounded(value) for value in center],
        'minimum_enclosing_radius_m': _rounded(radius),
        'minimum_radius_over_diameter': _rounded(radius / diameter),
        'diameter_circle_covers_region': bool(radius <= diameter / 2.0 + 1e-9),
        'conclusion': (
            'A circle whose diameter equals the region diameter is not guaranteed '
            'to cover the region; this feasible region is an equilateral triangle.'),
    }


def _sample_crossing_metrics(
        sensor, bearing_deg, detector, angle_samples, radial_samples):
    sensor = np.asarray(sensor, dtype=float)
    detector = np.asarray(detector, dtype=float)
    angles = np.deg2rad(np.linspace(
        bearing_deg - ERROR_DEG, bearing_deg + ERROR_DEG, angle_samples))
    ranges = np.linspace(MIN_DIRECTION_RANGE_M, MAX_RANGE_M, radial_samples)
    angle_grid, range_grid = np.meshgrid(angles, ranges, indexing='ij')
    sources = sensor + np.stack((
        range_grid * np.cos(angle_grid),
        range_grid * np.sin(angle_grid)), axis=-1)
    first = sources - sensor
    second = sources - detector
    denominator = np.linalg.norm(first, axis=-1) * np.linalg.norm(second, axis=-1)
    valid = denominator > 1e-12
    cosine = np.full(denominator.shape, np.nan)
    cosine[valid] = np.abs(np.sum(first[valid] * second[valid], axis=-1)) / denominator[valid]
    crossing = np.degrees(np.arccos(np.clip(cosine, 0.0, 1.0)))
    flat_index = int(np.nanargmin(crossing))
    index = np.unravel_index(flat_index, crossing.shape)
    distances = np.linalg.norm(second, axis=-1)
    return {
        'minimum_crossing_angle_deg': _rounded(crossing[index]),
        'worst_source_range_m': _rounded(range_grid[index], 6),
        'worst_source_bearing_deg': _rounded(math.degrees(angle_grid[index]), 6),
        'sampled_max_distance_m': _rounded(np.max(distances)),
        'angle_samples': int(angle_samples),
        'radial_samples': int(radial_samples),
    }


def _q2_design(sensor, bearing_deg):
    sensor = np.asarray(sensor, dtype=float)
    centers, radius = geometry.second_detector_candidate_disks(
        sensor, bearing_deg, ERROR_DEG, MAX_RANGE_M, MIN_RECEIVE_RADIUS_M)
    recommended = geometry.recommended_second_detectors(
        sensor, bearing_deg, ERROR_DEG, MAX_RANGE_M, MIN_RECEIVE_RADIUS_M)
    selected = recommended[0]
    exact_max_distance = float(np.max(np.linalg.norm(centers - selected, axis=1)))

    central = np.array([
        math.cos(math.radians(bearing_deg)),
        math.sin(math.radians(bearing_deg))])
    perpendicular = np.array([-central[1], central[0]])
    collinear = sensor + (MAX_RANGE_M / 2.0) * central
    perpendicular_only = sensor + MIN_RECEIVE_RADIUS_M * perpendicular

    final_metrics = _sample_crossing_metrics(
        sensor, bearing_deg, selected, 321, 401)
    collinear_metrics = _sample_crossing_metrics(
        sensor, bearing_deg, collinear, 321, 401)
    angular_convergence = [
        _sample_crossing_metrics(sensor, bearing_deg, selected, count, 401)
        for count in (41, 81, 161, 321)
    ]
    radial_convergence = [
        _sample_crossing_metrics(sensor, bearing_deg, selected, 321, count)
        for count in (101, 201, 401)
    ]
    changes = [
        abs(angular_convergence[-1]['minimum_crossing_angle_deg']
            - angular_convergence[-2]['minimum_crossing_angle_deg']),
        abs(radial_convergence[-1]['minimum_crossing_angle_deg']
            - radial_convergence[-2]['minimum_crossing_angle_deg']),
    ]
    return {
        'first_sensor_m': [_rounded(value) for value in sensor],
        'measured_bearing_deg': _rounded(bearing_deg),
        'bearing_half_error_deg': ERROR_DEG,
        'maximum_possible_receive_range_m': MAX_RANGE_M,
        'guaranteed_receive_radius_m': MIN_RECEIVE_RADIUS_M,
        'candidate_region': (
            'intersection of three 1000 m discs centered at the first sensor '
            'and the two endpoints of the 1500 m bearing-sector arc'),
        'candidate_disc_centers_m': [
            [_rounded(value) for value in row] for row in centers],
        'recommended_detectors_m': [
            [_rounded(value) for value in row] for row in recommended],
        'selected_detector_m': [_rounded(value) for value in selected],
        'movement_distance_m': _rounded(np.linalg.norm(selected - sensor)),
        'movement_time_s_at_5_mps': _rounded(np.linalg.norm(selected - sensor) / 5.0),
        'guaranteed_max_distance_m': _rounded(exact_max_distance),
        'sampled_min_crossing_angle_deg': final_metrics['minimum_crossing_angle_deg'],
        'worst_sampled_source': {
            'range_m': final_metrics['worst_source_range_m'],
            'bearing_deg': final_metrics['worst_source_bearing_deg'],
        },
        'collinear_baseline_detector_m': [_rounded(value) for value in collinear],
        'collinear_baseline_min_crossing_angle_deg': (
            collinear_metrics['minimum_crossing_angle_deg']),
        'perpendicular_only_detector_m': [
            _rounded(value) for value in perpendicular_only],
        'perpendicular_only_max_distance_m': _rounded(
            np.max(np.linalg.norm(centers - perpendicular_only, axis=1))),
        'resolution_convergence': {
            'angular': angular_convergence,
            'radial': radial_convergence,
            'final_change_deg': _rounded(max(changes)),
        },
    }


def build_report(sensor=(0.0, 0.0), bearing_deg=0.0):
    return {
        'metadata': {
            'problem': '2026 CUMCM B',
            'questions': [1, 2],
            'script': 'python/q1_q2_analysis.py',
            'status': 'verified-analytic-and-numeric',
            'coordinate_convention': 'east-positive x, north-positive y, degrees CCW from east',
        },
        'q1': _q1_counterexample(),
        'q2': _q2_design(sensor, bearing_deg),
    }


def write_report(path, report=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        build_report() if report is None else report,
        ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    path.write_text(payload, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output', type=Path,
        default=Path(__file__).resolve().parents[1] / 'output' /
        'q1-q2-geometry-20260911.json')
    args = parser.parse_args()
    write_report(args.output)
    print(args.output)


if __name__ == '__main__':
    main()
