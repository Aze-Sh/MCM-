"""v7: complete-obligation planning, active observations and service accounting."""
from dataclasses import asdict
import math
import time
from adaptive_v6 import SolverV6
from solver import ModelMismatch,BudgetStop
from strategy import Anchor,annular_points,annular_update,annular_clear_point
from posterior import constrain,nearest_clear_point
from planning import fallback_bound,open_route
from joint_belief import SAFE
from service_graph import build_graph,source_modes
from interception import choose_interception
from coverage_v7 import revise_route,proof_allowance
from optical_v7 import optical_decision,optical_cover,conditional_chain
from probe_frontier import regional_upper

STRATEGY='obligation-service-interception-v7'


class SolverV7(SolverV6):
    def __init__(self,transport,problem,progress=None):
        super().__init__(transport,problem,progress)
        self.incumbent=[];self.incumbent_modes=[]
        self.global_plans=[];self.service_receipts=[];self.information_decisions=[]
        self.active_information_reads=0;self.stationary_information_reads=0
        self.max_pending_sources=0;self.first_discovery_times={}
        self.source_waits={};self.source_service_start={}
        self.active_service=None
        self.regional_probe_count=0

    def discover(self,channel):
        super().discover(channel)
        self.first_discovery_times[channel]=self.virtual

    def finish_clear(self,channel):
        if channel in self.first_discovery_times:
            start=self.source_service_start.get(channel,self.virtual)
            self.source_waits[channel]=dict(wait_until_service_s=start-self.first_discovery_times[channel],
                discovery_to_clear_s=self.virtual-self.first_discovery_times[channel])
        super().finish_clear(channel)

    def next_route(self):
        route=open_route(self.position,self.remaining)
        revision=(len(self.visited),len(self.cleared))
        allowance=proof_allowance(len(self.visited),self.scan_limit,self.tail_proof_calls)
        if self.visited and self.unknown and revision!=self.last_tail_revision and allowance:
            self.last_tail_revision=revision
            route,d=revise_route(self.position,self.visited,route,self.problem,allowance)
            self.tail_proof_calls+=d['proofs_attempted'];self.tail_edits.append(d)
            self.emit('residual_route_revision',**d);self.remaining=list(route)
        return route

    def radio_round(self,c,anchor=None,first=None):
        a=self.anchors[c] if anchor is None else anchor
        if a.rounds>=(5 if self.problem==3 else 6) or a.bound<=44.5:
            raise ModelMismatch('Radio round violates finite contraction conditions')
        pair=list(annular_points(a,self.position))
        if first is not None:
            if min(math.dist(first,p) for p in pair)>1e-7:
                raise ModelMismatch('Planned probe does not belong to its certified anchor')
            pair.sort(key=lambda p:math.dist(p,first))
        # An older but still valid outer anchor may be retained by the incumbent.
        # It has the same consumed round count and does not reset any work.
        self.anchors[c]=a;self.stage='localize'
        for q in pair:
            reply=self.action('/measure',q,c)
            self.source_measures[c]=self.source_measures.get(c,0)+1
            if reply['measure_result']=='near':
                self.clear(q,c);return
            if reply['measure_result']=='direction':
                self.anchors[c]=annular_update(a,q,reply['svd_deg'])
                self.regions[c]=constrain(self.regions[c],self.anchors[c],annular=True)
                self.record_positive(c,q);break
            if self.problem==3:
                raise ModelMismatch('Guaranteed omnidirectional reception failed')
            self.directions[c].negative(q,self.positives[c])
        else:
            self.anchors[c]=annular_update(a)
            self.negative_pairs[c]=self.negative_pairs.get(c,0)+1
            self.regions[c]=constrain(self.regions[c],self.anchors[c],annular=True)
            self.beliefs[c].intersect(self.regions[c]);self._sync(c)
        self.emit('anchor_updated',channel=c,anchor=asdict(self.anchors[c]))

    def optical(self,c,target):
        plan,d=optical_decision(self._belief(c),self.anchors[c],self.position,target,int(c!=self.channel))
        self.emit('optical_bound_comparison',channel=c,**d)
        self.optical_overlap_rejected+=int(d['reason']=='bounds_overlap_keep_rf')
        if plan is None:
            return False
        self.optical_accepted+=1;self.emit('optical_cover_planned',channel=c,**plan)
        start=self.virtual;limit=plan['worst_time_s']
        alone=conditional_chain(self.beliefs[c].polygons(),plan['points'],self.position)['worst_time_s']
        self.stage='clear';remaining=list(plan['points']);attempts=0
        while remaining and attempts<3:
            q=remaining.pop(0);attempts+=1;self.optical_probes+=1
            reply=self.action('/clear',q,c)
            if reply['clear_result']=='success':
                self.finish_clear(c);return True
            self.failed_clears+=1;self.emit('optical_probe_negative',channel=c,point=q)
            if remaining:
                revised=optical_cover(self.beliefs[c],self.anchors[c],self.position,target,3-attempts)
                spent=self.virtual-start
                if revised is not None:
                    other=conditional_chain(self.beliefs[c].polygons(),revised['points'],self.position)['worst_time_s']
                    if revised['worst_time_s']<=limit-spent-1e-6 and other<=alone-spent-1e-6:
                        remaining=list(revised['points']);self.optical_failure_replans+=1
                        self.emit('optical_failure_replanned',channel=c,**revised)
        raise ModelMismatch('Certified optical chain exhausted')

    def complete_reference(self,c,target):
        """Execute a continuation bounded by the ordinary annular fallback."""
        while c in self.anchors:
            a=self.anchors[c]
            self.refine_actions(c,list(annular_points(a,self.position))+[target],target)
            a=self.anchors[c];p=self.position;poly=self._belief(c).hull()
            switch=int(c!=self.channel)
            alone=fallback_bound(a,p,self.problem)-1+switch
            bound=fallback_bound(a,p,self.problem,target,poly)-1+switch if target is not None else alone
            points=[nearest_clear_point(poly,p),annular_clear_point(a,p)]
            if target is not None:points.append(nearest_clear_point(poly,target))
            candidates=[]
            for q in points:
                if q is None:continue
                local=math.dist(p,q)/5+5
                total=local+(math.dist(q,target)/5 if target is not None else 0.)
                if local<=alone+1e-6 and total<=bound+1e-6:
                    candidates.append((total,q))
            if candidates:
                self.clear(min(candidates)[1],c);return
            if self.optical(c,target):return
            regional=regional_upper(self._belief(c),a,p,target)
            if regional is not None and regional[0]<=bound-1e-6 and regional[1]<=alone-1e-6:
                self.regional_round(c,a,regional[2]['point'],regional[2]['bound'])
                continue
            self.radio_round(c)

    def regional_round(self,c,anchor,point,bound):
        if bound>.502*anchor.bound-2.4+1e-7 or anchor.rounds>=(5 if self.problem==3 else 6):
            raise ModelMismatch('Regional probe does not preserve the contraction bound')
        self.stage='localize';reply=self.action('/measure',point,c)
        self.source_measures[c]=self.source_measures.get(c,0)+1;self.regional_probe_count+=1
        self.emit('regional_probe_executed',channel=c,point=point,bound=bound)
        if reply['measure_result']=='near':self.clear(point,c);return
        if reply['measure_result']!='direction':raise ModelMismatch('Certified visible regional probe lost signal')
        self.anchors[c]=Anchor(tuple(point),reply['svd_deg'],bound,anchor.rounds+1)
        self.regions[c]=constrain(self.regions[c],self.anchors[c],annular=True)
        self.record_positive(c,point)

    def information_read(self,c,plan,target):
        point=plan['point'];before=self.position;self.stage='shared_measure'
        reply=self.action('/measure',point,c)
        self.optional_counts[c]+=1;self.optional_positions[c].append(tuple(point))
        stationary=math.dist(before,point)<1e-6
        self.stationary_information_reads+=int(stationary)
        self.active_information_reads+=int(not stationary);self.shared_by_lookahead+=1
        self.emit('information_intercept_executed',channel=c,stationary=stationary,
                  response=reply['measure_result'],**plan)
        if reply['measure_result']=='near':self.clear(point,c);return
        if reply['measure_result']=='direction':
            if self.anchors[c].rounds!=0:raise ModelMismatch('Information step reset consumed rounds')
            bound=max(math.dist(point,v) for v in self.regions[c])+SAFE
            self.anchors[c]=Anchor(tuple(point),reply['svd_deg'],min(1500.,bound),0)
            self.regions[c]=constrain(self.regions[c],self.anchors[c],annular=True)
            self.record_positive(c,point)
        elif self.problem==3:raise ModelMismatch('Guaranteed information point lost reception')
        else:self.directions[c].negative(point,self.positives[c])
        self.complete_reference(c,target)

    def execute_source(self,c,mode,target):
        self.source_service_start[c]=self.virtual
        self.route_target=target;self.stage='localize'
        if mode.kind=='clear':
            self.clear(mode.entry,c);return
        if self.optical(c,target):return
        alone=math.dist(self.position,mode.entry)/5+mode.service_s
        total=alone+(mode.departure(target) if target is not None else 0.)
        plan,d=choose_interception(self._belief(c),self.anchors[c],self.position,self.problem,target,
            total,alone,self.optional_counts[c],self.optional_positions[c],int(c!=self.channel))
        self.information_decisions.append(dict(channel=c,**d,selected=plan))
        self.emit('information_intercept_decision',channel=c,**d,selected=plan)
        if plan is not None:
            self.information_read(c,plan,target);return
        if mode.kind=='regional_probe':self.regional_round(c,mode.anchor,mode.entry,mode.probe_bound)
        else:self.radio_round(c,mode.anchor,mode.first_probe)
        if c in self.anchors:self.complete_reference(c,target)

    def approach(self,c):
        modes=source_modes(c,self.anchors[c],self._belief(c).hull(),self.problem,self.position,belief=self._belief(c))
        mode=min(modes,key=lambda m:math.dist(self.position,m.entry)/5+m.service_s+(m.departure(self.route_target) if self.route_target is not None else 0.))
        self.execute_source(c,mode,self.route_target)

    def run(self):
        self.started=time.monotonic();reply=self.io.call('/enter');self.entered=True
        self.virtual=reply['virtual_time_s'];self.max_virtual=reply['max_virtual_duration_s']
        self.deadline=self.started+reply['remaining_real_duration_s'];self.io.deadline=self.deadline
        self.reason='running'
        try:
            while self.anchors or self.search_needed():
                route=self.next_route() if self.search_needed() else []
                if not route and not self.anchors:break
                self.max_pending_sources=max(self.max_pending_sources,len(self.anchors))
                graph=build_graph(self,route,self.incumbent_modes)
                plan=graph.optimize(self.incumbent)
                self.incumbent=list(plan['order']);self.incumbent_modes=list(plan['modes'])
                first=plan['modes'][0];target=plan['modes'][1].entry if len(plan['modes'])>1 else None
                diagnostic={k:v for k,v in plan.items() if k!='modes'}
                diagnostic.update(pending_sources=len(self.anchors),pending_scans=len(route),
                    first_kind=first.kind,first_entry=first.entry,
                    interpretation='bounds_on_current_known_obligations_not_future_hidden_sources')
                self.global_plans.append(diagnostic);self.emit('complete_obligation_plan',**diagnostic)
                start=self.virtual;position=self.position
                local_bound=math.dist(position,first.entry)/5+first.service_s
                with_target=local_bound+(first.departure(target) if target is not None else 0.)
                self.active_service=dict(job=first.job,start_virtual_s=start,local_upper_s=local_bound,
                                         completion_and_successor_upper_s=with_target,target=target)
                if first.kind=='scan':self.scan(first.entry)
                else:self.execute_source(first.job[1],first,target)
                actual=self.virtual-start;remaining_leg=math.dist(self.position,target)/5 if target is not None else 0.
                receipt=dict(self.active_service,actual_service_s=actual,
                             feasible_successor_leg_s=remaining_leg,
                             local_upper_slack_s=local_bound-actual,
                             completion_and_successor_slack_s=with_target-actual-remaining_leg)
                self.service_receipts.append(receipt);self.emit('service_completed',**receipt);self.active_service=None
                if min(receipt['local_upper_slack_s'],receipt['completion_and_successor_slack_s'])<-1e-3:
                    raise ModelMismatch('Executed service exceeded its committed upper bound')
                if self.search_needed():self.certify_unknown()
            if self.anchors or self.discovered!=self.cleared:raise ModelMismatch('Uncleared discovered sources remain')
            if not 10<=len(self.discovered)<=16:raise ModelMismatch('Completion contradicts source-count interval')
            if len(self.discovered)==16:self.completion_basis='source_count_upper_bound'
            elif not self.remaining:self.completion_basis='proved_coverage_schedule'
            elif self.unknown:raise ModelMismatch('Unresolved unknown channels remain')
            self.absent.update(self.unknown);self.unknown.clear();self.certificate=True;self.reason='complete_with_certificate'
        except BudgetStop as exc:self.reason=str(exc)
        self.exit();return self.summary()

    def summary(self):
        result=super().summary()
        result.update(strategy=STRATEGY,global_obligation_plans=self.global_plans,
            service_receipts=self.service_receipts,information_decisions=self.information_decisions,
            active_information_reads=self.active_information_reads,stationary_information_reads=self.stationary_information_reads,
            max_pending_sources=self.max_pending_sources,source_waits=self.source_waits,pending_service=self.active_service,
            regional_probe_count=self.regional_probe_count)
        return result
