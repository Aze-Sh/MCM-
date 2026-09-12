"""Whole-outcome lookahead and optical plans gated by a valid RF lower bound."""
from dataclasses import replace
import math
from geometry import hull
from posterior import nearest_clear_point, clip
from strategy import annular_clear_point, CLEAR_RADIUS
from planning import fallback_bound, rectangle_chain, route_length
from joint_belief import EPS, SAFE, TAU, minimum_distance


def terminal_upper(belief,anchor,position,problem,target=None,allow_anchor_disk=True):
    poly=belief.hull()
    bound=min(anchor.bound,max(math.dist(anchor.point,v) for v in poly)+SAFE)
    tightened=replace(anchor,bound=max(5+SAFE,bound))
    best=fallback_bound(tightened,position,problem,target,poly)
    choices=[nearest_clear_point(poly,position)]
    if allow_anchor_disk:
        choices.append(annular_clear_point(tightened,position))
    if target is not None:
        choices.append(nearest_clear_point(poly,target))
    point=None
    for q in choices:
        if q is not None:
            value=math.dist(position,q)/5+5+(math.dist(q,target)/5 if target is not None else 0)
            if value<best:
                best,point=value,q
    return best,point


def output_intervals(poly,q,max_bins=12):
    if minimum_distance(poly,q)<SAFE:
        start,width=0.,TAU
    else:
        angles=sorted((math.atan2(v[1]-q[1],v[0]-q[0])%TAU) for v in poly)
        gaps=[(angles[(i+1)%len(angles)]-a)%TAU for i,a in enumerate(angles)]
        i=max(range(len(gaps)),key=lambda i:gaps[i])
        start=angles[(i+1)%len(angles)]-EPS
        width=TAU-gaps[i]+2*EPS
    count=min(max_bins,max(1,math.ceil(width/math.radians(4))))
    return [(start+i*width/count,start+(i+1)*width/count) for i in range(count)]


def measurement_envelope(belief,anchor,q,problem,target=None,measure_cost=6):
    """A finite upper envelope over ALL near/negative/bearing outcomes.

    Measurements must be in the minimum receive radius of every cell. Output
    intervals cover the entire possible bearing range; no probability or
    sampled hidden environment is used. Before local contraction has started,
    an actual positive reading may install a new <=1000 m anchor. No already
    consumed contraction round is reset.
    """
    poly=belief.hull()
    if max(math.dist(q,v) for v in poly)>=1000-SAFE:
        return None
    branches=[]
    if belief.outcome(q,"near") is not None:
        branches.append(dict(kind="near",upper_s=5+(math.dist(q,target)/5 if target is not None else 0)))
    negative=belief.outcome(q,"no_signal") if problem==4 else None
    if negative is not None:
        value,_=terminal_upper(negative,anchor,q,problem,target)
        branches.append(dict(kind="no_signal",upper_s=value))
    for lo,hi in output_intervals(poly,q):
        posterior=belief.outcome(q,"direction",(lo,hi))
        if posterior is not None:
            if anchor.rounds==0:
                bound=max(5+SAFE,max(math.dist(q,v) for v in posterior.hull())+SAFE)
                temporary=replace(anchor,point=tuple(q),bearing=math.degrees((lo+hi)/2)%360,
                                  bound=min(1500,bound))
                # Mid-bin angle is NOT an observed bearing. Only the
                # orientation-independent fallback bound may use this anchor.
                value,_=terminal_upper(posterior,temporary,q,problem,target,False)
            else:
                value,_=terminal_upper(posterior,anchor,q,problem,target)
            branches.append(dict(kind="direction",interval_rad=[lo,hi],upper_s=value))
    if not branches:
        raise ArithmeticError("Measurement has no geometrically possible response")
    return dict(upper_s=measure_cost+max(b["upper_s"] for b in branches),
                branches=branches,scope="whole_outcome_intervals")


def rf_lower_bound(belief,position,target=None,switch_cost=0):
    """Lower bound for EVERY policy that measures this source before clearing.

    Each accepted witness is a complete world satisfying all real observations.
    Even perfect information cannot avoid reaching a 20 m neighbourhood of it.
    Witnesses only improve a lower bound; they are never used as a coverage proof.
    """
    direct=0. if target is None else math.dist(position,target)
    travel=direct;witnesses=belief.witnesses()
    for witness in witnesses:
        x=witness["point"]
        lower=max(0.,math.dist(position,x)-20)
        if target is not None:
            lower+=max(0.,math.dist(target,x)-20)
        travel=max(travel,lower)
    return dict(lower_s=10+switch_cost+travel/5,witness_count=len(witnesses),
                scope="all_measure_first_single_source_policies_to_same_target")


def chain_cost(points,position,target=None):
    elapsed=0.;previous=position;worst=0.
    for i,q in enumerate(points):
        elapsed+=math.dist(previous,q)/5
        worst=max(worst,elapsed+3*i+5+(math.dist(q,target)/5 if target is not None else 0))
        previous=q
    return worst


