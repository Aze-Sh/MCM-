import sys,importlib.util,json
from pathlib import Path
ROOT=Path('/home/public/zcq/MCM/MCM-');BASE=Path('/tmp/mcm-fourth-stage/base')
sys.path[:0]=[str(BASE),str(ROOT/'solutions/baseline/python')]
from near_optimal import suanfa as v
text=(ROOT/'experiments/near-optimal/benchmark.py').read_text().replace('ROOT = Path(__file__).resolve().parents[2]',f'ROOT = Path({str(ROOT)!r})').replace("sys.path[:0] = [str(ROOT/'solutions/adaptive/python'),str(ROOT/'solutions/baseline/python')]",f"sys.path[:0] = [{str(BASE)!r},str(ROOT/'solutions/baseline/python')]")
path=Path('/tmp/mcm-q3-local-cover/benchmark_frozen.py');path.write_text(text)
spec=importlib.util.spec_from_file_location('benchmark',path);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
from install import install
install(v)
output=Path('/tmp/mcm-q3-local-cover/results');results=[]
for case in b.cases('matched')+b.cases('validation'):
    if case['problem']!=3:continue
    result,events=b.run_case(case,output=output,wall_limit=180)
    audits=result['summary']['local_search_adjustment'];result['adjustment_statistics']=dict(attempted=len(audits),proved=sum(a['accepted'] is not None for a in audits),proofs=sum(len(a['checks']) for a in audits),wall_s=sum(a['wall_s'] for a in audits),accepted=[a['accepted'] for a in audits if a['accepted']])
    results.append(result)
    print(json.dumps({k:result.get(k) for k in ('name','virtual_time_s','source_count','cleared_count','error','replay','wall_s','adjustment_statistics')}),flush=True)
output.mkdir(parents=True,exist_ok=True);(output/'summary.json').write_text(json.dumps(results,indent=2))
