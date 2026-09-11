import importlib.util
import json
import math

import numpy as np
import pytest


def analysis():
    assert importlib.util.find_spec('q1_q2_analysis'), 'Q1/Q2 analysis is not implemented'
    import q1_q2_analysis
    return q1_q2_analysis


def test_report_contains_reproducible_q1_q2_evidence():
    report = analysis().build_report()
    assert report['q1']['region_status'] == 'bounded'
    assert report['q1']['diameter_m'] == pytest.approx(40.0)
    assert report['q1']['minimum_enclosing_radius_m'] == pytest.approx(
        40 / math.sqrt(3))
    assert report['q1']['diameter_circle_covers_region'] is False
    assert report['q2']['guaranteed_max_distance_m'] <= 1000 + 1e-8
    assert report['q2']['sampled_min_crossing_angle_deg'] >= 39.5
    assert report['q2']['collinear_baseline_min_crossing_angle_deg'] == pytest.approx(0)


def test_report_is_rotation_invariant():
    module = analysis()
    baseline = module.build_report(sensor=(0, 0), bearing_deg=0)
    rotated = module.build_report(sensor=(20, -10), bearing_deg=90)
    assert rotated['q2']['guaranteed_max_distance_m'] == pytest.approx(
        baseline['q2']['guaranteed_max_distance_m'])
    assert rotated['q2']['sampled_min_crossing_angle_deg'] == pytest.approx(
        baseline['q2']['sampled_min_crossing_angle_deg'])


def test_resolution_convergence_and_stable_json(tmp_path):
    module = analysis()
    report = module.build_report()
    convergence = report['q2']['resolution_convergence']
    assert convergence['final_change_deg'] < 0.05

    first = tmp_path / 'first.json'
    second = tmp_path / 'second.json'
    module.write_report(first, report)
    module.write_report(second, module.build_report())
    assert first.read_bytes() == second.read_bytes()
    parsed = json.loads(first.read_text(encoding='utf-8'))
    assert parsed['metadata']['script'] == 'python/q1_q2_analysis.py'
    windows_drive_prefix = 'C:' + chr(92)
    assert windows_drive_prefix not in first.read_text(encoding='utf-8')
