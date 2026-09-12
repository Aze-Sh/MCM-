"""Truth-free evidence ledger. Only accepted observations enter this module."""
from dataclasses import dataclass, field
from fractions import Fraction as F
import math
from . import geometry as g


class EvidenceError(RuntimeError):
    pass


def intersection(poly, other):
    if len(other)<3:
        return poly  # Retaining an outer cell is safe for degenerate clippers.
    for a,b in zip(other,other[1:]+other[:1]):
        edge = g.sub(b,a)
        normal = edge[1],-edge[0]
        poly = g.clip(poly,normal,g.dot(normal,a))
        if not poly:
            break
    return poly


@dataclass
class Source:
    origin: tuple
    bearing: float | None
    points: dict = field(default_factory=dict)
    cells: dict = field(default_factory=dict)
    polygon: list = field(default_factory=list)
    positives: list = field(default_factory=list)
    negatives: list = field(default_factory=list)
    anchor_point: tuple = ()
    anchor_bearing: float = 0.
    anchor_radius: float = 1500.
    rounds: int = 0

    @classmethod
    def found(cls, origin, bearing=None):
        origin = g.point(origin)
        obj = cls(origin,bearing,anchor_point=origin,anchor_bearing=bearing or 0.)
        domain = g.rectangle(-1800,-1800,1800,1800)
        if bearing is None:
            x,y = origin
            obj.polygon = intersection(g.rectangle(x-5,y-5,x+5,y+5),domain)
            obj.points = {0:origin};obj.cells = {0:obj.polygon}
            obj.anchor_radius = 5.
        else:
            obj.polygon = g.apply_bearing(domain,origin,F(bearing))
            index = 0
            for row,y in enumerate((-25,0,25)):
                for k in (range(61) if row%2==0 else range(60,-1,-1)):
                    x = 25*k
                    bounds = (max(0,x-F(25,2)),max(-30,y-F(25,2)),
                              min(1500,x+F(25,2)),min(30,y+F(25,2)))
                    cell = intersection(g.transformed_box(origin,bearing,bounds),obj.polygon)
                    q = g.rotated_point(origin,bearing,x,y)
                    if cell:
                        if not g.disk_contains(cell,q,F(20)):
                            raise EvidenceError("Optical responsibility is not covered")
                        obj.points[index],obj.cells[index] = q,cell
                    index += 1
        obj.positives.append(origin)
        obj._check()
        return obj

    def _check(self):
        if not self.polygon or not self.cells:
            raise EvidenceError("Known source lost all feasible responsibilities")

    def restrict(self, poly):
        if not poly:
            raise EvidenceError("Accepted evidence contradicts known source")
        self.cells = {i:out for i,p in self.cells.items() if (out:=intersection(p,poly))}
        self.polygon = poly
        self._check()

    def positive(self, q, bearing):
        q = g.point(q)
        self.restrict(g.apply_bearing(self.polygon,q,F(bearing)))
        self.positives.append(q)
        self.anchor_point,self.anchor_bearing = q,bearing
        self.anchor_radius = min(1500.,math.nextafter(float(max(g.ceil_distance(q,v) for v in self.polygon)),math.inf))
        self.rounds += 1

    def near(self,q):
        q = g.point(q);x,y = q
        self.restrict(intersection(self.polygon,g.rectangle(x-5,y-5,x+5,y+5)))
        self.anchor_point = q
        # A square enclosing the 5 m disk is sufficient for a direct clear.
        self.anchor_radius = math.nextafter(float(max(g.ceil_distance(q,v) for v in self.polygon)),math.inf)

    def negative(self,q,problem):
        q = g.point(q)
        self.negatives.append(q)
        if problem == 3:
            poly = self.polygon
            for p in self.positives:
                # no_signal implies |s-q| > R >= |s-p|.
                poly = g.clip(poly,g.sub(q,p),(g.dot(q,q)-g.dot(p,p))/2)
            self.restrict(poly)
        self.cells = {i:p for i,p in self.cells.items()
                      if problem != 3 or not g.disk_contains(p,q,F(1000))}
        self._check()

    def negative_pair(self,positive,a,b):
        if positive not in self.positives or a not in self.negatives or b not in self.negatives:
            raise EvidenceError("Pair contraction lacks its observed evidence")
        poly,changed = g.verified_pair_cut(self.polygon,positive,a,b)
        if changed:
            self.restrict(poly)
            self.anchor_radius = min(self.anchor_radius,
                math.nextafter(float(max(g.ceil_distance(self.anchor_point,v) for v in poly)),math.inf))
        self.rounds += 1
        return changed

    def optical_failure(self,q):
        q = g.point(q)
        self.cells = {i:p for i,p in self.cells.items() if not g.disk_contains(p,q,F(20))}
        self._check()
        self.polygon = g.hull(v for p in self.cells.values() for v in p)

    def fallback_points(self):
        return [self.points[i] for i in sorted(self.cells)]

    def terminal_bound(self, position, target=None):
        """Maximum conditional cost of the remaining fixed optical chain."""
        p = g.point(position)
        spent = F(0)
        worst = F(0)
        for q in self.fallback_points():
            spent += g.ceil_distance(p,q)/5
            end = g.ceil_distance(q,g.point(target))/5 if target is not None else 0
            worst = max(worst,spent+5+end)
            spent += 3
            p = q
        return math.nextafter(float(worst),math.inf)


