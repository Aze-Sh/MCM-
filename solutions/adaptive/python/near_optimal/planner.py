"""Bounded event rollout and verified continuous optical proposals.

Costs here rank a finite candidate family, not the continuous problem optimum.
Every radio outcome bin is an OUTER region. Optical continuations cover all
remaining responsibility cells, including after an adverse radio response.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import time
from posterior import nearest_clear_point
from routing import improve_clear_route
from . import geometry as g
from .state import intersection


@dataclass(frozen=True)
class Event:
    kind: str
    channel: int
    points: tuple
    estimate: float
    method: str


def continuous_clear(source, current, target=None):
    polygon = [g.floating(p) for p in source.polygon]
    candidate = nearest_clear_point(polygon, current)
    if candidate is None:
        return None
    options = [candidate]
    if target is not None:
        q, _ = improve_clear_route(polygon, 19.8-1e-6, candidate, current, target)
        options.append(q)
    valid = [g.point(q) for q in options if g.disk_contains(source.polygon,g.point(q),F('19.8'))]
    if not valid:
        return None
    return min(valid,key=lambda q: math.dist(current,g.floating(q)) +
               (math.dist(g.floating(q),target) if target is not None else 0))


def optical_order(source, current, mode='snake', cells=None):
    ids = set(source.cells if cells is None else cells)
    if mode == 'snake':
        return [source.points[i] for i in sorted(ids)]
    order = [];p = g.point(current)
    while ids:
        i = min(ids,key=lambda i:(g.squared(p,source.points[i]),i))
        ids.remove(i);p = source.points[i];order.append(p)
    return order


def chain_bound(points, current, target=None):
    p = g.point(current);spent = F(0);worst = F(0)
    for q in points:
        spent += g.ceil_distance(p,q)/5
        leave = g.ceil_distance(q,g.point(target))/5 if target is not None else 0
        worst = max(worst,spent+5+leave)
        spent += 3;p = q
    return math.nextafter(float(worst),math.inf)


def continuations(source, current, cells=None):
    """Two complete, fixed optical continuations; min of genuine upper bounds."""
    return min((chain_bound(order,current),mode,order) for mode in ('snake','nearest')
               if (order:=optical_order(source,current,mode,cells)))


def pair_points(source, current, fraction=.5):
    # Original positive anchor stays valid after an atomic negative pair.
    length = F(source.anchor_radius)
    x = 5+(length-5)*F(fraction)
    points = [g.rotated_point(source.anchor_point,source.anchor_bearing,x,sign*length/50)
              for sign in (-1,1)]
    return tuple(sorted(points,key=lambda q:g.squared(q,g.point(current))))


def possible_cells(source, polygon):
    if not polygon:
        return []
    return [i for i,cell in source.cells.items() if intersection(cell,polygon)]


def radio_rollout(source, current, pair, problem, deadline):
    """One full RF event, then two complete optical continuations.

    Six closed 60-degree observation intervals cover all direction outputs.
    Impossible outcomes may remain: this weakens the bound, never removes a
    legal world. A time limit discards the entire unfinished candidate.
    """
    a,b = pair;start = float(g.ceil_distance(g.point(current),a)/5)+6
    worst = 0.;branches = 0
    def positive_and_near(q, prefix, poly):
        nonlocal worst,branches
        for lo in range(0,360,60):
            if time.perf_counter() >= deadline:
                raise TimeoutError('Incomplete radio outcome expansion')
            region = g.apply_bearing(poly,q,F(lo),hi=F(lo+60))
            ids = possible_cells(source,region)
            if ids:
                upper,_,_ = continuations(source,q,ids)
                worst = max(worst,prefix+upper);branches += 1
        # Including an impossible near response is a harmless relaxation.
        worst = max(worst,prefix+5);branches += 1
    positive_and_near(a,start,source.polygon)
    if problem == 3:
        # A negative is impossible only when the entire outer region is in
        # the minimum reception disk. Otherwise retain its full continuation.
        if not g.disk_contains(source.polygon,a,F(1000)):
            worst = max(worst,start+continuations(source,a)[0]);branches += 1
    else:
        prefix = start+float(g.ceil_distance(a,b)/5)+5
        positive_and_near(b,prefix,source.polygon)
        region,_ = g.verified_pair_cut(source.polygon,source.anchor_point,a,b)
        ids = possible_cells(source,region)
        if ids:
            worst = max(worst,prefix+continuations(source,b,ids)[0]);branches += 1
    return worst,branches


class Planner:
    def __init__(self, seconds=.20):
        if not math.isfinite(seconds) or seconds<0:
            raise ValueError('Invalid planning budget')
        self.seconds = seconds
        self.statistics = dict(decisions=0,rollout_candidates=0,rollout_timeouts=0,
                               continuous_clears=0,radio_events=0)

    def source_event(self, source, channel, current, tuned, extra, target=None):
        q = continuous_clear(source,current,target)
        if q is not None:
            self.statistics['continuous_clears'] += 1
            return Event('clear',channel,(q,),math.dist(current,g.floating(q))/5+5,'verified_continuous')
        upper,mode,order = continuations(source,current)
        best = Event('clear',channel,(order[0],),upper,'complete_optical_'+mode)
        if extra<2 or source.anchor_radius<=5 or source.rounds>=12:
            return best
        deadline = time.perf_counter()+self.seconds
        for fraction in (.5,.38,.62):
            pair = pair_points(source,current,fraction)
            try:
                value,branches = radio_rollout(source,current,pair,self.problem,deadline)
            except TimeoutError:
                self.statistics['rollout_timeouts'] += 1
                break
            self.statistics['rollout_candidates'] += 1
            if value < best.estimate:
                best = Event('radio',channel,pair,value,f'interval_rollout_{fraction:g}_{branches}_branches')
        # An annular event remains a useful candidate when the conservative
        # interval relaxation cannot prove an improvement. Its selection is
        # heuristic, and is bounded by the independent global allowance.
        if best.kind == 'clear' and len(source.cells)>4:
            pair = pair_points(source,current)
            best = Event('radio',channel,pair,best.estimate,'annular_proposal_with_guard')
        self.statistics['radio_events'] += best.kind=='radio'
        return best

    def choose(self, ledger, current, tuned, search_points):
        """Two-event travel lookahead across known services and search events.

        Only event ranking uses representative centers. They are never evidence
        and never provide a reported bound. Future unknown sources remain in
        Ledger.remaining_upper, independent of this finite ranking problem.
        """
        self.statistics['decisions'] += 1;self.problem = ledger.problem
        jobs = []
        for c in sorted(ledger.pending):
            source = ledger.channels[c].source
            p = tuple(sum(float(v[k]) for v in source.polygon)/len(source.polygon) for k in (0,1))
            jobs.append(('source',c,p))
        searches = []
        for q in search_points:
            todo = [c for c in ledger.unknown if g.point(q) not in ledger.channels[c].radio]
            if todo:
                searches.append(('search',min(todo,key=lambda c:(c!=tuned,c)),q))
        searches = searches[:1]  # First stop of a complete open 2-opt route.
        jobs += searches
        if not jobs:
            return None
        # A finite two-event ranking proxy. Complete, certified continuation
        # values are computed inside source_event and the global budget guard.
        def rank(job):
            first = math.dist(current,job[2])/5
            rest = [j for j in jobs if j!=job]
            second = min((math.dist(job[2],j[2])/5 for j in rest),default=0)
            service = 5 if job[0]=='source' else 6*len(ledger.unknown)
            return first + .35*second + service, job[0],job[1]
        job = min(jobs,key=rank)
        if job[0]=='search':
            return Event('search',job[1],(g.point(job[2]),),rank(job)[0],'two_event_search')
        target = min((j[2] for j in jobs if j!=job),key=lambda p:math.dist(job[2],p),default=None)
        return self.source_event(ledger.channels[job[1]].source,job[1],current,tuned,ledger.extra,target)
