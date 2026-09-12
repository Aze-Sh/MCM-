"""Shorten a complete future search plan with exact prospective certificates.

A certificate here says what the plan WOULD cover after executing its remaining
measurements. Only Ledger may certify absence from measurements already made.
"""
import time
from planning import open_route,route_length
from . import geometry as g


class SearchPlan:
    def __init__(self,points,seconds=.25):
        self.points = list(points);self.seconds = seconds
        self.signature = None;self.route = []
        self.proofs = self.deletions = self.replacements = 0
        self.pending_stop = None

    def propose_stop(self,q):
        self.pending_stop = tuple(q)

    def update(self,ledger,current):
        if not ledger.unknown:
            return []
        common = set.intersection(*(set(ledger.channels[c].radio) for c in ledger.unknown))
        remaining = [q for q in self.points if g.point(q) not in common]
        signature = (tuple(sorted(common)),tuple(sorted(ledger.unknown)),self.pending_stop)
        # Repositioning can change the route, but does not repeatedly release
        # more proof work for exactly the same search evidence.
        route = open_route(current,remaining)
        if signature==self.signature:
            return route
        self.signature = signature
        deadline = time.perf_counter()+self.seconds
        def cost(qs):
            return route_length(current,qs)/5+6*len(ledger.unknown)*len(qs)
        for _ in range(3):
            old = cost(route);options = []
            for q in route:
                rest = [p for p in route if p!=q]
                trial = open_route(current,rest)
                options.append((cost(trial),'delete',q,trial))
                if self.pending_stop is not None and self.pending_stop not in rest and g.point(self.pending_stop) not in common:
                    trial = open_route(current,rest+[self.pending_stop])
                    options.append((cost(trial),'replace',q,trial))
            improved = False
            for value,kind,removed,trial in sorted(options):
                if value>=old-1e-6 or time.perf_counter()>=deadline:
                    break
                self.proofs += 1
                points = tuple(sorted(common|{g.point(q) for q in trial}))
                proved = g.coverage_certificate(points,(),ledger.problem,4096)[0]
                if proved:
                    route = trial;improved = True
                    self.deletions += kind=='delete';self.replacements += kind=='replace'
                    break
            if not improved:
                break
        # All revisions are complete covers of common actual history + future
        # stops. No channel record or ledger responsibility is changed here.
        self.points = route
        self.route = route;self.pending_stop = None
        self.signature = (tuple(sorted(common)),tuple(sorted(ledger.unknown)),None)
        return route
