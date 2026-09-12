"""v5: joint evidence, whole-outcome route lookahead and certified optical gate."""
from dataclasses import asdict
import math
from cooperative import CooperativeSolver
from solver import ModelMismatch
from strategy import Anchor, annular_points, annular_update
from posterior import constrain
from planning import open_route
from joint_belief import JointBelief, SAFE
from decision import terminal_upper, measurement_envelope, optical_decision, optical_cover, chain_cost

STRATEGY="joint-outcome-lookahead-v5"


class AdaptiveSolver(CooperativeSolver):
    def __init__(self,transport,problem,progress=None):
        super().__init__(transport,problem,progress)
        self.raw_evidence={c:[] for c in range(1,21)}
        self.beliefs={}
        self.posterior_stats={}
        self.reserved_source=None;self.committed_source=None
        self.forecast_cache={}
        self.lookahead_decisions=0;self.shared_by_lookahead=0
        self.optical_accepted=self.optical_overlap_rejected=self.optical_failure_replans=0

    def _sync(self,c):
        belief=self.beliefs[c]
        self.regions[c]=belief.hull()
        if c in self.anchors:
            self.refresh_history(c)
        previous=self.posterior_stats.get(c,{})
        self.posterior_stats[c]=dict(cells=len(belief.cells),
            max_cells=max(len(belief.cells),previous.get("max_cells",0)),
            retained_parent_count=belief.retained_parents,
            raw_observation_count=len(belief.records))

    def _belief(self,c):
        if c not in self.beliefs:
            records=self.raw_evidence[c]
            if not records:
                # Supports explicit offline state fixtures; ordinary runs always
                # arrive here with the actual discovery observation recorded.
                a=self.anchors[c]
                records=[dict(kind="direction",point=a.point,bearing=a.bearing)]
            self.beliefs[c]=JointBelief(self.regions[c],self.problem,records)
            self._sync(c)
        return self.beliefs[c]

    def action(self,path,point,channel):
        reply=super().action(path,point,channel)
        record=None
        if path=="/measure":
            record=dict(kind=reply["measure_result"],point=tuple(point))
            if record["kind"]=="direction":
                record["bearing"]=reply["svd_deg"]
        elif reply["clear_result"]!="success":
            record=dict(kind="clear_failure",point=tuple(point))
        if record is not None:
            self.raw_evidence[channel].append(record)
            if channel in self.beliefs and record["kind"]!="near":
                self.beliefs[channel].observe(record)
                self._sync(channel)
            self.forecast_cache.clear()
        return reply

    def record_positive(self,channel,point):
        super().record_positive(channel,point)
        belief=self._belief(channel)
        belief.intersect(self.regions[channel])
        self._sync(channel)

    def finish_clear(self,channel):
        super().finish_clear(channel)
        self.beliefs.pop(channel,None)
        if self.committed_source==channel:
            self.committed_source=None
        if self.reserved_source==channel:
            self.reserved_source=None
        self.forecast_cache.clear()

    def _forecast(self,c,q,target,cost=6):
        if self.optional_counts[c]>=2 or self.anchors[c].rounds!=0:
            return None
        if tuple(q) in self.positives[c]+self.optional_positions[c]:
            return None
        belief=self._belief(c)
        key=(c,len(self.raw_evidence[c]),self.anchors[c],tuple(q),target,cost)
        if key not in self.forecast_cache:
            self.forecast_cache[key]=measurement_envelope(belief,self.anchors[c],q,self.problem,target,cost)
        return self.forecast_cache[key]

    def choose_candidates(self,route):
        self.reserved_source=None
        if self.committed_source in self.anchors:
            c=self.committed_source
            ready=[c] if self.clear_plan(c)[0] is not None else []
            return [(0.,c)],ready
        target=route[0] if route else None
        direct=math.dist(self.position,target)/5 if target is not None else 0.
        now={}
        for c in self.anchors:
            now[c]=terminal_upper(self._belief(c),self.anchors[c],self.position,self.problem,target)[0]-direct
        if not route:
            return [(value,c) for c,value in now.items()],[c for c in now if self.clear_plan(c)[0] is not None]
        future=route[1] if len(route)>1 else None
        edge=math.dist(target,future)/5 if future is not None else 0.
        # All sources receive route-aware bounds; at most three receive the
        # more expensive whole-response branching in one decision.
        shortlist=set(sorted(now,key=lambda c:now[c])[:3])
        immediate=[];ready=[];deferred=[]
        for c,current in now.items():
            later=terminal_upper(self._belief(c),self.anchors[c],target,self.problem,future)[0]-edge
            read=False;envelope=None
            if c in shortlist and self.clear_plan(c)[0] is None:
                envelope=self._forecast(c,target,future)
                if envelope is not None and envelope["upper_s"]-edge<later-1:
                    later=envelope["upper_s"]-edge;read=True
            if current<=later+1:
                immediate.append((current,c))
                if self.clear_plan(c)[0] is not None:
                    ready.append(c)
            else:
                deferred.append((current-later,c,read))
            self.lookahead_decisions+=1
            self.emit("route_information_comparison",channel=c,now_extra_upper_s=current,
                      next_stop_extra_upper_s=later,next_stop=target,after_stop=future,
                      proposed_shared_measure=read,
                      outcome_count=0 if envelope is None else len(envelope["branches"]),
                      interpretation="conditional_upper_bounds_not_realized_savings")
        if not immediate:
            choices=[entry for entry in deferred if entry[2]]
            if choices:
                self.reserved_source=max(choices)[1]
        return immediate,ready

    def shared_measurements(self,point):
        route=open_route(point,self.remaining) if self.unknown and len(self.discovered)<16 else []
        target=route[0] if route else None
        chosen=self.reserved_source if self.reserved_source in self.anchors else None
        self.reserved_source=None
        if chosen is None:
            options=[]
            for c in sorted(self.anchors,key=lambda c:math.dist(self.anchors[c].point,point))[:3]:
                if self.clear_plan(c)[0] is not None:
                    continue
                before,_=terminal_upper(self._belief(c),self.anchors[c],point,self.problem,target)
                plan=self._forecast(c,point,target,5+int(c!=self.channel))
                if plan is not None and plan["upper_s"]<before-1:
                    options.append((before-plan["upper_s"],c))
            if options:
                chosen=max(options)[1]
        if chosen is None:
            self.stage="search";return
        c=chosen
        if self.clear_plan(c)[0] is not None:
            self.committed_source=c;return
        plan=self._forecast(c,point,target,5+int(c!=self.channel))
        if plan is None:
            return
        self.stage="shared_measure"
        reply=self.action("/measure",point,c)
        self.optional_counts[c]+=1;self.optional_positions[c].append(tuple(point))
        self.shared_by_lookahead+=1
        self.emit("shared_measure_by_outcomes",channel=c,result=reply["measure_result"],
                  predicted_completion_upper_s=plan["upper_s"],outcome_count=len(plan["branches"]))
        if reply["measure_result"]=="near":
            self.clear(point,c)
        elif reply["measure_result"]=="direction":
            if self.anchors[c].rounds!=0:
                raise ModelMismatch("Shared observation attempted after local contraction began")
            bound=max(math.dist(point,v) for v in self.regions[c])+SAFE
            self.anchors[c]=Anchor(tuple(point),reply["svd_deg"],min(1000,bound),0)
            self.regions[c]=constrain(self.regions[c],self.anchors[c],annular=True)
            self.record_positive(c,point)
        elif self.problem==3:
            raise ModelMismatch("In-range shared observation lost omnidirectional signal")
        else:
            self.directions[c].negative(point,self.positives[c])
        if c in self.anchors:
            # Execute the continuation after the chosen observation; do not keep
            # spending shared reads merely because new forecasts look attractive.
            self.committed_source=c
        self.stage="search"

    def approach(self,channel):
        self._belief(channel)
        self.stage="localize"
        while channel not in self.cleared:
            anchor=self.anchors[channel]
            point,method=self.improved_clear(channel,self.position,self.route_target)
            if point is not None:
                self.emit("clear_planned",channel=channel,point=point,method=method)
                self.clear(point,channel);return
            plan,decision=optical_decision(self.beliefs[channel],anchor,self.position,
                                           self.route_target,int(channel!=self.channel))
            self.emit("optical_bound_comparison",channel=channel,**decision)
            self.optical_overlap_rejected+=int(decision["reason"]=="bounds_overlap_keep_rf")
            if plan is not None:
                self.optical_accepted+=1
                self.emit("optical_cover_planned",channel=channel,**plan)
                self.stage="clear";remaining=list(plan["points"]);attempts=0
                while remaining and attempts<3:
                    q=remaining.pop(0);attempts+=1;self.optical_probes+=1
                    reply=self.action("/clear",q,channel)
                    if reply["clear_result"]=="success":
                        self.finish_clear(channel);return
                    self.failed_clears+=1
                    self.emit("optical_probe_negative",channel=channel,point=q)
                    if remaining:
                        revised=optical_cover(self.beliefs[channel],self.anchors[channel],
                                             self.position,self.route_target,3-attempts)
                        if revised is not None and revised["worst_time_s"]<chain_cost(remaining,self.position,self.route_target)-1e-5:
                            remaining=list(revised["points"]);self.optical_failure_replans+=1
                            self.emit("optical_failure_replanned",channel=channel,**revised)
                raise ModelMismatch("Certified optical cover exhausted without success")
            if anchor.rounds>=(5 if self.problem==3 else 6):
                raise ModelMismatch("Annular round bound exceeded")
            for q in annular_points(anchor,self.position):
                reply=self.action("/measure",q,channel)
                self.source_measures[channel]=self.source_measures.get(channel,0)+1
                if reply["measure_result"]=="near":
                    self.clear(q,channel);return
                if reply["measure_result"]=="direction":
                    self.anchors[channel]=annular_update(anchor,q,reply["svd_deg"])
                    self.regions[channel]=constrain(self.regions[channel],self.anchors[channel],annular=True)
                    self.record_positive(channel,q)
                    break
                if self.problem==3:
                    raise ModelMismatch("Guaranteed omnidirectional measurement lost signal")
                self.directions[channel].negative(q,self.positives[channel])
            else:
                self.anchors[channel]=annular_update(anchor)
                self.negative_pairs[channel]=self.negative_pairs.get(channel,0)+1
                self.regions[channel]=constrain(self.regions[channel],self.anchors[channel],annular=True)
                self.beliefs[channel].intersect(self.regions[channel]);self._sync(channel)
            self.emit("anchor_updated",channel=channel,anchor=asdict(self.anchors[channel]))

    def summary(self):
        result=super().summary()
        result.update(strategy=STRATEGY,posterior_cells=self.posterior_stats,
                      lookahead_decisions=self.lookahead_decisions,shared_by_lookahead=self.shared_by_lookahead,
                      optical_dominance_accepts=self.optical_accepted,
                      optical_overlap_rejections=self.optical_overlap_rejected,
                      optical_failure_replans=self.optical_failure_replans)
        return result
