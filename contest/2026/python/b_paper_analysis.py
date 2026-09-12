"""Deterministic sensitivity and ablation evidence for the B-paper."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import b_geometry as geometry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIN_RECEIVE_RADIUS_M = 1000.0
MIN_DIRECTION_RANGE_M = 5.0001
REPORT_FILES = {
    'v1': 'synthetic-stress-20260911.json',
    'v2': 'synthetic-stress-route-v2-20260911.json',
    'v3': 'synthetic-stress-stop16-v3-20260911.json',
}


def _rounded(value, digits=6):
    return round(float(value), digits)


def _minimum_crossing_angle(error_deg, max_range_m, detector,
                            angle_samples=161, radial_samples=201):
    angles = np.deg2rad(np.linspace(-error_deg, error_deg, angle_samples))
    ranges = np.linspace(MIN_DIRECTION_RANGE_M, max_range_m, radial_samples)
    angle_grid, range_grid = np.meshgrid(angles, ranges, indexing='ij')
    sources = np.stack((
        range_grid * np.cos(angle_grid),
        range_grid * np.sin(angle_grid)), axis=-1)
    first = sources
    second = sources - np.asarray(detector, dtype=float)
    scale = np.linalg.norm(first, axis=-1) * np.linalg.norm(second, axis=-1)
    cosine = np.abs(np.sum(first * second, axis=-1)) / np.maximum(scale, 1e-12)
    return float(np.min(np.degrees(np.arccos(np.clip(cosine, 0.0, 1.0)))))


def _q2_point(error_deg, max_range_m, *, dense=False):
    centers, _ = geometry.second_detector_candidate_disks(
        (0.0, 0.0), 0.0, error_deg, max_range_m, MIN_RECEIVE_RADIUS_M)
    detector = geometry.recommended_second_detectors(
        (0.0, 0.0), 0.0, error_deg, max_range_m,
        MIN_RECEIVE_RADIUS_M)[0]
    samples = (321, 401) if dense else (161, 201)
    return {
        'error_deg': _rounded(error_deg),
        'max_range_m': _rounded(max_range_m),
        'detector_x_m': _rounded(detector[0]),
        'transverse_baseline_m': _rounded(abs(detector[1])),
        'guaranteed_max_distance_m': _rounded(
            np.max(np.linalg.norm(centers - detector, axis=1)), 9),
        'minimum_crossing_angle_deg': _rounded(_minimum_crossing_angle(
            error_deg, max_range_m, detector, *samples)),
    }


def _q2_sensitivity():
    error_values = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0)
    range_values = (1000.0, 1200.0, 1400.0, 1500.0,
                    1600.0, 1800.0, 1900.0, 1950.0)
    return {
        'fixed_guaranteed_receive_radius_m': MIN_RECEIVE_RADIUS_M,
        'operating_point': _q2_point(1.0, 1500.0, dense=True),
        'error_sweep_at_1500_m': [
            _q2_point(error_deg, 1500.0) for error_deg in error_values],
        'range_sweep_at_1_deg': [
            _q2_point(1.0, max_range_m) for max_range_m in range_values],
        'failure_boundary': (
            'A single guaranteed second detector may not exist when '
            'max_range_m exceeds twice the guaranteed receive radius.'),
    }


def _load_reports(output_dir):
    reports = {}
    for version, name in REPORT_FILES.items():
        reports[version] = json.loads(
            (output_dir / name).read_text(encoding='utf-8'))
    return reports


def _mean(runs, key):
    return float(np.mean([run[key] for run in runs]))


def _case_signatures(runs):
    signatures = {}
    for run in runs:
        seed = run['seed']
        if seed in signatures:
            raise ValueError(f'Duplicate synthetic seed: {seed}')
        signatures[seed] = (
            run['source_count'],
            json.dumps(run['synthetic_truth'], sort_keys=True, separators=(',', ':')),
        )
    return signatures


def _verify_paired_inputs(reports):
    for problem in (3, 4):
        reference = _case_signatures(
            [run for run in reports['v1']['runs'] if run['problem'] == problem])
        for version in ('v2', 'v3'):
            candidate = _case_signatures(
                [run for run in reports[version]['runs'] if run['problem'] == problem])
            if candidate != reference:
                raise ValueError(
                    f'Problem {problem} inputs differ between v1 and {version}')
    return True


def _strategy_ablation(reports):
    result = {
        'report_files': REPORT_FILES,
        'all_reports_passed': all(report['all_passed'] for report in reports.values()),
        'paired_inputs_verified': _verify_paired_inputs(reports),
    }
    for problem in (3, 4):
        by_version = {
            version: [run for run in report['runs'] if run['problem'] == problem]
            for version, report in reports.items()
        }
        summaries = {}
        for version, runs in by_version.items():
            summaries[version] = {
                'run_count': len(runs),
                'all_cleared': all(run['clear_fraction'] == 1 for run in runs),
                'mean_virtual_time_s': _rounded(_mean(runs, 'virtual_time_s')),
                'mean_moving_distance_m': _rounded(_mean(runs, 'moving_distance_m')),
                'virtual_time_standard_deviation_s': _rounded(
                    np.std([run['virtual_time_s'] for run in runs], ddof=1)),
            }
        mean_v1 = summaries['v1']['mean_virtual_time_s']
        mean_v2 = summaries['v2']['mean_virtual_time_s']
        v2_source16 = [run for run in by_version['v2'] if run['source_count'] == 16]
        v3_source16 = [run for run in by_version['v3'] if run['source_count'] == 16]
        mean_v2_16 = _mean(v2_source16, 'virtual_time_s')
        mean_v3_16 = _mean(v3_source16, 'virtual_time_s')
        result[f'q{problem}'] = {
            'versions': summaries,
            'v1_to_v2_virtual_time_reduction_percent': _rounded(
                100.0 * (mean_v1 - mean_v2) / mean_v1),
            'v1_to_v2_moving_distance_reduction_percent': _rounded(
                100.0 * (
                    summaries['v1']['mean_moving_distance_m']
                    - summaries['v2']['mean_moving_distance_m'])
                / summaries['v1']['mean_moving_distance_m']),
            'source16_case_count': len(v2_source16),
            'source16_v2_mean_virtual_time_s': _rounded(mean_v2_16),
            'source16_v3_mean_virtual_time_s': _rounded(mean_v3_16),
            'source16_v2_to_v3_reduction_percent': _rounded(
                100.0 * (mean_v2_16 - mean_v3_16) / mean_v2_16),
        }
    return result


def _q4_directional_stress(reports):
    runs = [run for run in reports['v3']['runs'] if run['problem'] == 4]
    rows = []
    for run in runs:
        directional_count = sum(
            source.get('direction') is not None for source in run['synthetic_truth'])
        rows.append({
            'seed': run['seed'],
            'source_count': run['source_count'],
            'directional_count': directional_count,
            'directional_fraction': _rounded(directional_count / run['source_count']),
            'virtual_time_s': _rounded(run['virtual_time_s']),
            'clear_fraction': _rounded(run['clear_fraction']),
        })
    definitions = (
        ('less_than_0.5', lambda value: value < 0.5),
        ('0.5_to_less_than_0.7', lambda value: 0.5 <= value < 0.7),
        ('at_least_0.7', lambda value: value >= 0.7),
    )
    bins = []
    for label, predicate in definitions:
        selected = [row for row in rows if predicate(row['directional_fraction'])]
        bins.append({
            'label': label,
            'count': len(selected),
            'mean_virtual_time_s': (
                _rounded(np.mean([row['virtual_time_s'] for row in selected]))
                if selected else None),
            'all_cleared': all(row['clear_fraction'] == 1 for row in selected),
        })
    return {
        'run_count': len(rows),
        'all_cleared': all(row['clear_fraction'] == 1 for row in rows),
        'minimum_directional_fraction': min(row['directional_fraction'] for row in rows),
        'maximum_directional_fraction': max(row['directional_fraction'] for row in rows),
        'bins': bins,
        'runs': rows,
    }


def build_report(output_dir=None):
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / 'output'
    reports = _load_reports(output_dir)
    return {
        'metadata': {
            'problem': '2026 CUMCM B',
            'status': 'verified-derived-evidence',
            'script': 'python/b_paper_analysis.py',
            'inputs': [f'output/{name}' for name in REPORT_FILES.values()],
            'note': 'Synthetic evidence only; not an official-score distribution.',
        },
        'q2_sensitivity': _q2_sensitivity(),
        'strategy_ablation': _strategy_ablation(reports),
        'q4_directional_stress': _q4_directional_stress(reports),
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
        default=PROJECT_ROOT / 'output' / 'paper-evidence-20260912.json')
    args = parser.parse_args()
    write_report(args.output)
    print(args.output)


if __name__ == '__main__':
    main()
