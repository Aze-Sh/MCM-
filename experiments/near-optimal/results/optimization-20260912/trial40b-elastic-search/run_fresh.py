import sys, importlib.util, json, hashlib
from pathlib import Path
BASE = Path('/tmp/mcm-fourth-stage/base')
HERE = Path('/tmp/mcm-q3-local-cover')
ROOT = Path('/home/public/zcq/MCM/MCM-')
manifest=json.loads((HERE/'sha256.json').read_text())
assert hashlib.sha256((HERE/'install.py').read_bytes()).hexdigest()==manifest[str(HERE/'install.py')]
sys.path[:0] = [str(BASE), str(ROOT/'solutions/baseline/python')]
from near_optimal import suanfa as v
spec=importlib.util.spec_from_file_location('benchmark', HERE/'benchmark_frozen.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
from install import install
install(v)
output=HERE/'fresh-results';rows=[]
for case in b.cases('fresh'):
    if case['problem']!=3:continue
    result,events=b.run_case(case,output=output,wall_limit=180)
    audits=result['summary']['local_search_adjustment']
    result['adjustment_statistics']=dict(attempted=len(audits),proved=sum(a['accepted'] is not None for a in audits),proofs=sum(len(a['checks']) for a in audits),wall_s=sum(a['wall_s'] for a in audits),accepted=[a['accepted'] for a in audits if a['accepted']])
    rows.append(result)
    print(json.dumps({k:result.get(k) for k in ('name','virtual_time_s','source_count','cleared_count','error','replay','wall_s','adjustment_statistics')}),flush=True)
output.mkdir(parents=True,exist_ok=True)
(output/'summary.json').write_text(json.dumps(rows,indent=2))
