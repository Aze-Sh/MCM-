"""Stronger witness bounds and continuous refinement of certified disk covers."""
import math
from geometry import hull
from posterior import clip, nearest_clear_point
from routing import improve_clear_route
from strategy import CLEAR_RADIUS
from decision import optical_cover as finite_cover, chain_cost


def disk_visit_lower(position,x,target=None,radius=20.):
    """Convex supporting-plane dual bounds, never a numerical primal minimum.

    Every iterate z gives f(z)+g.(x-z)-r*||g|| <= min_{B(x,r)} f.
    Retaining the largest valid lower bound makes early termination harmless.
    """
    if target is None:
        return max(0.,math.dist(position,x)-radius)
    lower=max(math.dist(position,target),math.dist(position,x)+math.dist(target,x)-2*radius)
    z=x
    for iteration in range(24):
        d1=math.dist(z,position);d2=math.dist(z,target)
        g=tuple((z[i]-position[i])/d1 if d1>1e-12 else 0. for i in (0,1))
        g=tuple(g[i]+((z[i]-target[i])/d2 if d2>1e-12 else 0.) for i in (0,1))
        norm=math.hypot(*g)
        dual=d1+d2+sum(g[i]*(x[i]-z[i]) for i in (0,1))-radius*norm
        lower=max(lower,dual-1e-6)
        if norm<1e-12:
            break
        vertex=tuple(x[i]-radius*g[i]/norm for i in (0,1))
        # Feasible Frank-Wolfe iterates; convergence is not needed for validity.
        step=2/(iteration+2)
        z=tuple((1-step)*z[i]+step*vertex[i] for i in (0,1))
    return max(0.,lower)


def cost_witnesses(belief,position,target=None,limit=12):
    seeds=belief.witnesses(limit)
    found={tuple(w["point"]):w for w in seeds}
    def objective(p):
        return disk_visit_lower(position,p,target)
    # Cost-directed candidates are spread across all components. Each proposed
    # world is rechecked against raw observations; a polygon alone is not proof.
    for poly in belief.polygons():
        center=tuple(sum(v[i] for v in poly)/len(poly) for i in (0,1))
        extreme=max(poly,key=objective)
        for alpha in (1.,.999,.9,.5):
            p=tuple(alpha*extreme[i]+(1-alpha)*center[i] for i in (0,1))
            if (w:=belief.witness(p)) is not None:
                found[p]=w
    ranked=sorted(found.values(),key=lambda w:objective(w["point"]),reverse=True)[:4]
    vertices=[v for p in belief.polygons() for v in p]
    for w in ranked:
        p=w["point"];direction=max(vertices,key=objective)
        for alpha in (.5,.75,.875,.9375,.96875,.984375,.9921875):
            candidate=tuple((1-alpha)*p[i]+alpha*direction[i] for i in (0,1))
            if objective(candidate)>objective(p) and (new:=belief.witness(candidate)) is not None:
                found[candidate]=new
    return sorted(found.values(),key=lambda w:objective(w["point"]),reverse=True)[:limit]


def rf_lower_bound(belief,position,target=None,switch_cost=0):
    witnesses=cost_witnesses(belief,position,target)
    lower=0. if target is None else math.dist(position,target)
    lower=max([lower]+[disk_visit_lower(position,w["point"],target) for w in witnesses])
    return dict(lower_s=10+switch_cost+lower/5,witness_count=len(witnesses),
                scope="all_measure_first_single_source_policies_to_same_target",
                lower_method="validated_cost_witnesses_and_disk_supporting_planes")


def voronoi_atoms(polygons,centers):
    groups=[[] for _ in centers]
    for poly in polygons:
        for i,q in enumerate(centers):
            part=poly
            for j,r in enumerate(centers):
                if i==j:
                    continue
                nx,ny=r[0]-q[0],r[1]-q[1]
                part=clip(part,nx,ny,(r[0]**2+r[1]**2-q[0]**2-q[1]**2)/2)
            if part:
                groups[i].extend(part)
    return groups


