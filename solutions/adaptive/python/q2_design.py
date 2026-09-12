"""Q2 deterministic one-dimensional optimization with analytic error bounds.

The movement radius is a user-selected budget spent from the first detector.
Branch bounds cover the full feasible angle interval; no hidden arenas sampled.
"""
import heapq
import math
from strategy import EPSILON_RAD as EPS


def diameter_bound(rho,theta):
    """Upper diameter of the physical two-bearing compatible set."""
    a,b=rho*math.cos(theta),rho*math.sin(theta)
    distance=max(math.sqrt(r*r+rho*rho-2*r*rho*math.cos(theta+EPS)) for r in (5.,1500.))
    cross_height=b*math.cos(EPS)-a*math.sin(EPS)
    return strip_bound(distance,cross_height),distance


def strip_bound(distance,height):
    sine=max(0.,min(1.,height/max(distance,1e-12)))
    gamma=math.asin(sine)-2*EPS
    if gamma<=0:
        return math.inf
    w1,w2=1500*math.sin(EPS),distance*math.sin(EPS)
    # Exact longest diagonal of the two enclosing strip intersection.
    return 2*math.sqrt(w1*w1+w2*w2+2*w1*w2*math.cos(gamma))/math.sin(gamma)


def optimize_angle(rho,tolerance=.02,max_nodes=1024):
    if not 5<rho<1000:
        raise ValueError("A positive reception margin requires 5 < movement < 1000")
    lo=EPS+1e-8;hi=math.acos(rho/2000)-EPS-1e-8
    def evaluate(theta):
        return diameter_bound(rho,theta)[0]
    def lower(a,b):
        # D(theta) is increasing on this interval, h(theta)=rho*sin(theta-EPS)
        # is increasing, and strip_bound increases with D and decreases with h.
        d=diameter_bound(rho,a)[1]
        h=rho*math.sin(b-EPS)
        return max(0.,strip_bound(d,h)-1e-6)
    best=min((evaluate(t),t) for t in (lo,(lo+hi)/2,hi))
    heap=[(lower(lo,hi),lo,hi)];nodes=0;pruned_lower=math.inf
    while heap and nodes<max_nodes:
        lb,a,b=heapq.heappop(heap)
        if best[0]-lb<=tolerance:
            pruned_lower=min(pruned_lower,lb);break
        mid=(a+b)/2
        for x,y in ((a,mid),(mid,b)):
            t=(x+y)/2;value=evaluate(t);nodes+=1
            if value<best[0]:
                best=(value,t)
            bound=lower(x,y)
            if bound<best[0]:
                heapq.heappush(heap,(bound,x,y))
            else:
                pruned_lower=min(pruned_lower,bound)
    lower_bound=min(best[0],pruned_lower,min((entry[0] for entry in heap),default=math.inf))
    bound,theta=best;a,b=rho*math.cos(theta),rho*math.sin(theta)
    endpoint=max(math.dist((a,b),(1000*math.cos(EPS),s*1000*math.sin(EPS))) for s in (-1,1))
    return dict(movement_m=rho,a_m=a,b_m=b,diameter_upper_m=bound,
                angle_family_lower_m=lower_bound,optimization_gap_m=bound-lower_bound,
                reception_margin_m=1000-max(rho,endpoint),nodes=nodes,
                scope="entire_feasible_angle_interval_at_fixed_movement_radius")


def report():
    radii=(600.,800.,math.hypot(750,600),999.)
    return dict(old_point=dict(a_m=750,b_m=600,movement_m=radii[2],
                               diameter_upper_m=diameter_bound(radii[2],math.atan2(600,750))[0]),
                movement_error_frontier=[optimize_angle(r) for r in radii],
                recommended_900m=optimize_angle(900.),
                note="Bounds on physical compatible-set diameter; optimization gap concerns this analytic bound at fixed radius, not exact minimax diameter.")


if __name__=="__main__":
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report(),ensure_ascii=False,indent=2),encoding='utf-8')
