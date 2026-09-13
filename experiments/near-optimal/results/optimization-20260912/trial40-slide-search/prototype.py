import importlib.util,math,sys
from pathlib import Path
ROOT=Path('/home/public/zcq/MCM/MCM-')
sys.path[:0]=['/tmp/mcm-fourth-stage/base',str(ROOT/'solutions/baseline/python')]
from near_optimal import suanfa as v
spec=importlib.util.spec_from_file_location('bench',ROOT/'experiments/near-optimal/benchmark.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
old=v.gengxin_luxian
moves=[]
def refresh(plan,ledger,position):
    pending=plan['pending_stop']
    route=old(plan,ledger,position)
    if ledger['problem']!=3 or pending is None or not route:return route
    if math.dist(route[0],position)<1e-7:return route
    unknown=v.pindao(ledger,('unknown',))
    common=set.intersection(*(set(ledger['channels'][c]['radio']) for c in unknown))
    fixed=common|{v.g.point(q) for q in route[1:]}
    origin=tuple(route[0]);lo=0.;hi=1.;best=origin
    for step in range(7):
        fraction=1. if step==0 else (lo+hi)/2
        q=tuple(origin[k]+fraction*(position[k]-origin[k]) for k in (0,1))
        points=tuple(sorted(fixed|{v.g.point(q)}))
        proved,_,_,_=v.g.coverage_certificate(points,(),3,min(4096,ledger['coverage_nodes']),min(12,ledger['coverage_depth']))
        if proved:
            lo=fraction;best=q
            if fraction==1:break
        else:hi=fraction
    if best!=origin:
        route=[best]+route[1:]
        moves.append(dict(from_point=origin,to_point=best,distance=math.dist(origin,best)))
        plan['points']=route;plan['route']=route
    return route
v.gengxin_luxian=refresh
output=ROOT/'experiments/near-optimal/results/optimization-20260912/trial40-slide-search'
for suite in ('matched','validation'):
    for case in [c for c in b.cases(suite) if c['problem']==3]:
        moves.clear()
        result,_=b.run_case(case,output=output,wall_limit=180)
        print(case['name'],result['virtual_time_s'],result['cleared_count'],result['error'],'slides',len(moves),'distance',sum(x['distance'] for x in moves),flush=True)
