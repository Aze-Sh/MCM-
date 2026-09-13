"""Reproduce the historical v7 comparison using synthetic inputs only."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import json
import math
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'validation/baseline_v7')]
from benchmark import case_from_record, offline_io
from simulator import SyntheticSimulator
from adaptive_v7 import SolverV7


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', help='Run one named case; default: all 20 cases')
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/baseline_check')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    reference = json.loads((ROOT / 'validation/performance-comparison.json').read_text(encoding='utf-8'))
    inputs = {r['name']: r for r in json.loads((ROOT / 'validation/expected-fast.json').read_text(encoding='utf-8'))['cases']}
    rows = [r for r in reference['cases'] if not args.case or r['name'] == args.case]
    if not rows:
        parser.error('Unknown case')
    checked = []
    for row in rows:
        case = case_from_record(inputs[row['name']])
        world = SyntheticSimulator(case['sources'], error_seed=case['seed'])
        io = offline_io(world.transport)
        io['wall_deadline'] = time.monotonic() + 180
        adapter = SimpleNamespace(call=io['call'], record=io['record'], pending=None, deadline=math.inf)
        start = time.monotonic()
        solver = SolverV7(adapter, case['problem'])
        solver.run()
        total = world.virtual_time
        matches = abs(total - row['v7_s']) < 1e-6 and len(world.cleared) == len(case['sources'])
        result = dict(name=row['name'], source_count=len(case['sources']), cleared_count=len(world.cleared),
                      virtual_time_s=total, expected_time_s=row['v7_s'], matches=matches,
                      wall_s=time.monotonic()-start, scope='offline synthetic comparison only')
        logfile = args.output / ('v7-' + row['name'] + '.jsonl')
        logfile.write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in io['events']), encoding='utf-8')
        result['log_sha256'] = hashlib.sha256(logfile.read_bytes()).hexdigest()
        logfile.with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        checked.append(result)
        print(json.dumps(result), flush=True)
        if not matches:
            raise RuntimeError('Comparison differs from the frozen result')
    (args.output / 'verification.json').write_text(json.dumps(dict(cases=checked, verified=len(checked)), indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
