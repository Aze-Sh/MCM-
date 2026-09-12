"""All outstanding obligations share one directed, bounded service graph.

Every source is serviced once in every compared plan. A radio mode enters at
its first actual probe, not at a fictional return to the discovery anchor.
Exit polygons bound the true completion position, rather than point estimates.
"""
from dataclasses import dataclass
import math
from strategy import annular_points, annular_update, annular_clear_point
from posterior import nearest_clear_point
from planning import fallback_bound, open_route
from probe_frontier import guaranteed_probes


@dataclass
class Mode:
    job: tuple
    kind: str
    entry: tuple
    service_s: float
    exit_vertices: list
    exit_radius: float=0.
    first_probe: tuple | None=None
    anchor: object=None

    def departure(self,target):
        return (max(math.dist(v,target) for v in self.exit_vertices)+self.exit_radius)/5


def radio_modes(channel,anchor,polygon,problem):
    if anchor.bound<=44.5:
        return []
    pair=annular_points(anchor,anchor.point);modes=[]
    for q,other in (pair,pair[::-1]):
        # Bearing zero here is only a placeholder: fallback_bound uses no angle.
        positive=annular_update(anchor,q,0.)
        first=max(5.,fallback_bound(positive,q,problem)-1.)
        if problem==4:
            second=annular_update(anchor,other,0.)
            hidden=annular_update(anchor)
            after_second=max(5.,fallback_bound(second,other,problem)-1.,
                             fallback_bound(hidden,other,problem)-1.)
            first=max(first,math.dist(q,other)/5+5+after_second)
        modes.append(Mode(('source',channel),'radio',q,6+first,polygon,20.,q,anchor))
    return modes


def assignment(cost):
    """Square minimum assignment via primal-dual potentials, O(n^3)."""
    n=len(cost);u=[0.]*(n+1);v=[0.]*(n+1);p=[0]*(n+1);way=[0]*(n+1)
    for i in range(1,n+1):
        p[0]=i;j0=0;minimum=[float('inf')]*(n+1);used=[False]*(n+1)
        while True:
            used[j0]=True;i0=p[j0];delta=float('inf');j1=0
            for j in range(1,n+1):
                if not used[j]:
                    cur=cost[i0-1][j-1]-u[i0]-v[j]
                    if cur<minimum[j]:minimum[j]=cur;way[j]=j0
                    if minimum[j]<delta:delta=minimum[j];j1=j
            for j in range(n+1):
                if used[j]:u[p[j]]+=delta;v[j]-=delta
                else:minimum[j]-=delta
            j0=j1
            if p[j0]==0:break
        while True:
            j1=way[j0];p[j0]=p[j1];j0=j1
            if j0==0:break
    successor=[0]*n
    for j in range(1,n+1):successor[p[j]-1]=j-1
    return sum(cost[i][j] for i,j in enumerate(successor)),successor


def source_modes(channel,anchor,polygon,problem,position,targets=(),belief=None):
    points=[]
    for target in [position,anchor.point]+list(targets)[:2]:
        q=nearest_clear_point(polygon,target)
        if q is not None:
            points.append(q)
        q=annular_clear_point(anchor,target)
        if q is not None:
            points.append(q)
    points=list(dict.fromkeys(tuple(q) for q in points))
    if points:
        return [Mode(('source',channel),'clear',q,5.,[q]) for q in points[:4]]
    modes=radio_modes(channel,anchor,polygon,problem)
    if belief is not None:
        for probe in guaranteed_probes(belief,anchor,position):
            mode=Mode(('source',channel),'regional_probe',probe['point'],probe['service_s'],polygon,20.,anchor=anchor)
            mode.probe_bound=probe['bound'];modes.append(mode)
    return modes


