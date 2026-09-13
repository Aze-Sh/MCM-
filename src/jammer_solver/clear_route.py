"""Bounded convex descent for one clear followed by one committed search point.

No solver dependency or exploration. Each returned point is feasible and never
increases the fixed-target two-leg cost of its supplied feasible starting point.
The Frank-Wolfe gap is a numerical diagnostic, not an interval certificate.
"""
import math
from itertools import combinations
from .bearing_geometry import distance


def two_leg(point,current,target):
    return distance(current,point)+distance(point,target)


def improve_clear_route(centers,radius,start,current,target,max_steps=24):
    def feasible(p):
        return all(distance(p,c)<=radius+1e-10 for c in centers)
    if not centers or radius<=0 or not feasible(start):
        return start,dict(iterations=0,gap_m=None)
    corners = []
    for a,b in combinations(centers,2):
        d = distance(a,b)
        if d <= 1e-12 or d > 2*radius:
            continue
        mid = (a[0]+b[0])/2,(a[1]+b[1])/2
        h = math.sqrt(max(0.0,radius*radius-d*d/4))
        dx,dy = -(b[1]-a[1])*h/d,(b[0]-a[0])*h/d
        for p in ((mid[0]+dx,mid[1]+dy),(mid[0]-dx,mid[1]-dy)):
            if feasible(p):
                corners.append(p)
    point,steps,gap = start,0,None
    for _ in range(max_steps):
        value = two_leg(point,current,target)
        if value-distance(current,target)<=1e-7:
            gap = max(0.0,value-distance(current,target))
            break
        d1,d2 = distance(point,current),distance(point,target)
        if min(d1,d2)<=1e-12:
            gap=0.0
            break
        g = ((point[0]-current[0])/d1+(point[0]-target[0])/d2,
             (point[1]-current[1])/d1+(point[1]-target[1])/d2)
        norm = math.hypot(*g)
        if norm<=1e-12:
            gap=None
            break
        candidates = corners+[point]
        for c in centers:
            candidate = c[0]-radius*g[0]/norm,c[1]-radius*g[1]/norm
            if feasible(candidate):
                candidates.append(candidate)
        support = min(candidates,key=lambda p:g[0]*p[0]+g[1]*p[1])
        gap = max(0.0,g[0]*(point[0]-support[0])+g[1]*(point[1]-support[1]))
        if gap<=1e-5:
            break
        # Along a feasible chord the objective is convex. Fixed work, no sweep.
        def interpolate(t):
            return point[0]+t*(support[0]-point[0]),point[1]+t*(support[1]-point[1])
        lo,hi=0.0,1.0
        for _ in range(36):
            left,right=(2*lo+hi)/3,(lo+2*hi)/3
            if two_leg(interpolate(left),current,target)<=two_leg(interpolate(right),current,target):
                hi=right
            else:
                lo=left
        candidate=min((point,support,interpolate((lo+hi)/2)),key=lambda p:two_leg(p,current,target))
        if not feasible(candidate):
            break
        improvement=value-two_leg(candidate,current,target)
        point=candidate
        steps+=1
        gap=None  # Previous gradient gap does not describe the new iterate.
        if improvement<=1e-9:
            break
    return point,dict(iterations=steps,gap_m=gap)
