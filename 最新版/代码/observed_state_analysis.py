"""Read the first actual scan; compare policy bounds without executing actions."""
import json
from pathlib import Path
from adaptive_v7 import SolverV7
from strategy import Anchor
from posterior import initial_region
from evidence import disk_outer
from service_graph import build_graph
from interception import choose_interception


class ReadOnlyTransport:
    pending=None
    def record(self,event):pass
    def call(self,*args,**kwargs):raise RuntimeError('Observed-state analysis cannot execute any action')


def analyze_first_scan(folder):
    folder=Path(folder);meta=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    s=SolverV7(ReadOnlyTransport(),meta['problem']);intents={};seen=set()
    for line in (folder/'actions.jsonl').read_text(encoding='utf-8').splitlines():
        event=json.loads(line)
        if event.get('event')=='intent':intents[event['payload']['request_id']]=event
        if event.get('event')=='response' and event['response'].get('accepted'):
            rid=event['request_id']
            if rid in seen:continue
            seen.add(rid);intent=intents[rid];reply=event['response'];path=intent['path']
            if path not in ('/measure','/clear'):continue
            payload=intent['payload'];p=(payload['position']['x'],payload['position']['y']);c=payload['channel']
            s.position=p;s.virtual=reply['virtual_time_s']
            if path=='/clear':
                if reply['clear_result']=='success':s.finish_clear(c)
                continue
            s.channel=c;kind=reply['measure_result'];record=dict(kind=kind,point=p)
            if kind=='direction':record['bearing']=reply['svd_deg']
            s.raw_evidence[c].append(record)
            if kind=='no_signal':s.search_negatives[c].append(p);continue
            s.discover(c)
            if kind=='direction':
                s.anchors[c]=Anchor(p,reply['svd_deg'])
                s.regions[c]=disk_outer(initial_region(s.anchors[c],annular=True),(0,0),1800,128)
                s.record_positive(c,p)
        if event.get('event')=='search_point_done':
            s.visited.append(s.position);s.remaining.remove(s.position);break
    graph=build_graph(s,s.remaining);plan=graph.optimize()
    first_source=next((m for m in plan['modes'] if m.kind in ('radio','regional_probe')),None)
    intercept=None;diagnostic=None
    if first_source:
        c=first_source.job[1];target=next((m.entry for m in plan['modes'] if m.kind=='scan'),None)
        alone=__import__('math').dist(s.position,first_source.entry)/5+first_source.service_s
        total=alone+(first_source.departure(target) if target is not None else 0.)
        intercept,diagnostic=choose_interception(s._belief(c),s.anchors[c],s.position,s.problem,target,total,alone,channel_switch=int(c!=s.channel))
    return dict(problem=s.problem,case_code=meta['case_code'],observed_version=meta['strategy'],
        observation_cutoff_virtual_s=s.virtual,known_sources=len(s.anchors),remaining_scans=len(s.remaining),
        baseline_complete_order_upper_s=plan['baseline_upper_s'],selected_complete_order_upper_s=plan['upper_s'],
        assignment_lower_s=plan['assignment_lower_s'],finite_graph_gap_s=plan['finite_graph_gap_s'],
        planned_order=plan['order'],planned_modes=[m.kind for m in plan['modes']],information_candidate=intercept,information_diagnostic=diagnostic,
        interpretation='Real observations; alternative policy bounds only. No alternative response or simulated total time was generated.')
