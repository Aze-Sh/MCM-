import importlib.util
import json
import string

import pytest


def analysis():
    assert importlib.util.find_spec('b_paper_analysis'), 'Paper evidence analysis is not implemented'
    import b_paper_analysis
    return b_paper_analysis


def test_paper_evidence_matches_verified_reports():
    report = analysis().build_report()
    q2 = report['q2_sensitivity']
    operating = q2['operating_point']
    assert operating['error_deg'] == pytest.approx(1.0)
    assert operating['max_range_m'] == pytest.approx(1500.0)
    assert operating['guaranteed_max_distance_m'] <= 1000.0 + 1e-8
    assert operating['minimum_crossing_angle_deg'] >= 39.4

    ablation = report['strategy_ablation']
    assert ablation['all_reports_passed'] is True
    assert ablation['paired_inputs_verified'] is True
    assert ablation['q3']['v1_to_v2_virtual_time_reduction_percent'] == pytest.approx(12.70, abs=0.01)
    assert ablation['q4']['v1_to_v2_virtual_time_reduction_percent'] == pytest.approx(9.99, abs=0.01)
    assert ablation['q3']['source16_v2_to_v3_reduction_percent'] == pytest.approx(32.59, abs=0.01)
    assert ablation['q4']['source16_v2_to_v3_reduction_percent'] == pytest.approx(19.60, abs=0.01)

    directional = report['q4_directional_stress']
    assert directional['run_count'] == 50
    assert directional['all_cleared'] is True
    assert sum(item['count'] for item in directional['bins']) == 50


def test_paper_evidence_json_is_stable_and_portable(tmp_path):
    module = analysis()
    first = tmp_path / 'first.json'
    second = tmp_path / 'second.json'
    module.write_report(first)
    module.write_report(second)
    assert first.read_bytes() == second.read_bytes()
    text = first.read_text(encoding='utf-8')
    assert not any(f'{letter}:' + chr(92) in text for letter in string.ascii_letters)
    assert json.loads(text)['metadata']['status'] == 'verified-derived-evidence'
