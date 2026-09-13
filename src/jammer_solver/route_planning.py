"""Bounded improvement of an open visiting route."""
import math


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
