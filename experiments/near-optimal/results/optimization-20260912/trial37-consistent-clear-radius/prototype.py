import importlib.util,inspect,sys
from pathlib import Path
ROOT=Path('/home/public/zcq/MCM/MCM-')
sys.path[:0]=['/tmp/mcm-fourth-stage/base',str(ROOT/'solutions/baseline/python')]
from near_optimal import suanfa as v
import posterior
scope=dict(posterior.__dict__)
source=inspect.getsource(posterior.nearest_clear_point)
assert 'radius = CLEAR_RADIUS-1e-6' in source
exec(source.replace('radius = CLEAR_RADIUS-1e-6','radius = 19.8-1e-6'),scope)
v.nearest_clear_point=scope['nearest_clear_point']
spec=importlib.util.spec_from_file_location('bench',ROOT/'experiments/near-optimal/benchmark.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
output=ROOT/'experiments/near-optimal/results/optimization-20260912/trial37-consistent-clear-radius'
for suite in ('matched','validation'):
    for case in b.cases(suite):
        result,_=b.run_case(case,output=output,wall_limit=180)
        print(case['name'],result['virtual_time_s'],result['cleared_count'],result['error'],flush=True)
