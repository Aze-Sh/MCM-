"""Opt-in v8: event proposals behind an independent completion ledger."""
import math
import time
from protocol import validate_reply, UncertainAction
from strategy import search_points
from . import geometry as g
from .state import Ledger, EvidenceError
from .planner import Planner
from .search_plan import SearchPlan

STRATEGY = 'event-rollout-certified-completion-v8'


class SolverV8:
    def __init__(self, transport, problem, progress=None, *, extra_actions=640,
                 planning_seconds=.20, request_seconds=.10, fallback_only=False):
        if not math.isfinite(request_seconds) or request_seconds<=0:
            raise ValueError('A positive assumed request latency is required')
        self.io,self.problem,self.progress = transport,problem,progress
        self.ledger = Ledger(problem,extra_actions)
        self.planner = Planner(planning_seconds)
        self.request_seconds,self.fallback_only = request_seconds,fallback_only
        self.position,self.channel,self.virtual = (0.,0.),1,0.
        self.travel = 0.;self.measures = self.clear_attempts = self.switches = 0
        self.entered = self.exit_confirmed = self.exit_attempted = self.certificate = False
        self.reason = 'not_started';self.started = None
        self.deadline,self.max_virtual = math.inf,360000.
        self.fallback_used = False;self.initial_upper = None
        self.search_candidates = search_points(problem)
        self.search_plan = SearchPlan(self.search_candidates)
        self.guard_checks = 0

    def emit(self,event,**fields):
        data = dict(event=event,virtual_time_s=self.virtual,**fields)
        self.io.record(data)
        if self.progress:
            self.progress(data)

    def remaining_requests(self):
        l = self.ledger
        return (sum(len(l.channels[c].pending) for c in l.unknown)
                +sum(len(l.channels[c].source.cells) for c in l.pending)
                +183*min(16-len(l.discovered),len(l.unknown))+2)

    def guard(self,points):
        """All-feedback budget guard, including future undiscovered sources.

        Moving the common virtual-return point by d increases the complete
        fallback bound by at most (2m+1)d/5. Refinement only deletes tasks;
        discovery transfers one 1843.1 s future reserve to a shorter known job.
        Apply to the ENTIRE atomic event before its first request.
        """
        self.guard_checks += 1
        upper = self.ledger.remaining_upper(self.position)
        p = self.position;distance = 0.
        for q in points:
            distance += float(g.ceil_distance(g.point(p),g.point(q)))
            p = g.floating(q)
        m = min(16,len(self.ledger.pending)+len(points))
        virtual_ok = self.virtual+upper+(2*m+2)*distance/5+6*len(points)<self.max_virtual-2
        real_ok = time.monotonic()+(self.remaining_requests()+len(points))*self.request_seconds+30<self.deadline
        return virtual_ok and real_ok

    def action(self,path,q,c,*,prove=True):
        q = g.floating(g.point(q))
        if getattr(self.io,'pending',None) is not None:
            raise UncertainAction('Earlier request unresolved')
        if time.monotonic()>=self.deadline-2:
            raise TimeoutError('Real deadline reserve reached without completion')
        moved = math.dist(self.position,q)
        if self.virtual+moved/5+6>=self.max_virtual-1:
            raise EvidenceError('Physical action exceeds virtual budget')
        switching = int(path=='/measure' and c!=self.channel)
        reply = self.io.call(path,q,c)
        validate_reply(path,reply)
        before = self.virtual
        # An accepted action has physically executed, even on a later audit
        # failure. Do not pretend it can be rolled back or sent anew.
        self.position = q;self.virtual = reply['virtual_time_s'];self.travel += moved
        if path=='/measure':
            self.measures += 1;self.switches += switching;self.channel = c
            cost = 5+switching
        else:
            self.clear_attempts += 1
            cost = 5 if reply['clear_result']=='success' else 3
        if abs(self.virtual-before-moved/5-cost)>5e-5:
            raise EvidenceError('Accepted response violates documented virtual costs')
        discovered = c in self.ledger.discovered
        self.emit('evidence_observation',path=path,point=q,channel=c,reply=reply,prove=prove)
        receipt = self.ledger.observe(path,q,c,reply,prove=prove)
        self.emit('rank_receipt',**receipt)
        if not discovered and c in self.ledger.discovered:
            self.emit('discovered',channel=c)
        if path=='/clear' and reply['clear_result']=='success':
            self.search_plan.propose_stop(q)
            self.emit('cleared',channel=c,cleared_count=len(self.ledger.cleared))
        return reply

    def execute_event(self,event):
        self.emit('event_selected',kind=event.kind,channel=event.channel,
                  points=[g.floating(q) for q in event.points],method=event.method,
                  candidate_estimate_s=event.estimate,
                  estimate_scope='candidate ranking; not a global optimality bound')
        if event.kind=='search':
            q = event.points[0]
            # A shared stop scans remaining channels. Each channel keeps its
            # own actual history, including interrupted batches.
            for c in sorted(self.ledger.unknown,key=lambda c:(c!=self.channel,c)):
                if c not in self.ledger.unknown or q in self.ledger.channels[c].radio:
                    continue
                if self.ledger.extra<1 or not self.guard((q,)):
                    return False
                self.action('/measure',q,c)
            return True
        if event.kind=='clear':
            self.action('/clear',event.points[0],event.channel)
            return True
        source = self.ledger.channels[event.channel].source
        positive = source.anchor_point
        a,b = event.points
        first = self.action('/measure',a,event.channel)
        if first['measure_result']=='no_signal' and self.problem==4:
            second = self.action('/measure',b,event.channel)
            if second['measure_result']=='no_signal':
                before = self.ledger.potential()
                changed = source.negative_pair(positive,a,b)
                self.emit('verified_negative_pair',channel=event.channel,changed=changed,
                          positive=g.floating(positive),a=g.floating(a),b=g.floating(b),
                          rank_before=before,rank_after=self.ledger.potential())
        return True

    def finish_source(self,c):
        # Freeze one complete optical continuation. Actual exclusions can skip
        # points but cannot create new responsibilities or restart the chain.
        source = self.ledger.channels[c].source
        order = [(i,source.points[i]) for i in sorted(source.cells)]
        for i,q in order:
            if c not in self.ledger.pending:
                return
            if i in source.cells:
                self.action('/clear',q,c,prove=False)
        if c in self.ledger.pending:
            raise EvidenceError('Constructive optical cover exhausted without success')

    def committed_fallback(self):
        self.fallback_used = True
        upper = self.ledger.remaining_upper(self.position)
        if self.virtual+upper>=self.max_virtual-1:
            raise EvidenceError('No certified completion fits the remaining virtual budget')
        self.emit('fallback_committed',remaining_upper_s=upper,
                  requests_upper=self.remaining_requests(),
                  real_time_condition=f'requires sufficient actual latency; assumed {self.request_seconds:g} s/request')
        origin = self.position
        known = sorted(self.ledger.pending,key=lambda c:self.ledger.channels[c].source.terminal_bound(origin,origin))
        for c in known:
            self.finish_source(c)
        # Preserve the order used by remaining_upper; triangle inequality pays
        # for virtual returns without issuing a movement-only action.
        for q in g.search_grid():
            for c in sorted(self.ledger.unknown,key=lambda c:(c!=self.channel,c)):
                if c not in self.ledger.unknown or q not in self.ledger.channels[c].pending:
                    continue
                self.action('/measure',q,c,prove=False)
                if c in self.ledger.pending:
                    self.finish_source(c)
            if self.ledger.complete():
                break
        # Template completion is exact even with proof subdivision disabled.
        for c in sorted(self.ledger.unknown):
            self.ledger.certify(c)
        if not self.ledger.complete():
            raise EvidenceError('Full fallback exhausted without a valid 10–16 source completion')

    def run(self):
        self.started = time.monotonic()
        reply = self.io.call('/enter');validate_reply('/enter',reply)
        self.entered = True;self.virtual = reply['virtual_time_s']
        self.max_virtual = reply['max_virtual_duration_s']
        self.deadline = time.monotonic()+reply['remaining_real_duration_s']
        self.io.deadline = self.deadline
        self.initial_upper = self.ledger.remaining_upper(self.position)
        self.reason = 'running'
        self.emit('v8_started',problem=self.problem,extra_actions=self.ledger.extra,
                  max_virtual_s=self.max_virtual)
        while not self.ledger.complete():
            if self.fallback_only or self.ledger.extra<2:
                self.committed_fallback();break
            if time.monotonic()+self.remaining_requests()*self.request_seconds+30>=self.deadline:
                self.committed_fallback();break
            search_route = self.search_plan.update(self.ledger,self.position)
            event = self.planner.choose(self.ledger,self.position,self.channel,search_route)
            if event is None or not self.guard(event.points):
                self.committed_fallback();break
            if not self.execute_event(event):
                self.committed_fallback();break
        self.certificate = self.ledger.complete()
        self.reason = 'certified_all_cleared' if self.certificate else 'incomplete'
        self.emit('completion_checked',certified=self.certificate)
        self.exit()
        return self.summary()

    def exit(self):
        if not self.entered or self.exit_attempted:
            return
        if getattr(self.io,'pending',None) is not None:
            raise UncertainAction('Cannot exit while earlier request is unresolved')
        self.exit_attempted = True
        reply = self.io.call('/exit');validate_reply('/exit',reply)
        if abs(reply['virtual_time_s']-self.virtual)>5e-5:
            raise EvidenceError('Exit unexpectedly changed virtual time')
        self.exit_confirmed = True

    def summary(self):
        return dict(strategy=STRATEGY,problem=self.problem,reason=self.reason,
                    completion_certified=self.certificate,exit_confirmed=self.exit_confirmed,
                    virtual_time_s=self.virtual,moving_distance_m=self.travel,
                    average_clear_time_s=self.virtual/len(self.ledger.cleared) if self.ledger.cleared else None,
                    measures=self.measures,clear_attempts=self.clear_attempts,switches=self.switches,
                    initial_fallback_upper_s=self.initial_upper,fallback_used=self.fallback_used,
                    budget_guard_checks=self.guard_checks,planner=self.planner.statistics,
                    search_plan=dict(proofs=self.search_plan.proofs,deletions=self.search_plan.deletions,
                                     replacements=self.search_plan.replacements),
                    real_time_guarantee='conditional on execution and request latency; not unconditional',
                    **self.ledger.summary())
