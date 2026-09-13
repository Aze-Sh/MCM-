import importlib.util,math,sys
from pathlib import Path
ROOT=Path('/home/public/zcq/MCM/MCM-')
sys.path[:0]=['/tmp/mcm-fourth-stage/base',str(ROOT/'solutions/baseline/python')]
from near_optimal import suanfa as v
spec=importlib.util.spec_from_file_location('bench',ROOT/'experiments/near-optimal/benchmark.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
old=v.xuan_dongzuo
improvements=[]
def choose(planner,ledger,position,tuned,search):
    event=old(planner,ledger,position,tuned,search)
    if ledger['problem']==3 and event is not None and event['kind']=='clear' and event.get('target') is not None:
        source=ledger['channels'][event['channel']]['source']
        q=v.continuous_clear(source,position,event['target'])
        if q is not None:
            original=v.g.floating(event['points'][0]);target=event['target'];new=v.g.floating(q)
            gain=(math.dist(position,original)+math.dist(original,target)-math.dist(position,new)-math.dist(new,target))/5
            if gain>1e-7:
                improvements.append(gain)
                event=dict(event,points=(q,),method='verified_clear_route_to_next_entry')
    return event
v.xuan_dongzuo=choose
output=ROOT/'experiments/near-optimal/results/optimization-20260912/trial38-clear-route'
for suite in ('matched','validation'):
    for case in [c for c in b.cases(suite) if c['problem']==3]:
        improvements.clear()
        result,_=b.run_case(case,output=output,wall_limit=180)
        print(case['name'],result['virtual_time_s'],result['cleared_count'],result['error'],'moves',len(improvements),'predicted_gain',sum(improvements),flush=True)
