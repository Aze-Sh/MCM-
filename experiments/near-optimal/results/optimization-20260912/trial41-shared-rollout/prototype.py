import copy,importlib.util,inspect,math,sys,time
from pathlib import Path
ROOT=Path('/home/public/zcq/MCM/MCM-')
sys.path[:0]=['/tmp/mcm-fourth-stage/base',str(ROOT/'solutions/baseline/python')]
from near_optimal import suanfa as v
spec=importlib.util.spec_from_file_location('bench',ROOT/'experiments/near-optimal/benchmark.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
old=v.piliang_celiang
source=inspect.getsource(old);source=source[:source.index('    baocun_shijian(\n')]+"    return channels,q\n"
source=source.replace('def piliang_celiang(', 'def select_batch(')
scope=dict(v.__dict__);exec(source,scope);select=scope['select_batch']

def hypotheses(state,k):
    result=[]
    for i,c in enumerate(sorted(v.pindao(state['ledger'],('found',)))):
        fit,_=v.radio_model(state['ledger']['channels'][c]);parts=[]
        for p,lo,hi,angles,omni,area in fit:
            if omni:parts.append((p,(lo+hi)/2,area*(hi-lo)))
        mass=sum(w for p,r,w in parts)
        if mass<=0:raise ArithmeticError('No valid hypothesis at this quadrature resolution')
        fraction=((k+.5)/3+i*.6180339887498949)%1
        target=fraction*mass
        for p,r,w in parts:
            target-=w
            if target<=0:break
        result.append(b.Source(c,p,r,None))
    return result

def complete_known(state,truth,k,channels,q,tail,deadline):
    shadow=copy.deepcopy({name:value for name,value in state.items() if name not in ('io','progress')})
    world=b.SyntheticSimulator(truth,error_seed=17+k)
    world.active=True;world.position=state['position'];world.channel=state['channel'];world.virtual_time=state['virtual']
    shadow['io']=b.OfflineIO(world.transport);shadow['progress']=None;shadow['deadline']=math.inf
    shadow['planner']['seconds']=0
    for record in shadow['ledger']['channels'].values():
        if record['status']=='unknown':record['status']='absent';record['pending'].clear()
    if q is not None:
        for c in channels:v.zhixing(shadow,'/measure',q,c)
    while v.pindao(shadow['ledger'],('found',)):
        if time.perf_counter()>deadline:raise TimeoutError('Prediction budget reached')
        event=v.xuan_dongzuo(shadow['planner'],shadow['ledger'],shadow['position'],shadow['channel'],[])
        if event is None or not v.zhixing_shijian(shadow,event):raise RuntimeError('Predicted source service could not finish')
    return shadow['virtual']-state['virtual']+v.route_length(shadow['position'],v.open_route(shadow['position'],tail))/5

def predict(state,unknown):
    if state['problem']!=3:return old(state,unknown)
    choice=select(state,unknown)
    if choice is True:return True
    channels,original=choice
    ledger=state['ledger'];position=state['position']
    entry=v.xuan_dongzuo(copy.deepcopy(state['planner']),ledger,position,state['channel'],[])['points'][0]
    entry=v.g.floating(entry)
    candidates=[original,None]
    if entry!=original:candidates.append(entry)
    unknown_now=v.pindao(ledger,('unknown',))
    common=set.intersection(*(set(ledger['channels'][c]['radio']) for c in unknown_now)) if unknown_now else set()
    tail=[p for p in state['search_plan']['points'] if v.g.point(p) not in common] if unknown_now else []
    totals=[0.]*len(candidates);started=time.perf_counter();deadline=started+20
    try:
        for k in range(3):
            truth=hypotheses(state,k)
            for i,q in enumerate(candidates):totals[i]+=complete_known(state,truth,k,channels,q,tail,deadline)/3
    except (ArithmeticError,TimeoutError,RuntimeError) as error:
        v.baocun_shijian(state,'shared_prediction_rejected',reason=str(error),wall_s=time.perf_counter()-started)
        return old(state,unknown)
    best=min(range(len(totals)),key=lambda i:totals[i]);q=candidates[best]
    v.baocun_shijian(state,'shared_prediction_selected',choice=best,points=candidates,predicted_s=totals,wall_s=time.perf_counter()-started)
    if q is not None:
        for c in channels:
            if ledger['extra']<2 or not v.yusuan_jiancha(state,(q,)):return False
            v.zhixing(state,'/measure',q,c)
    return True
v.piliang_celiang=predict
output=ROOT/'experiments/near-optimal/results/optimization-20260912/trial41-shared-rollout'
for case in [c for c in b.cases('matched') if c['problem']==3]:
    result,events=b.run_case(case,output=output,wall_limit=240)
    notes=[e for e in events if e.get('event','').startswith('shared_prediction_')]
    print(case['name'],result['virtual_time_s'],result['cleared_count'],result['wall_s'],result['error'],notes,flush=True)
