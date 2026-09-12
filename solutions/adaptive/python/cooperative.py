"""Certified finite v4: compact coverage, joint scheduling, shared observations.

Each source has at most two stationary optional readings, then the original
5/6-round completion method or a <=3-disk optical cover. No model simulator.
"""
from dataclasses import asdict
import math
import time
from coverage import design, certify
from evidence import disk_outer, outside_disk_hull, DirectionEvidence
from planning import open_route, route_length, attachment, optical_plan, fallback_bound
from posterior import initial_region, constrain, clear_choice, nearest_clear_point
from routing import improve_clear_route, two_leg
from solver import Solver, ModelMismatch, BudgetStop
from strategy import Anchor, annular_points, annular_update, annular_clear_disk, annular_clear_point, CLEAR_RADIUS

STRATEGY="certified-cooperative-v4"


class CooperativeSolver(Solver):
    def __init__(self,transport,problem,progress=None):
        super().__init__(transport,problem,progress,use_history=True)
        self.remaining=design(problem)
        self.scan_limit=len(self.remaining)
        self.positives={c:[] for c in range(1,21)}
        self.directions={c:DirectionEvidence() for c in range(1,21)}
        self.optional_counts={c:0 for c in range(1,21)}
        self.optional_positions={c:[] for c in range(1,21)}
        self.optical_probes=self.failed_clears=0
        self.replacements=0
        self.absent=set()
        self.coverage_diagnostics=[]
        self.completion_basis=None
        self.route_target=None
        self.deferred_decisions=0
        self.joint_clear_batches=0
        self.stage="search"
        self.stage_costs={key:dict(travel_m=0.,virtual_time_s=0.,measure_count=0,clear_count=0)
                          for key in ("search","shared_measure","localize","clear")}

    def budget(self,point):
        if time.monotonic()>=self.deadline-25:
            raise BudgetStop("real_time_reserve")
        if self.virtual+math.dist(self.position,point)/5+6>=self.max_virtual-1:
            raise BudgetStop("virtual_time_reserve")
        if self.measures+self.clear_attempts >= (300 if self.problem==3 else 772):
            raise ModelMismatch("v4 finite action bound exceeded")

    def action(self,path,point,channel):
        before=self.virtual;travel=self.travel
        result=super().action(path,point,channel)
        entry=self.stage_costs[self.stage]
        entry["virtual_time_s"]+=self.virtual-before
        entry["travel_m"]+=self.travel-travel
        entry["measure_count"]+=int(path=="/measure")
        entry["clear_count"]+=int(path=="/clear")
        return result

    def finish_clear(self,channel):
        self.cleared.add(channel)
        self.anchors.pop(channel,None);self.regions.pop(channel,None)
        self.emit("cleared",channel=channel,cleared_count=len(self.cleared))

    def clear(self,point,channel):
        previous=self.stage;self.stage="clear"
        reply=self.action("/clear",point,channel)
        self.stage=previous
        if reply["clear_result"]!="success":
            raise ModelMismatch(f"Certified clear failed for channel {channel}")
        self.finish_clear(channel)

    def record_positive(self,channel,point):
        if tuple(point) not in self.positives[channel]:
            self.positives[channel].append(tuple(point))
        self.regions[channel]=disk_outer(self.regions[channel],point,1500)
        self.apply_negative_history(channel,point)
        if self.problem==3:
            for negative in self.search_negatives[channel]:
                self.regions[channel]=outside_disk_hull(self.regions[channel],negative)
        self.refresh_history(channel)

    def scan(self,point):
        self.stage="search"
        if len(self.visited)>=self.scan_limit:
            raise ModelMismatch("Global scan quota exceeded")
        # A replacement point is appended only after proving its schedule covers D.
        for channel in sorted(self.unknown,key=lambda c:(c!=self.channel,c)):
            if len(self.discovered)==16:
                break
            reply=self.action("/measure",point,channel)
            if reply["measure_result"]=="no_signal":
                self.search_negatives[channel].append(tuple(point))
                continue
            self.discover(channel)
            if reply["measure_result"]=="near":
                self.clear(point,channel)
            else:
                self.anchors[channel]=Anchor(tuple(point),reply["svd_deg"])
                region=initial_region(self.anchors[channel],annular=True)
                self.regions[channel]=disk_outer(region,(0.,0.),1800,128)
                self.record_positive(channel,point)
                self.emit("discovered",channel=channel,bearing=reply["svd_deg"])
        self.remaining.remove(point);self.visited.append(tuple(point))
        self.emit("search_point_done",visited=len(self.visited),remaining=len(self.remaining))
        self.shared_measurements(point)

    def shared_measurements(self,point):
        self.stage="shared_measure"
        for channel in sorted(list(self.anchors),key=lambda c:(c!=self.channel,c)):
            if self.optional_counts[channel]>=2 or tuple(point) in self.positives[channel]+self.optional_positions[channel]:
                continue
            polygon=self.regions[channel]
            bound=max(math.dist(point,v) for v in polygon)+1e-6
            if bound>=1000-1e-5 or self.clear_plan(channel)[0] is not None:
                continue
            center=tuple(sum(v[i] for v in polygon)/len(polygon) for i in (0,1))
            a=(point[0]-center[0],point[1]-center[1]);norm=math.hypot(*a)
            if norm<1e-6:
                continue
            parallax=0.
            for old in self.positives[channel]:
                b=(old[0]-center[0],old[1]-center[1]);den=norm*math.hypot(*b)
                if den>1e-8:
                    parallax=max(parallax,abs(a[0]*b[1]-a[1]*b[0])/den)
            if parallax<math.sin(math.radians(15)):
                continue
            evidence=self.directions[channel]
            if evidence.directional and evidence.minimum_dot(point,polygon)<=1e-5:
                continue
            reply=self.action("/measure",point,channel)
            self.optional_counts[channel]+=1;self.optional_positions[channel].append(tuple(point))
            self.emit("shared_measure",channel=channel,result=reply["measure_result"],parallax_score=parallax)
            if reply["measure_result"]=="near":
                self.clear(point,channel)
            elif reply["measure_result"]=="direction":
                temporary=Anchor(tuple(point),reply["svd_deg"],bound)
                self.regions[channel]=constrain(polygon,temporary,annular=True)
                # Keep the old contraction anchor/counter. Extra evidence only tightens it.
                self.record_positive(channel,point)
            elif self.problem==3:
                raise ModelMismatch("In-range shared measurement lost omnidirectional signal")
            else:
                evidence.negative(point,self.positives[channel])
        self.stage="search"

    def improved_clear(self,channel,position,target):
        point,method=clear_choice(self.anchors[channel],self.regions[channel],position,annular=True)
        if point is None or target is None:
            return point,method
        options=[(point,method)]
        start=nearest_clear_point(self.regions[channel],position)
        if start is not None:
            q,_=improve_clear_route(self.regions[channel],CLEAR_RADIUS-1e-6,start,position,target)
            options.append((q,"history_route"))
        disk=annular_clear_disk(self.anchors[channel])
        if disk is not None:
            start=annular_clear_point(self.anchors[channel],position)
            q,_=improve_clear_route([disk[0]],disk[1],start,position,target)
            options.append((q,"anchor_route"))
        return min(options,key=lambda item:two_leg(item[0],position,target))

    def approach(self,channel):
        self.stage="localize"
        while channel not in self.cleared:
            anchor=self.anchors[channel]
            point,method=self.improved_clear(channel,self.position,self.route_target)
            if point is not None:
                self.emit("clear_planned",channel=channel,point=point,method=method)
                self.clear(point,channel)
                self.history_clears+=int(method.startswith("history"))
                return
            plan=optical_plan(anchor,self.regions[channel],self.position,self.problem,self.route_target)
            if plan is not None:
                self.emit("optical_cover_planned",channel=channel,**plan)
                self.stage="clear"
                for q in plan["points"]:
                    self.optical_probes+=1
                    reply=self.action("/clear",q,channel)
                    if reply["clear_result"]=="success":
                        self.finish_clear(channel)
                        return
                    self.failed_clears+=1
                    self.emit("optical_probe_negative",channel=channel,point=q)
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
                self.refresh_history(channel)
            self.emit("anchor_updated",channel=channel,anchor=asdict(self.anchors[channel]))

    def certify_unknown(self):
        if not self.unknown:
            return True
        # All remaining unknown channels received exactly the same global scans.
        channel=min(self.unknown)
        points=self.search_negatives[channel]
        if any(self.search_negatives[c]!=points for c in self.unknown):
            raise ModelMismatch("Unknown-channel evidence diverged")
        result=certify(points,self.problem)
        self.coverage_diagnostics.append(result)
        if result["proved"]:
            self.absent.update(self.unknown);self.unknown.clear()
            self.completion_basis="continuous_box_certificate"
            self.emit("unknown_channels_excluded",channels=sorted(self.absent),**result)
            return True
        return False

    def replacement_scan(self):
        if self.replacements>=2 or not self.remaining or not self.unknown or len(self.discovered)>=16:
            return
        p=self.position
        if any(math.dist(p,q)<1e-6 for q in self.visited):
            return
        route=open_route(p,self.remaining)
        for q in sorted(route,key=lambda q:math.dist(p,q))[:2]:
            without=[v for v in route if v!=q]
            saving=route_length(p,route)-route_length(p,without)
            if saving<=30*len(self.unknown):
                continue
            result=certify(self.visited+without+[p],self.problem,max_nodes=4096)
            if not result["proved"]:
                continue
            self.remaining.remove(q);self.remaining.append(p)
            self.replacements+=1
            self.emit("coverage_vertex_replaced",old=q,new=p,route_saving_m=saving,proof=result)
            self.scan(p)
            return

    def joint_clear(self,channels,target):
        """Bounded 2-opt order plus coordinate improvement; no global optimality claim."""
        candidates={c:self.clear_plan(c)[0] for c in channels}
        # Pair identity retained even if two channels share the same safe point.
        order=sorted(channels,key=lambda c:(math.dist(self.position,candidates[c]),c))
        points=[candidates[c] for c in order]
        for _ in range(4):
            old=route_length(self.position,points,target);best=None
            for i in range(len(order)-1):
                for j in range(i+1,len(order)):
                    trial=points[:i]+list(reversed(points[i:j+1]))+points[j+1:]
                    value=route_length(self.position,trial,target)
                    if value<old-1e-7:
                        old=value;best=(i,j)
            if best is None:
                break
            i,j=best;order[i:j+1]=reversed(order[i:j+1]);points[i:j+1]=reversed(points[i:j+1])
        for _ in range(2):
            for i,c in enumerate(order):
                previous=self.position if i==0 else points[i-1]
                after=points[i+1] if i+1<len(points) else target
                q,_=self.improved_clear(c,previous,after)
                if q is not None:
                    before=math.dist(previous,points[i])+(math.dist(points[i],after) if after is not None else 0)
                    cost=math.dist(previous,q)+(math.dist(q,after) if after is not None else 0)
                    if cost<=before:
                        points[i]=q
        self.joint_clear_batches+=1
        self.emit("joint_clear_planned",channels=order,points=points,target=target)
        for c,q in zip(order,points):
            self.clear(q,c)

    def choose_candidates(self,route):
        """v4 routing policy; v5 overrides this bounded scheduling hook."""
        candidates=[];ready=[]
        for c in self.anchors:
            q,_=self.clear_plan(c)
            polygon=self.regions[c]
            estimate=q if q is not None else tuple(sum(v[i] for v in polygon)/len(polygon) for i in (0,1))
            extra,leg=attachment(self.position,route,estimate)
            if leg==0:
                cost=fallback_bound(self.anchors[c],self.position,self.problem) if q is None else math.dist(self.position,q)/5+5
                candidates.append((cost,c))
                if q is not None:
                    ready.append(c)
        return candidates,ready

    def run(self):
        self.started=time.monotonic()
        reply=self.io.call("/enter");self.entered=True
        self.virtual=reply["virtual_time_s"];self.max_virtual=reply["max_virtual_duration_s"]
        self.deadline=self.started+reply["remaining_real_duration_s"];self.io.deadline=self.deadline
        self.reason="running"
        try:
            while self.remaining or self.anchors:
                search_needed=bool(self.remaining and self.unknown and len(self.discovered)<16)
                route=open_route(self.position,self.remaining) if search_needed else []
                self.route_target=route[0] if route else None
                candidates,ready=self.choose_candidates(route)
                if ready:
                    self.joint_clear(ready,self.route_target)
                    self.replacement_scan()
                    continue
                if candidates:
                    self.approach(min(candidates)[1])
                    self.replacement_scan()
                    continue
                if not search_needed:
                    break
                if self.anchors:
                    self.deferred_decisions+=1
                    self.emit("sources_deferred",channels=sorted(self.anchors),next_search=route[0])
                self.scan(route[0])
                if self.remaining and len(self.discovered)<16:
                    self.certify_unknown()
            if self.anchors or self.discovered!=self.cleared:
                raise ModelMismatch("Uncleared discovered sources remain")
            if not 10<=len(self.discovered)<=16:
                raise ModelMismatch("Completion contradicts source-count interval")
            if len(self.discovered)==16:
                self.completion_basis="source_count_upper_bound"
                self.absent.update(self.unknown);self.unknown.clear()
            elif not self.remaining:
                self.completion_basis="proved_coverage_schedule"
                self.absent.update(self.unknown);self.unknown.clear()
            elif self.unknown:
                raise ModelMismatch("Unresolved unknown channels remain")
            self.certificate=True;self.reason="complete_with_certificate"
        except BudgetStop as exc:
            self.reason=str(exc)
        self.exit()
        return self.summary()

    def summary(self):
        result=super().summary()
        # These v3 diagnostics do not describe v4's joint schedule.
        for key in ("route_planned_reduction_m","next_search_committed","history_clear_count"):
            result.pop(key,None)
        result.update(strategy=STRATEGY,completion_basis=self.completion_basis,
                      absent_channels=sorted(self.absent),optional_measure_counts=self.optional_counts,
                      optical_probe_count=self.optical_probes,failed_clear_count=self.failed_clears,
                      coverage_replacements=self.replacements,coverage_diagnostics=self.coverage_diagnostics,
                      deferred_decisions=self.deferred_decisions,joint_clear_batches=self.joint_clear_batches,
                      directional_channels=[c for c,e in self.directions.items() if e.directional],
                      stage_costs=self.stage_costs,action_bound=300 if self.problem==3 else 772)
        return result
