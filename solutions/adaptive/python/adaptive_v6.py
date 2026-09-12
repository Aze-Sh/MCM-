"""v6: residual coverage edits and executable common-endpoint episodes."""
from dataclasses import asdict
import math
import time
from adaptive import AdaptiveSolver
from solver import ModelMismatch, BudgetStop
from strategy import Anchor, annular_points, annular_update
from posterior import constrain
from planning import open_route
from joint_belief import SAFE
from refinement import DecisionBelief
from decision import terminal_upper, chain_cost
from decision_v6 import optical_decision, optical_cover
from tail_search import revise_route

STRATEGY="residual-committed-policy-v6"


class SolverV6(AdaptiveSolver):
    def __init__(self,transport,problem,progress=None):
        super().__init__(transport,problem,progress)
        self.episode=None;self.episodes=[];self.tail_edits=[]
        self.last_tail_revision=None;self.tail_proof_calls=0
        self.refinement_decisions=[]

    def _belief(self,c):
        if c not in self.beliefs:
            records=self.raw_evidence[c] or [dict(kind="direction",point=self.anchors[c].point,bearing=self.anchors[c].bearing)]
            self.beliefs[c]=DecisionBelief(self.regions[c],self.problem,records)
            self._sync(c)
        return self.beliefs[c]

    def refine_actions(self,c,points,target):
        diagnostic=self._belief(c).refine_for_actions(points,self.position,target)
        if diagnostic["splits"]:
            self._sync(c);self.forecast_cache.clear()
            self.refinement_decisions.append(dict(channel=c,**diagnostic))
            self.emit("action_refinement",channel=c,**diagnostic)

    def shared_measurements(self,point):
        # The episode explicitly selects the only optional reading. A scan must
        # not secretly insert another source or change the committed endpoint.
        self.stage="search"

    def action(self,path,point,channel):
        before=self.virtual;start=self.position
        result=super().action(path,point,channel)
        if self.episode is not None and self.episode.get("awaiting_endpoint") and tuple(point)==self.episode["endpoint"]:
            arrival=before+math.dist(start,point)/5
            self.close_episode("arrived",arrival-self.episode["start_virtual_s"])
        return result

    def close_episode(self,status,cost=None):
        if self.episode is None:
            return
        record=dict(self.episode,status=status,actual_to_endpoint_s=cost)
        if cost is not None:
            record["upper_minus_actual_s"]=record["selected_upper_s"]-cost
        self.episodes.append(record);self.emit("episode_finished",**record)
        self.episode=None

    def search_needed(self):
        return bool(self.remaining and self.unknown and len(self.discovered)<16)

    def next_route(self):
        route=open_route(self.position,self.remaining)
        revision=(len(self.visited),len(self.cleared))
        # Proof work is bounded independently of scan quota and never creates an
        # extra request. A new real scan/clear is needed before proposing again.
        if self.visited and self.unknown and revision!=self.last_tail_revision and self.tail_proof_calls<16:
            self.last_tail_revision=revision
            route,diagnostic=revise_route(self.position,self.visited,route,self.problem,
                                         min(2,16-self.tail_proof_calls))
            self.tail_proof_calls+=diagnostic["proofs_attempted"]
            self.tail_edits.append(diagnostic);self.emit("residual_route_revision",**diagnostic)
            self.remaining=list(route)
        return route

    def select_episode(self,route):
        q=route[0];t=route[1] if len(route)>1 else None
        if not self.anchors:
            return None
        # With only one scan left, finish a source then scan it. This removes
        # the otherwise ambiguous free endpoint from the comparison entirely.
        short=sorted(self.anchors,key=lambda c:terminal_upper(self._belief(c),self.anchors[c],self.position,self.problem,q)[0])[:3]
        plans=[]
        for c in short:
            self.refine_actions(c,[q,t],t)
            b=self._belief(c);a=self.anchors[c]
            now=terminal_upper(b,a,self.position,self.problem,q)[0]
            if t is None:
                plans.append(dict(channel=c,order="finish_then_scan",first_scan=q,
                                  endpoint=q,selected_upper_s=now+11*len(self.unknown),read=False))
                continue
            # Both policies include the same global batch at q and end at t.
            # <= 6 per unknown RF + <= 5 for each possible same-point near clear.
            scan_upper=11*len(self.unknown)
            now+=math.dist(q,t)/5+scan_upper
            later=terminal_upper(b,a,q,self.problem,t)[0]
            forecast=self._forecast(c,q,t)
            read=forecast is not None and forecast["upper_s"]<later-1e-6
            if read:
                later=forecast["upper_s"]
            later+=math.dist(self.position,q)/5+scan_upper
            selected=now<=later
            plan=dict(channel=c,order="finish_then_scan" if selected else "scan_then_finish",
                      first_scan=q,endpoint=t,now_upper_s=now,later_upper_s=later,
                      selected_upper_s=min(now,later),read=read and not selected,
                      scan_upper_s=scan_upper,comparison="same_endpoint_policy_upper_bounds")
            plans.append(plan);self.lookahead_decisions+=1
        return min(plans,key=lambda p:(p["selected_upper_s"],p["channel"]))

    def episode_read(self,c,q,target):
        self.stage="shared_measure"
        reply=self.action("/measure",q,c)
        self.optional_counts[c]+=1;self.optional_positions[c].append(tuple(q))
        self.shared_by_lookahead+=1
        if reply["measure_result"]=="near":
            self.clear(q,c)
        elif reply["measure_result"]=="direction":
            if self.anchors[c].rounds!=0:
                raise ModelMismatch("Shared measurement after contraction began")
            bound=max(math.dist(q,v) for v in self.regions[c])+SAFE
            self.anchors[c]=Anchor(tuple(q),reply["svd_deg"],min(1000,bound),0)
            self.regions[c]=constrain(self.regions[c],self.anchors[c],annular=True)
            self.record_positive(c,q)
        elif self.problem==3:
            raise ModelMismatch("Guaranteed shared reception failed")
        else:
            self.directions[c].negative(q,self.positives[c])
        self.stage="search"

    def execute_episode(self,plan):
        c=plan["channel"];q=plan["first_scan"];t=plan["endpoint"]
        self.episode=dict(plan,start_virtual_s=self.virtual,awaiting_endpoint=False)
        self.emit("episode_committed",**self.episode)
        if plan["order"]=="finish_then_scan":
            self.route_target=q;self.approach(c)
            if self.search_needed():
                self.scan(q)
        else:
            self.scan(q)
            self.route_target=t
            if plan["read"] and c in self.anchors:
                self.episode_read(c,q,t)
            if c in self.anchors:
                self.approach(c)
        if t==q:
            # Last-stop policy includes the complete batch, not just its arrival.
            if q in self.visited and tuple(self.position)==tuple(q):
                self.close_episode("arrived",self.virtual-self.episode["start_virtual_s"])
            else:
                self.close_episode("endpoint_cancelled_search_no_longer_needed")
        elif self.search_needed() and t in self.remaining:
            self.episode["awaiting_endpoint"]=True
            self.scan(t)  # No source insertion or route rewrite before t.
        else:
            self.close_episode("endpoint_cancelled_search_no_longer_needed")

    def improved_clear(self,c,position,target):
        # Execute the exact feasible terminal alternative used by the bound.
        bound,q=terminal_upper(self._belief(c),self.anchors[c],position,self.problem,target)
        return (q,"forecast_feasible_terminal") if q is not None else (None,None)

    def approach(self,channel):
        self._belief(channel)
        self.stage="localize"
        while channel not in self.cleared:
            self.refine_actions(channel,list(annular_points(self.anchors[channel],self.position))+[self.route_target],self.route_target)
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

    def run(self):
        self.started=time.monotonic();reply=self.io.call("/enter");self.entered=True
        self.virtual=reply["virtual_time_s"];self.max_virtual=reply["max_virtual_duration_s"]
        self.deadline=self.started+reply["remaining_real_duration_s"];self.io.deadline=self.deadline
        self.reason="running"
        try:
            while self.anchors or self.search_needed():
                route=self.next_route() if self.search_needed() else []
                if not route:
                    if self.anchors:
                        self.route_target=None
                        self.approach(min(self.anchors,key=lambda c:terminal_upper(self._belief(c),self.anchors[c],self.position,self.problem)[0]))
                        continue
                    break
                plan=self.select_episode(route)
                if plan is None:
                    self.scan(route[0])
                else:
                    self.execute_episode(plan)
                if self.search_needed():
                    self.certify_unknown()
            if self.anchors or self.discovered!=self.cleared:
                raise ModelMismatch("Uncleared discovered sources remain")
            if not 10<=len(self.discovered)<=16:
                raise ModelMismatch("Completion contradicts source-count interval")
            if len(self.discovered)==16:
                self.completion_basis="source_count_upper_bound"
            elif not self.remaining:
                self.completion_basis="proved_coverage_schedule"
            elif self.unknown:
                raise ModelMismatch("Unresolved unknown channels remain")
            self.absent.update(self.unknown);self.unknown.clear()
            self.certificate=True;self.reason="complete_with_certificate"
        except BudgetStop as exc:
            self.reason=str(exc);self.close_episode("budget_interrupted")
        self.exit();return self.summary()

    def summary(self):
        result=super().summary()
        result.update(strategy=STRATEGY,route_episodes=self.episodes,tail_route_edits=self.tail_edits,
                      tail_proof_calls=self.tail_proof_calls,action_refinements=self.refinement_decisions,
                      pending_route_episode=self.episode)
        return result
