import json
from pathlib import Path
import subprocess
import sys

ENTRY = Path(__file__).resolve().parents[1] / 'python/main.py'


def test_synthetic_batch_writes_results_without_official_access(tmp_path):
    report = tmp_path/'simulation.json'
    process = subprocess.run([sys.executable,'-X','utf8',str(ENTRY),'simulate','--cases','1','--output',str(report)],capture_output=True,text=True,encoding='utf-8')
    assert process.returncode == 0, process.stderr
    assert report.exists(), 'Simulation runner did not produce its report'
    data=json.loads(report.read_text())
    assert data['kind']=='synthetic-not-official'
    assert data['strategy']=='coverage600-nearest-resume-adaptive8-grid20-stop16-v3'
    assert len(data['runs'])==2
    assert {r['problem'] for r in data['runs']}=={3,4}
    assert all(r['clear_fraction']==1 for r in data['runs'])


def test_practice_requires_explicit_mode_confirmation():
    process=subprocess.run([sys.executable,'-X','utf8',str(ENTRY),'practice','--robot-id','test-team'],capture_output=True,text=True,encoding='utf-8')
    assert process.returncode != 0
    assert '--confirm-practice' in process.stderr


def test_formal_requires_explicit_confirmation_and_run_number(tmp_path):
    missing_confirmation = subprocess.run(
        [sys.executable, '-X', 'utf8', str(ENTRY), 'formal', '--robot-id', 'test-team',
         '--problem', '3', '--formal-run', '1'],
        capture_output=True, text=True, encoding='utf-8')
    assert missing_confirmation.returncode != 0
    assert '--confirm-formal' in missing_confirmation.stderr

    missing_run = subprocess.run(
        [sys.executable, '-X', 'utf8', str(ENTRY), 'formal', '--robot-id', 'test-team',
         '--problem', '3', '--confirm-formal'],
        capture_output=True, text=True, encoding='utf-8')
    assert missing_run.returncode != 0
    assert '--formal-run' in missing_run.stderr

    missing_problem = subprocess.run(
        [sys.executable, '-X', 'utf8', str(ENTRY), 'formal', '--robot-id', 'test-team',
         '--formal-run', '1', '--confirm-formal', '--url', 'http://127.0.0.1:1',
         '--output', str(tmp_path / 'must-not-run.json')],
        capture_output=True, text=True, encoding='utf-8')
    assert missing_problem.returncode != 0
    assert '--problem' in missing_problem.stderr