def optical_cover(belief,anchor,position,target=None,max_attempts=3):
    """Best retained certificate among rectangles and a finite disk-cover search.

    Convex atoms preserve separated posterior components. Every atom must be
    wholly covered by at least one chosen disk; thus the finite search certifies
    the entire continuous union, not merely its vertices as unrelated samples.
    """
    if max_attempts<1:
        return None
    for component in belief.polygons():
        if any(math.dist(a,b)>2*CLEAR_RADIUS*max_attempts
               for i,a in enumerate(component) for b in component[i+1:]):
            # A convex component contains its longest segment. k disks cover
            # at most 2*k*r length along that segment, irrespective of centres.
            return None
    poly=belief.hull();angle=math.radians(anchor.bearing)
    mean=tuple(sum(v[i] for v in poly)/len(poly) for i in (0,1))
    xx=sum((v[0]-mean[0])**2 for v in poly);yy=sum((v[1]-mean[1])**2 for v in poly)
    xy=sum((v[0]-mean[0])*(v[1]-mean[1]) for v in poly)
    principal=.5*math.atan2(2*xy,xx-yy)
    best=None;points=[]
    def consider(chain,certificate):
        nonlocal best
        cost=chain_cost(chain,position,target)
        if best is None or cost<best["worst_time_s"]:
            best=dict(points=chain,worst_time_s=cost,certificate=certificate)
    for theta in (angle,angle+math.pi/2,principal):
        chain=rectangle_chain(poly,theta)
        if chain is not None and len(chain)<=max_attempts:
            consider(chain,"rectangle_cover");consider(list(reversed(chain)),"rectangle_cover")
            points.extend(chain)
    # Six spatial slabs permit the finite cover search to use different disks
    # for different portions of a long connected polygon, while retaining holes.
    nx,ny=math.cos(principal),math.sin(principal)
    lo=min(nx*v[0]+ny*v[1] for v in poly);hi=max(nx*v[0]+ny*v[1] for v in poly)
    atoms=[]
    for component in belief.polygons():
        pieces=[]
        for i in range(6):
            a=lo+(hi-lo)*i/6;b=lo+(hi-lo)*(i+1)/6
            piece=clip(clip(component,nx,ny,b),-nx,-ny,-a)
            if piece:
                pieces.append(piece)
        if len(atoms)+len(pieces)<=288:
            atoms.extend(pieces)
        else:
            # Resource cap keeps the unsplit component; no component is dropped.
            atoms.append(component)
    for atom in atoms:
        for p in (position,target):
            if p is not None:
                q=nearest_clear_point(atom,p)
                if q is not None:
                    points.append(q)
    points=list(dict.fromkeys(tuple(q) for q in points))
    masks=[]
    for q in points:
        mask=sum(1<<i for i,a in enumerate(atoms) if max(math.dist(q,v) for v in a)<CLEAR_RADIUS-1e-7)
        if mask:
            masks.append((q,mask))
    # Fixed finite candidate family, explicitly distinct from a global optimum.
    masks=sorted(masks,key=lambda qm:(-qm[1].bit_count()/(1+math.dist(position,qm[0])/100),qm[0]))[:14]
    full=(1<<len(atoms))-1;nodes=0
    def search(chain,covered,elapsed,worst):
        nonlocal nodes
        nodes+=1
        if covered==full:
            consider(chain,"continuous_atom_cover")
            return
        if len(chain)>=max_attempts:
            return
        previous=chain[-1] if chain else position
        for q,mask in masks:
            if mask|covered==covered:
                continue
            travel=elapsed+math.dist(previous,q)/5
            value=max(worst,travel+3*len(chain)+5+(math.dist(q,target)/5 if target is not None else 0))
            if best is not None and value>=best["worst_time_s"]-1e-8:
                continue
            search(chain+[q],covered|mask,travel,value)
    if masks and full:
        search([],0,0.,0.)
    if best is not None:
        best.update(atom_count=len(atoms),candidate_count=len(masks),search_nodes=nodes)
    return best


def optical_decision(belief,anchor,position,target=None,switch_cost=0):
    candidate=optical_cover(belief,anchor,position,target)
    if candidate is None:
        return None,dict(accepted=False,reason="no_three_disk_cover",optical_upper_s=None)
    lower=rf_lower_bound(belief,position,target,switch_cost)
    diagnostics=dict(**lower,optical_upper_s=None if candidate is None else candidate["worst_time_s"],
                     accepted=False,reason="no_three_disk_cover")
    gap=lower["lower_s"]-candidate["worst_time_s"]
    # Also require dominance for clearing alone: later route changes cannot
    # invalidate the decision solely by removing the planned outgoing leg.
    standalone=rf_lower_bound(belief,position,None,switch_cost)
    standalone_gap=standalone["lower_s"]-chain_cost(candidate["points"],position)
    gap=min(gap,standalone_gap)
    accepted=gap>1e-4
    diagnostics.update(accepted=accepted,dominance_gap_s=gap,
                       standalone_rf_lower_s=standalone["lower_s"],
                       standalone_optical_upper_s=chain_cost(candidate["points"],position),
                       reason="upper_below_rf_lower" if accepted else "bounds_overlap_keep_rf")
    return (candidate if accepted else None),diagnostics