class ServiceGraph:
    def __init__(self,position,jobs):
        self.position=tuple(position);self.jobs=jobs
        self.modes=[m for variants in jobs.values() for m in variants]
        self.ids={job:[i for i,m in enumerate(self.modes) if m.job==job] for job in jobs}
        self.index={id(m):i for i,m in enumerate(self.modes)}
        self.edge={(i,j):a.departure(b.entry)+b.service_s
                   for i,a in enumerate(self.modes) for j,b in enumerate(self.modes) if a.job!=b.job}
        self.start={i:math.dist(position,m.entry)/5+m.service_s for i,m in enumerate(self.modes)}
        self.evaluations=0

    def evaluate(self,order):
        """Exact mode DP for one fixed job order, with a free final endpoint."""
        self.evaluations+=1
        if not order:
            return 0.,[]
        costs={i:(self.start[i],[i]) for i in self.ids[order[0]]}
        for job in order[1:]:
            costs={j:min((v+self.edge[i,j],path+[j]) for i,(v,path) in costs.items()) for j in self.ids[job]}
        value,path=min(costs.values())
        return value,[self.modes[i] for i in path]

    def optimize(self,incumbent=(),passes=3):
        if not self.jobs:
            return dict(upper_s=0.,modes=[],order=[],evaluations=0,baseline_upper_s=0.)
        # Complete any old plan before comparing it: new obligations are never
        # dropped merely because they were absent from the previous prediction.
        old=[j for j in incumbent if j in self.jobs]
        old+= [j for j in self.jobs if j not in old]
        seeds=[old]
        remaining=list(self.jobs);greedy=[];last=None
        while remaining:
            job=min(remaining,key=lambda j:min(self.start[i] if last is None else self.edge[last,i] for i in self.ids[j]))
            last=min(self.ids[job],key=lambda i:self.start[i] if last is None else self.edge[last,i])
            greedy.append(job);remaining.remove(job)
        seeds.append(greedy)
        scans=[j for j in self.jobs if j[0]=='scan'];sources=[j for j in self.jobs if j[0]=='source']
        seeds.extend((sources+scans,scans+sources))
        lower,patched=self.assignment_seed()
        seeds.append(patched)
        baseline=self.evaluate(old)[0]
        evaluated=[]
        for seed in seeds:
            v,m=self.evaluate(seed);evaluated.append((v,seed,m))
        value,order,modes=min(evaluated,key=lambda e:e[0])
        for _ in range(passes):
            before=value;trials=[];n=len(order)
            # Mode choices are reoptimized for every candidate order. No local
            # improvement relies on treating uncertain source exits as centres.
            for i in range(n):
                for j in range(n):
                    if i==j:
                        continue
                    trial=list(order);item=trial.pop(i);trial.insert(j,item)
                    # Cheap current-mode edge score only shortlists candidates;
                    # the complete directed mode DP decides actual acceptance.
                    chosen={m.job:self.index[id(m)] for m in modes};seq=[chosen[k] for k in trial]
                    score=self.start[seq[0]]+sum(self.edge[a,b] for a,b in zip(seq,seq[1:]))
                    if score<value-1e-7:
                        trials.append((score,trial))
            for _,trial in sorted(trials,key=lambda x:x[0])[:16]:
                candidate,variants=self.evaluate(trial)
                if candidate<value-1e-7:
                    value,order,modes=candidate,trial,variants
            if value>=before-1e-7:
                break
        return dict(upper_s=value,modes=modes,order=order,evaluations=self.evaluations,
                    baseline_upper_s=baseline,assignment_lower_s=lower,
                    finite_graph_gap_s=max(0.,value-lower),
                    scope='all_current_known_jobs_same_obligations')

    def assignment_seed(self):
        jobs=list(self.jobs);n=len(jobs);cost=[[1e12]*(n+1) for _ in range(n+1)]
        for j,job in enumerate(jobs,1):cost[0][j]=min(self.start[k] for k in self.ids[job])
        for i,a in enumerate(jobs,1):
            cost[i][0]=0.
            for j,b in enumerate(jobs,1):
                if i!=j:cost[i][j]=min(self.edge[x,y] for x in self.ids[a] for y in self.ids[b])
        lower,successor=assignment(cost)
        def cycle(start):
            out=[start];q=successor[start]
            while q!=start:out.append(q);q=successor[q]
            return out
        main=cycle(0)
        while len(main)<n+1:
            other=cycle(next(i for i in range(n+1) if i not in main))
            a,b=min(((a,b) for a in main for b in other),
                    key=lambda ab:cost[ab[0]][successor[ab[1]]]+cost[ab[1]][successor[ab[0]]]
                                  -cost[ab[0]][successor[ab[0]]]-cost[ab[1]][successor[ab[1]]])
            successor[a],successor[b]=successor[b],successor[a];main=cycle(0)
        return max(0.,lower-1e-6),[jobs[i-1] for i in main[1:]]


def build_graph(solver,route,incumbent_modes=()):
    jobs={}
    for point in route:
        job=('scan',tuple(point))
        jobs[job]=[Mode(job,'scan',tuple(point),11.*len(solver.unknown),[tuple(point)])]
    targets=list(route[:2])
    for c in solver.anchors:
        belief=solver._belief(c)
        jobs['source',c]=source_modes(c,solver.anchors[c],belief.hull(),solver.problem,solver.position,targets,belief)
        for old in incumbent_modes:
            if old.job!=('source',c):continue
            if old.kind=='clear' or (old.anchor is not None and old.anchor.rounds==solver.anchors[c].rounds):
                # Historical modes remain valid under additional constraints;
                # retaining them keeps the old complete plan available.
                jobs['source',c].append(old)
        if not jobs['source',c]:
            raise ArithmeticError('Source has neither a clear mode nor a finite radio mode')
    return ServiceGraph(solver.position,jobs)
