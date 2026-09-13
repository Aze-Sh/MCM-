import importlib.util,inspect,sys
from pathlib import Path
ROOT=Path('/home/public/zcq/MCM/MCM-')
sys.path[:0]=['/tmp/mcm-fourth-stage/base',str(ROOT/'solutions/baseline/python')]
from near_optimal import suanfa as v
spec=importlib.util.spec_from_file_location('bench',ROOT/'experiments/near-optimal/benchmark.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
old=v.piliang_celiang
source=inspect.getsource(old)
start=source.index('    radius = 350\n')
end=source.index('        gain = 0.0\n',start)
source=source[:start]+'''    candidates = []
    for angle in range(0,360,30):
        q = (position[0]+350*math.cos(math.radians(angle)),position[1]+350*math.sin(math.radians(angle)))
        candidates.append((angle,350,q))
    seen={q for _,_,q in candidates}
    for c in sorted(pindao(jilu,('found',))):
        yuan=jilu['channels'][c]['source']
        clear=continuous_clear(yuan,position)
        entries=[clear] if clear is not None else [pair_points(yuan,position,f)[0] for f in (.38,.5,.62)]
        for point in entries:
            q=g.floating(point)
            if q in seen:continue
            seen.add(q)
            radius=math.dist(position,q)
            angle=math.degrees(math.atan2(q[1]-position[1],q[0]-position[0]))%360
            candidates.append((angle,radius,q))
    radii={q:radius for _,radius,q in candidates}
    options = []
    for angle,radius,q in candidates:
'''+source[end:]
source=source.replace('    score, angle, q, gain, detour, channels = min(options)','    score, angle, q, gain, detour, channels = min(options)\n    radius = radii[q]')
exec(source,v.__dict__)
new=v.piliang_celiang
v.piliang_celiang=lambda state,unknown:new(state,unknown) if state['problem']==3 else old(state,unknown)
output=ROOT/'experiments/near-optimal/results/optimization-20260912/trial39-shared-service-entry'
for suite in ('matched','validation'):
    for case in [c for c in b.cases(suite) if c['problem']==3]:
        result,events=b.run_case(case,output=output,wall_limit=180)
        radii=[round(e['radius'],2) for e in events if e.get('event')=='batch_observation_selected']
        print(case['name'],result['virtual_time_s'],result['cleared_count'],result['error'],radii,flush=True)
