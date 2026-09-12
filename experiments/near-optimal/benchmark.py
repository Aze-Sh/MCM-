"""Portable offline comparisons. Does not connect to the official simulator."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import signal
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'solutions/adaptive/python'),str(ROOT/'solutions/baseline/python')]
from b_simulation import SyntheticSimulator, Source, random_case
from near_optimal.solver import SolverV8
from near_optimal.replay import replay
from near_optimal.finite_policy import calibrate


class OfflineIO:
    """Only a protocol callback crosses into the policy, never source objects."""
    def __init__(self, send):
        self._send = send;self.pending = None;self.deadline = math.inf
        self.serial = 0;self.events = [];self.counts = Counter()
        self.wall_deadline = math.inf

    def check_wall_time(self):
        if time.monotonic() >= self.wall_deadline:
            raise TimeoutError('Offline wall time limit exceeded')

    def call(self,path,point=None,channel=None):
        self.check_wall_time()
        self.serial += 1
        request = dict(arena_id='default',robot_id='offline-v8',request_id=f'offline-{self.serial}')
        if point is not None:
            request.update(position=dict(x=float(point[0]),y=float(point[1])),channel=channel)
        status,reply = self._send(path,json.dumps(request).encode())
        self.events.append(dict(event='offline_response',path=path,request=request,reply=reply,status=status))
        if status!=200:
            raise RuntimeError(f'Offline HTTP status {status}')
        return reply

    def record(self,event):
        self.check_wall_time()
        self.counts[event['event']] += 1;self.events.append(event)


class ExtremeSimulator(SyntheticSimulator):
    def _detect(self,source,pos):
        reply = super()._detect(source,pos)
        if reply['measure_result']=='direction':
            angle = math.degrees(math.atan2(source.position[1]-pos[1],source.position[0]-pos[0]))
            token = f'{source.channel}:{pos[0]!r}:{pos[1]!r}'.encode()
            error = 1 if hashlib.sha256(token).digest()[0]%2 else -1
            reply['svd_deg'] = round((angle+error)%360,2)%360
        return reply


def cases(suite):
    if suite=='matched':
        saved = json.loads((ROOT/'experiments/optimality-bounds/cases.json').read_text())
        return [dict(name=f'q{c["problem"]}-seed{c["seed"]}',problem=c['problem'],seed=c['seed'],
                     sources=[Source(s['channel'],tuple(s['position']),s['radius'],s['direction']) for s in c['source_truth']],
                     saved_v7_s=c['virtual_time_s'],extreme=False) for c in saved['cases']]
    if suite=='stress':
        result = []
        for problem in (3,4):
            for n in (10,16):
                for geometry in ('boundary','cluster'):
                    sources = []
                    for i in range(n):
                        angle = 360*i/n + .013
                        r = 1799.99 if geometry=='boundary' else 8+i*1.3
                        p = (r*math.cos(math.radians(angle)),r*math.sin(math.radians(angle)))
                        sources.append(Source(i+1,p,1000.,angle if problem==4 else None))
                    result.append(dict(name=f'q{problem}-{geometry}-n{n}',problem=problem,seed=n,
                                       sources=sources,extreme=True))
        return result
    if suite=='fallback':
        return [dict(name=f'q{p}-fallback-n{n}',problem=p,seed=n,
                     sources=[Source(i+1,((i-5)*35.,(i%3-1)*25.),1000.,(i*37)%360 if p==4 else None)
                              for i in range(n)],extreme=True) for p,n in ((3,10),(4,16))]
    raise ValueError(suite)


def run_case(case, algorithm='v8', planning_seconds=.20, extra_actions=640,
             fallback_only=False, wall_limit=90, output=None):
    cls = ExtremeSimulator if case.get('extreme') else SyntheticSimulator
    world = cls(case['sources'],error_seed=case['seed'])
    io = OfflineIO(world.transport)
    if algorithm=='v7':
        from adaptive_v7 import SolverV7
        solver = SolverV7(io,case['problem'])
    else:
        solver = SolverV8(io,case['problem'],planning_seconds=planning_seconds,
                          extra_actions=extra_actions,fallback_only=fallback_only)
    result = dict(name=case['name'],algorithm=algorithm,problem=case['problem'],seed=case['seed'],
                  source_count=len(case['sources']),source_truth=[asdict(s) for s in case['sources']],
                  noise='fixed extreme +/-1 degree' if case.get('extreme') else 'repository fixed coordinate hash',
                  kind='synthetic only; not official simulator evidence',
                  planning_seconds=planning_seconds,extra_actions=extra_actions,
                  fallback_only=fallback_only,wall_limit_s=wall_limit)
    if 'saved_v7_s' in case:
        result['saved_v7_s'] = case['saved_v7_s']
    def expired(*_): raise TimeoutError('Offline wall time limit exceeded')
    # Windows has no SIGALRM: check cooperatively at action/event boundaries.
    # POSIX retains the hard alarm, including during long geometry operations.
    has_alarm = hasattr(signal, 'SIGALRM')
    previous = signal.signal(signal.SIGALRM,expired) if has_alarm else None
    if has_alarm:
        signal.alarm(wall_limit)
    io.wall_deadline = time.monotonic() + wall_limit if wall_limit > 0 else math.inf
    started = time.perf_counter()
    try:
        result['summary'] = solver.run()
        if algorithm=='v8':
            audit = replay(io.events)
            result['replay'] = {k:audit[k] for k in ('verified','actions','virtual_time_s')}
            receipts = [e for e in io.events if e.get('event')=='rank_receipt']
            if any(e['after']>=e['before'] for e in receipts):
                raise AssertionError('Completion rank did not strictly decrease')
        if len(world.cleared)!=len(case['sources']) or not solver.certificate or not solver.exit_confirmed:
            raise AssertionError('Solver failed actual full clearance or declared completion')
        if abs(world.virtual_time-solver.virtual)>5e-5:
            raise AssertionError('Simulator and solver virtual times differ')
        result['error'] = None
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
        result['traceback'] = traceback.format_exc()
        result['summary'] = solver.summary()
    finally:
        if has_alarm:
            signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    result.update(wall_s=time.perf_counter()-started,cleared_count=len(world.cleared),
                  virtual_time_s=world.virtual_time,average_clear_time_s=world.virtual_time/len(case['sources']),
                  counts=world.counts,event_counts=dict(io.counts))
    if output is not None:
        output.mkdir(parents=True,exist_ok=True)
        name = f'{algorithm}-{case["name"]}'
        raw = ''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in io.events)
        (output/f'{name}.jsonl').write_text(raw,encoding='utf-8')
        result['log_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
        (output/f'{name}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result,io.events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=('matched','stress','fallback','calibration'),default='matched')
    parser.add_argument('--algorithm',choices=('v7','v8'),default='v8')
    parser.add_argument('--planning-seconds',type=float,default=.20)
    parser.add_argument('--extra-actions',type=int,default=640)
    parser.add_argument('--wall-limit',type=int,default=90)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'results')
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    if args.suite=='calibration':
        result = [calibrate([(0,),(60,),(120,)],(0,60,120)),
                  calibrate([(0,120),(120,0)],(0,60,120)),
                  calibrate([(0,180),(60,120),(180,0)],(0,60,120,180))]
        (args.output/'calibration.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2));return 0
    results = []
    for case in cases(args.suite):
        result,_ = run_case(case,args.algorithm,args.planning_seconds,args.extra_actions,
                           fallback_only=args.suite=='fallback',wall_limit=args.wall_limit,output=args.output)
        results.append(result)
        print(json.dumps({k:result[k] for k in ('name','algorithm','source_count','cleared_count',
                                               'virtual_time_s','wall_s','error')},ensure_ascii=False),flush=True)
    (args.output/f'{args.algorithm}-{args.suite}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    return int(any(r['error'] for r in results))


if __name__=='__main__':
    raise SystemExit(main())