@dataclass
class Channel:
    status: str = "unknown"
    radio: list = field(default_factory=list)
    optical: list = field(default_factory=list)
    records: list = field(default_factory=list)
    pending: set = field(default_factory=lambda: set(g.search_grid()))
    source: Source | None = None
    proof: dict | None = None


class Ledger:
    def __init__(self, problem, extra_actions=640):
        if problem not in (3,4) or type(extra_actions) is not int or extra_actions < 0:
            raise ValueError("Invalid problem or extra action allowance")
        self.problem = problem
        self.channels = {c:Channel() for c in range(1,21)}
        self.extra_initial = self.extra = extra_actions
        self.receipts = []
        self.certificates = []

    @property
    def unknown(self):
        return {c for c,s in self.channels.items() if s.status=="unknown"}

    @property
    def pending(self):
        return {c for c,s in self.channels.items() if s.status=="found"}

    @property
    def discovered(self):
        return {c for c,s in self.channels.items() if s.status in ("found","cleared")}

    @property
    def cleared(self):
        return {c for c,s in self.channels.items() if s.status=="cleared"}

    def potential(self):
        return (sum(len(s.pending) for s in self.channels.values() if s.status=="unknown")
                +sum(len(s.source.cells) for s in self.channels.values() if s.status=="found")
                +183*(16-len(self.discovered))+self.extra)

    def absent(self,c,basis,**details):
        s = self.channels[c]
        if s.status != "unknown":
            raise EvidenceError("Cannot mark a discovered source absent")
        s.status = "absent";s.pending.clear()
        s.proof = dict(channel=c,basis=basis,**details)
        self.certificates.append(s.proof)

    def certify(self,c,max_nodes=4096):
        s = self.channels[c]
        if s.status != "unknown":
            return False
        if not s.pending:
            self.absent(c,"exact_600m_grid_template",radio_count=len(s.radio))
            return True
        if len(s.radio)<(6 if self.problem==3 else 7) and not s.optical:
            return False
        proved,nodes,box,leaves = g.coverage_certificate(tuple(sorted(set(s.radio))),
                    tuple(sorted(set(s.optical))),self.problem,max_nodes)
        if proved:
            # Exact certificate consists of the deterministic input points and
            # subdivision settings. It can be replayed independently.
            self.absent(c,"rational_continuous_coverage",radio_count=len(s.radio),
                        optical_count=len(s.optical),nodes=nodes,leaf_count=len(leaves),
                        max_nodes=max_nodes,radio=[g.floating(q) for q in s.radio],
                        optical=[g.floating(q) for q in s.optical])
        return proved

    def observe(self,path,q,c,reply,prove=True):
        """Call only after accepted response validation and exact cost checking."""
        before = self.potential()
        q = g.point(q);s = self.channels[c]
        if s.status in ("cleared","absent"):
            raise EvidenceError("Action targets a resolved channel")
        kind = reply["measure_result" if path=="/measure" else "clear_result"]
        s.records.append(dict(path=path,point=g.floating(q),kind=kind,
                              bearing=reply.get("svd_deg")))
        if path == "/measure":
            if s.status == "unknown":
                if kind == "no_signal":
                    s.radio.append(q);s.pending.discard(q)
                    if prove:
                        self.certify(c)
                else:
                    s.status = "found";s.pending.clear()
                    s.source = Source.found(q,reply["svd_deg"] if kind=="direction" else None)
            elif kind == "direction":
                s.source.positive(q,reply["svd_deg"])
            elif kind == "near":
                s.source.near(q)
            else:
                s.source.negative(q,self.problem)
        elif kind == "success":
            s.status = "cleared";s.pending.clear();s.source = None
        elif s.status == "unknown":
            s.optical.append(q)
            if prove:
                self.certify(c)
        else:
            s.source.optical_failure(q)
        if len(self.discovered)>16:
            raise EvidenceError("More than 16 distinct sources")
        if len(self.discovered)==16:
            for other in sorted(self.unknown):
                self.absent(other,"source_count_upper_bound")
        if self.potential() >= before:
            if self.extra <= 0:
                raise EvidenceError("An unproductive action had no reserved allowance")
            self.extra -= 1
        after = self.potential()
        if after >= before or after < 0:
            raise EvidenceError("Completion rank failed to decrease")
        receipt = dict(before=before,after=after,extra_remaining=self.extra,
                       channel=c,path=path,result=kind)
        self.receipts.append(receipt)
        return receipt

    def complete(self):
        return not self.unknown and not self.pending and 10<=len(self.cleared)<=16

    def fallback_action(self,position):
        p = g.point(position)
        if self.pending:
            c = min(self.pending,key=lambda c: self.channels[c].source.terminal_bound(p))
            s = self.channels[c].source
            return "/clear",g.floating(s.fallback_points()[0]),c
        if self.unknown:
            q = next(q for q in g.search_grid()
                     if any(q in self.channels[c].pending for c in self.unknown))
            c = min(c for c in self.unknown if q in self.channels[c].pending)
            return "/measure",g.floating(q),c
        raise EvidenceError("No fallback action and no valid completion")

    def remaining_upper(self,position):
        """One complete policy, with virtual returns to current position.

        Known sources: fixed optical chains. Unknown sources: remaining grid,
        immediate optical completion on discovery, then continue the grid.
        No undiscovered-source cost is omitted.
        """
        p = g.point(position)
        components = [self.channels[c].source.terminal_bound(p,p) for c in self.pending]
        points = set(q for c in self.unknown for q in self.channels[c].pending)
        previous = p
        for q in g.search_grid():
            if q in points:
                components.append(math.nextafter(float(g.ceil_distance(previous,q)/5),math.inf))
                previous = q
        requests = sum(len(self.channels[c].pending) for c in self.unknown)
        components.append(6*requests)
        # 1770 ideal + 73 for <=1 m point errors; another .1 s covers all
        # outward millimetre rounding in a 183-point chain and its return.
        components.append(math.nextafter(1843.1*min(16-len(self.discovered),len(self.unknown)),math.inf))
        return math.nextafter(math.fsum(components),math.inf)

    def summary(self):
        return dict(discovered_channels=sorted(self.discovered),cleared_channels=sorted(self.cleared),
                    unknown_channels=sorted(self.unknown),pending_channels=sorted(self.pending),
                    absent_channels=[c for c,s in self.channels.items() if s.status=="absent"],
                    extra_actions_remaining=self.extra,completion_rank=self.potential(),
                    rank_receipts=len(self.receipts),absence_certificates=self.certificates)
