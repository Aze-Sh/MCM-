"""Bounded route improvement and certified optical endgame candidates."""
import math
from strategy import CLEAR_RADIUS, EPSILON_RAD


def route_length(start,points,end=None):
    path=[start]+list(points)+([] if end is None else [end])
    return sum(math.dist(a,b) for a,b in zip(path,path[1:]))


def open_route(start,points,end=None):
    """Keep original and nearest-neighbour seeds, then bounded open 2-opt."""
    if len(points)<2:
        return list(points)
    remaining=list(points);greedy=[];p=start
    while remaining:
        q=min(remaining,key=lambda q:(math.dist(p,q),q))
        greedy.append(q);remaining.remove(q);p=q
    order=min((list(points),greedy),key=lambda qs:route_length(start,qs,end))
    for _ in range(8):
        best_delta,best_pair=0.,None
        for i in range(len(order)-1):
            a=start if i==0 else order[i-1]
            for j in range(i+1,len(order)):
                b=order[j+1] if j+1<len(order) else end
                before=math.dist(a,order[i]);after=math.dist(a,order[j])
                if b is not None:
                    before+=math.dist(order[j],b);after+=math.dist(order[i],b)
                if after-before<best_delta-1e-8:
                    best_delta,best_pair=after-before,(i,j)
        if best_pair is None:
            break
        i,j=best_pair;order[i:j+1]=reversed(order[i:j+1])
    return order


def attachment(start,route,point):
    """Cheapest insertion leg including a free final endpoint; heuristic."""
    costs=[];previous=start
    for i,next_point in enumerate(route):
        costs.append((math.dist(previous,point)+math.dist(point,next_point)-math.dist(previous,next_point),i))
        previous=next_point
    costs.append((math.dist(previous,point),len(route)))
    return min(costs)


def fallback_bound(anchor,position,problem,target=None,polygon=None):
    """Conservative time bound for uninterrupted v3 annular completion."""
    L=anchor.bound;travel=math.dist(position,anchor.point);rounds=0
    while L>44.5:
        if problem==3:
            travel+=.501*L+2.5;L=.502*L-2.4
        else:
            travel+=1.042*L+5;L=.502*L+2.505
        rounds+=1
    travel+=L+CLEAR_RADIUS
    cost=travel/5+5*rounds*(1 if problem==3 else 2)+6
    if target is not None:
        cost+=(max(math.dist(v,target) for v in polygon)+CLEAR_RADIUS)/5
    return cost


def rectangle_chain(polygon,angle):
    """At most three equal disks covering an enclosing oriented rectangle."""
    u=(math.cos(angle),math.sin(angle));v=(-u[1],u[0])
    xs=[p[0]*u[0]+p[1]*u[1] for p in polygon]
    ys=[p[0]*v[0]+p[1]*v[1] for p in polygon]
    lo,hi=min(xs)-1e-6,max(xs)+1e-6
    mid=(min(ys)+max(ys))/2;w=(max(ys)-min(ys))/2+1e-6
    radius=CLEAR_RADIUS-1e-5
    if w>=radius:
        return None
    half=math.sqrt(radius*radius-w*w)
    count=max(1,math.ceil((hi-lo)/(2*half)))
    if count>3:
        return None
    coords=[(lo+hi)/2] if count==1 else [lo+half+(hi-lo-2*half)*i/(count-1) for i in range(count)]
    return [(x*u[0]+mid*v[0],x*u[1]+mid*v[1]) for x in coords]


def optical_plan(anchor,polygon,position,problem,target=None):
    """Compare certified disk covers against a fallback upper bound, not its realized cost."""
    angle=math.radians(anchor.bearing)
    # Either enclosure suffices independently. No unproved rectangle intersection.
    a=anchor.point;u=(math.cos(angle),math.sin(angle));v=(-u[1],u[0])
    sector=[]
    for x in (5*math.cos(EPSILON_RAD),anchor.bound):
        for y in (-anchor.bound*math.sin(EPSILON_RAD),anchor.bound*math.sin(EPSILON_RAD)):
            sector.append((a[0]+x*u[0]+y*v[0],a[1]+x*u[1]+y*v[1]))
    candidates=[]
    for enclosure in (polygon,sector):
        for theta in (angle,angle+math.pi/2):
            chain=rectangle_chain(enclosure,theta)
            if chain is None:
                continue
            for points in (chain,list(reversed(chain))):
                elapsed=0.;previous=position;costs=[]
                for i,q in enumerate(points):
                    elapsed+=math.dist(previous,q)/5
                    costs.append(elapsed+3*i+5+(math.dist(q,target)/5 if target is not None else 0))
                    previous=q
                candidates.append((max(costs),points))
    if not candidates:
        return None
    value,points=min(candidates,key=lambda item:item[0])
    upper=fallback_bound(anchor,position,problem,target,polygon)
    if value>=upper-1e-6:
        return None
    return dict(points=points,worst_time_s=value,fallback_upper_s=upper)
