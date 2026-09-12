"""Minimize movement subject to a certified analytic diameter target."""
import heapq
import math
from q2_design import diameter_bound,strip_bound,optimize_angle,EPS


def minimum_movement(target=163.,max_nodes=6000,tolerance=.1):
    seed=optimize_angle(900.)
    if seed['diameter_upper_m']>target:
        seed=optimize_angle(999.)
    if seed['diameter_upper_m']>target:
        raise ValueError('No initial feasible design for this target; choose a larger diameter target')
    best=(seed['movement_m'],math.atan2(seed['b_m'],seed['a_m']),seed['diameter_upper_m'])
    heap=[];serial=0;nodes=0
    def add(r0,r1,t0,t1):
        nonlocal serial
        r1=min(r1,2000*math.cos(t0+EPS));t1=min(t1,math.acos(r0/2000)-EPS)
        if r0>=r1 or t0>=t1 or r0>=best[0]:return
        distances=[]
        for r in (5.,1500.):
            rho=max(r0,min(r1,r*math.cos(t0+EPS)))
            distances.append(math.sqrt(max(0.,r*r+rho*rho-2*r*rho*math.cos(t0+EPS))))
        lb=strip_bound(max(distances),r1*math.sin(t1-EPS))-1e-6
        if lb>target:return
        serial+=1;heapq.heappush(heap,(r0,serial,(r0,r1,t0,t1)))
    add(5.0001,best[0],EPS+1e-8,math.pi/2-EPS-1e-8)
    stopped_lower=None
    while heap and nodes<max_nodes:
        lower,_,(r0,r1,t0,t1)=heapq.heappop(heap)
        if best[0]-lower<=tolerance:
            stopped_lower=lower;break
        if lower>=best[0]:continue
        nodes+=1;rm=(r0+r1)/2;tm=(t0+t1)/2
        for rho,theta in ((rm,tm),(r1,tm),(rm,min(t1,max(t0,best[1])))):
            if rho<best[0] and rho<1000 and theta<=math.acos(rho/2000)-EPS:
                bound=diameter_bound(rho,theta)[0]
                if bound<=target-1e-5:best=(rho,theta,bound)
        if (r1-r0)/1000>(t1-t0)/(math.pi/2):
            add(r0,rm,t0,t1);add(rm,r1,t0,t1)
        else:
            add(r0,r1,t0,tm);add(r0,r1,tm,t1)
    lower=min([best[0]]+([stopped_lower] if stopped_lower is not None else [])+[x[0] for x in heap])
    rho,theta,bound=best;a,b=rho*math.cos(theta),rho*math.sin(theta)
    return dict(movement_m=rho,a_m=a,b_m=b,diameter_upper_m=bound,target_diameter_m=target,
                movement_lower_m=lower,movement_gap_m=rho-lower,nodes=nodes,
                reception_margin_m=1000-max(rho,max(math.dist((a,b),(1000*math.cos(EPS),s*1000*math.sin(EPS))) for s in (-1,1))),
                scope='global_movement_bound_for_the_analytic_strip_criterion_not_exact_physical_diameter')
