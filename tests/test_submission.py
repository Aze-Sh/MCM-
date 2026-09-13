import csv
import json
from pathlib import Path
import tempfile
import unittest

import prepare_submission as package


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        inputs = self.root / 'submission_inputs'
        inputs.mkdir()
        for directory in ('q2_comparison', 'sensitivity', 'ablation', 'practice_details'):
            (inputs / directory).mkdir()
        (inputs / 'human_review.json').write_text('{}', encoding='utf-8')
        self.columns = ('problem', 'test', 'case_code', 'cleared_count', 'virtual_time_s',
                        'average_time_s', 'real_time_s', 'log_filename', 'upload_confirmed')
        self.rows = []
        for q in (3, 4):
            for i in (1, 2, 3):
                (inputs / f'formal/q{q}/test_{i}').mkdir(parents=True)
                self.rows.append(dict.fromkeys(self.columns, '') | dict(problem=str(q), test=str(i)))
        self.save()

    def save(self):
        with (self.root / 'submission_inputs/formal_results.csv').open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, self.columns)
            writer.writeheader()
            writer.writerows(self.rows)

    def fixture_log(self, package_type, index=1):
        # A metadata-only fixture, deliberately not an authentic signed log.
        path = self.root / 'submission_inputs/formal/q3/test_1/fixture.jlog'
        meta = dict(package_type=package_type, problem_no=3, formal_index=index, case_code='TEST-CASE')
        payload = b'JMBPLOG1' + bytes(6) + json.dumps(meta).encode() + bytes(32)
        path.write_bytes(payload)
        self.rows[0].update(case_code='TEST-CASE', log_filename=path.name,
                            cleared_count='10', virtual_time_s='3000',
                            average_time_s='300', real_time_s='30', upload_confirmed='true')
        self.save()
        return path, payload

    def test_empty_slots_remain_missing_and_no_logs_are_created(self):
        pending, errors, logs = package.check_inputs(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(logs, [])
        self.assertEqual(sum('缺少原始正式日志' in item for item in pending), 6)
        self.assertFalse(list(self.root.rglob('*.jlog')))

    def test_practice_log_cannot_fill_a_formal_slot(self):
        path, original = self.fixture_log('practice_behavior_log')
        _, errors, logs = package.check_inputs(self.root)
        self.assertTrue(any('演练日志不能代替' in e for e in errors))
        self.assertEqual(logs, [])
        self.assertEqual(path.read_bytes(), original)

    def test_matching_envelope_is_preserved_without_claiming_signature_validation(self):
        path, original = self.fixture_log('formal_behavior_log')
        _, errors, logs = package.check_inputs(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(logs, [path])
        self.assertEqual(path.read_bytes(), original)

    def test_wrong_formal_index_is_rejected(self):
        self.fixture_log('formal_behavior_log', index=2)
        _, errors, logs = package.check_inputs(self.root)
        self.assertTrue(any('正式次数' in e for e in errors))
        self.assertEqual(logs, [])

    def test_invalid_average_is_not_accepted(self):
        self.fixture_log('formal_behavior_log')
        self.rows[0]['average_time_s'] = '100'
        self.save()
        _, errors, _ = package.check_inputs(self.root)
        self.assertTrue(any('平均时间' in e for e in errors))

    def test_identical_inputs_produce_identical_archive_bytes(self):
        left, right = self.root / 'a.zip', self.root / 'b.zip'
        package.write_zip(left, {'b.txt': b'2', 'a.txt': b'1'})
        package.write_zip(right, {'a.txt': b'1', 'b.txt': b'2'})
        self.assertEqual(left.read_bytes(), right.read_bytes())

    def test_identity_patterns_are_reported_without_exposing_values(self):
        path = self.root / 'metadata.json'
        identity = '123456' + '654321'
        path.write_text(json.dumps({'robot_id': identity}), encoding='utf-8')
        report = package.check_anonymity([path])
        self.assertEqual(report, ['metadata.json'])
        self.assertNotIn(identity, str(report))


if __name__ == '__main__':
    unittest.main()
