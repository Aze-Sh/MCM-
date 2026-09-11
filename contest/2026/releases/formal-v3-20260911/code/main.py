"""B entry: default synthetic tests; official practice requires explicit selection."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import uuid

from b_client import RobotClient, UncertainAction
from b_geometry import bearing_region, diameter, enclosing_circle
from b_simulation import SyntheticSimulator, random_case
from b_strategy import STRATEGY_ID, search

ROOT = Path(__file__).resolve().parents[1]


def write_report(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,ensure_ascii=False,indent=2,allow_nan=False)


def simulate(cases, seed, output):
    runs=[]
    for problem in (3,4):
        for case in range(cases):
            case_seed=seed+case
            sources=random_case(case_seed,mixed=problem==4)
            world=SyntheticSimulator(sources,error_seed=case_seed)
            client=RobotClient('synthetic',transport=world.transport)
            started=time.perf_counter()
            client.enter()
            try:
                summary=search(client)
                client.exit()
                summary['error']=None
            except Exception as exc:
                summary=dict(error=f'{type(exc).__name__}: {exc}',coverage_complete=False,
                             all_detected_cleared=False,virtual_time_s=client.virtual_time)
            summary.update(problem=problem,seed=case_seed,source_count=len(sources),
                           cleared_count=len(world.cleared),clear_fraction=len(world.cleared)/len(sources),
                           program_runtime_s=time.perf_counter()-started,
                           average_clear_time_s=client.virtual_time/len(world.cleared) if world.cleared else None,
                           counts=world.counts,moving_distance_m=world.distance,
                           synthetic_truth=[asdict(s) for s in sources])
            runs.append(summary)
            print(f'Q{problem} seed={case_seed}: {len(world.cleared)}/{len(sources)}, virtual={client.virtual_time:.1f}s, real={summary["program_runtime_s"]:.2f}s',flush=True)
    result=dict(kind='synthetic-not-official',created_utc=datetime.now(timezone.utc).isoformat(),
                strategy=STRATEGY_ID,
                assumptions='Uniform-area disk positions, uniform radii, random channels, 60% directional probability in Q4; coordinate-hashed fixed bounded error. Not official distributions.',
                all_passed=all(r['clear_fraction']==1 and r['completion_certified'] and not r['error'] for r in runs),runs=runs)
    write_report(output,result)
    print(f'Report: {output}')
    return 0 if result['all_passed'] else 1


def live_run(args, output, run_id):
    label = (f'formal-q{args.problem}-run{args.formal_run}'
             if args.mode == 'formal' else 'practice')
    log=ROOT/'logs'/f'{label}-{run_id}.jsonl'
    client=RobotClient(args.robot_id,base_url=args.url,log_path=log)
    summary=dict(kind=f'{args.mode}-user-confirmed',problem=args.problem,
                 formal_run=args.formal_run if args.mode == 'formal' else None,
                 strategy=STRATEGY_ID,
                 clear_fraction=None,source_count=None,official_case_code=None,
                 note='Case code and true total must be transcribed from official practice UI; API does not expose source total.',
                 action_log=str(log.relative_to(ROOT)))
    started=time.perf_counter()
    code=0
    try:
        client.enter()
        print(f'Entered {args.mode}; running coverage baseline.',flush=True)
        summary.update(search(client))
        client.exit()
    except UncertainAction as exc:
        summary['error']=str(exc)
        summary['outcome_uncertain']=True
        code=2
    except Exception as exc:
        summary['error']=f'{type(exc).__name__}: {exc}'
        code=2
    summary.update(program_runtime_s=time.perf_counter()-started,
                   cleared_count=len(client.cleared),virtual_time_s=client.virtual_time)
    write_report(output,summary)
    print(f'Report: {output}',flush=True)
    return code


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',nargs='?',default='simulate',choices=['simulate','practice','formal'])
    parser.add_argument('--cases',type=int,default=3)
    parser.add_argument('--seed',type=int,default=20260911)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--robot-id',default=os.environ.get('CUMCM_ROBOT_ID'))
    parser.add_argument('--url',default='http://127.0.0.1:2026')
    parser.add_argument('--problem',type=int,choices=[3,4])
    parser.add_argument('--confirm-practice',action='store_true',help='Confirm official UI is in PRACTICE, not formal mode')
    parser.add_argument('--confirm-formal',action='store_true',help='Confirm official UI is in the intended FORMAL test')
    parser.add_argument('--formal-run',type=int,choices=[1,2,3],help='Formal attempt number for this problem')
    args=parser.parse_args()
    if args.mode=='practice' and not args.confirm_practice:
        parser.error('Select a practice module in the simulator and supply --confirm-practice')
    if args.mode=='formal' and not args.confirm_formal:
        parser.error('Select the intended formal module in the simulator and supply --confirm-formal')
    if args.mode=='formal' and args.formal_run is None:
        parser.error('--formal-run 1, 2, or 3 is required for formal mode')
    if args.mode in {'practice','formal'} and args.problem is None:
        parser.error('--problem 3 or 4 is required for live simulator modes')
    if args.mode in {'practice','formal'} and not args.robot_id:
        parser.error('--robot-id or CUMCM_ROBOT_ID required')
    if args.cases<1:
        parser.error('--cases must be positive')
    run_id=datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    output=args.output or ROOT/'output'/f'{args.mode}-{run_id}.json'
    if output.exists():
        parser.error(f'Report already exists; choose a new output path: {output}')
    return simulate(args.cases,args.seed,output) if args.mode=='simulate' else live_run(args,output,run_id)


if __name__ == "__main__":
    raise SystemExit(main())