def refine_centers(polygons,centers,position,target=None):
    """Continuous feasible-coordinate improvement of the max-prefix cost.

    Voronoi pieces partition every continuous polygon. Each retained piece is
    entirely in its assigned disk, before and after each centre modification.
    """
    centers=list(centers);groups=voronoi_atoms(polygons,centers)
    safety=CLEAR_RADIUS-1e-6
    if any(not points or max(math.dist(q,v) for v in points)>safety
           for q,points in zip(centers,groups)):
        return centers,0
    improvement=0.
    for _ in range(3):
        changed=False
        for i,points in enumerate(groups):
            poly=hull(points);old=centers[i]
            previous=position if i==0 else centers[i-1]
            after=target if i+1==len(centers) else centers[i+1]
            candidates=[nearest_clear_point(poly,p) for p in (position,previous,target,after) if p is not None]
            if after is not None:
                q,_=improve_clear_route(poly,safety,old,previous,after)
                candidates.append(q)
            before=chain_cost(centers,position,target)
            best=(before,old)
            for q in candidates:
                if q is None or max(math.dist(q,v) for v in points)>safety:
                    continue
                # Full max-prefix objective, not just adjacent-edge length.
                for alpha in (1.,.5,.25):
                    trial=tuple(old[k]+alpha*(q[k]-old[k]) for k in (0,1))
                    seq=centers[:i]+[trial]+centers[i+1:]
                    cost=chain_cost(seq,position,target)
                    if cost<best[0]-1e-7:
                        best=(cost,trial)
            if best[0]<before:
                centers[i]=best[1];improvement+=before-best[0];changed=True
        if not changed:
            break
    return centers,improvement


def optical_cover(belief,anchor,position,target=None,max_attempts=3):
    if max_attempts<1 or any(any(math.dist(a,b)>2*CLEAR_RADIUS*max_attempts
        for i,a in enumerate(p) for b in p[i+1:]) for p in belief.polygons()):
        return None
    baseline=finite_cover(belief,anchor,position,target,max_attempts)
    candidates=[] if baseline is None else [baseline]
    polygons=belief.polygons();poly=belief.hull()
    # Additional analytic partitions change the cover itself, rather than only
    # moving one of the old finite candidate points. All pieces are preserved.
    mean=tuple(sum(v[i] for v in poly)/len(poly) for i in (0,1))
    xx=sum((v[0]-mean[0])**2 for v in poly);yy=sum((v[1]-mean[1])**2 for v in poly)
    xy=sum((v[0]-mean[0])*(v[1]-mean[1]) for v in poly)
    principal=.5*math.atan2(2*xy,xx-yy)
    for angle in (principal,math.radians(anchor.bearing)):
        nx,ny=math.cos(angle),math.sin(angle)
        lo=min(nx*v[0]+ny*v[1] for v in poly);hi=max(nx*v[0]+ny*v[1] for v in poly)
        for count in range(2,max_attempts+1):
            chain=[]
            for i in range(count):
                a=lo+(hi-lo)*i/count;b=lo+(hi-lo)*(i+1)/count
                vertices=[]
                for p in polygons:
                    vertices.extend(clip(clip(p,nx,ny,b),-nx,-ny,-a))
                if not vertices:
                    continue
                q=nearest_clear_point(hull(vertices),position if not chain else chain[-1])
                if q is None:
                    break
                chain.append(q)
            else:
                for seq in (chain,list(reversed(chain))):
                    if seq:
                        candidates.append(dict(points=seq,worst_time_s=chain_cost(seq,position,target),certificate="continuous_slab_cover"))
    if not candidates:
        return None
    candidates.sort(key=lambda c:c["worst_time_s"])
    best=candidates[0]
    for candidate in candidates[:4]:
        centers,gain=refine_centers(polygons,candidate["points"],position,target)
        cost=chain_cost(centers,position,target)
        if cost<best["worst_time_s"]-1e-7:
            best=dict(points=centers,worst_time_s=cost,certificate="continuous_voronoi_piece_cover",
                      continuous_improvement_s=gain)
    return best


def optical_decision(belief,anchor,position,target=None,switch_cost=0):
    candidate=optical_cover(belief,anchor,position,target)
    if candidate is None:
        return None,dict(accepted=False,reason="no_three_disk_cover",optical_upper_s=None)
    lower=rf_lower_bound(belief,position,target,switch_cost)
    standalone=lower if target is None else rf_lower_bound(belief,position,None,switch_cost)
    standalone_upper=chain_cost(candidate["points"],position)
    gap=min(lower["lower_s"]-candidate["worst_time_s"],standalone["lower_s"]-standalone_upper)
    accepted=gap>1e-4
    diagnostic=dict(**lower,accepted=accepted,optical_upper_s=candidate["worst_time_s"],
                    standalone_rf_lower_s=standalone["lower_s"],standalone_optical_upper_s=standalone_upper,
                    dominance_gap_s=gap,reason="upper_below_rf_lower" if accepted else "bounds_overlap_keep_rf")
    return (candidate if accepted else None),diagnostic
