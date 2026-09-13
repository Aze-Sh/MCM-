"""Finite coverage designs and conservative continuous-domain certificates.

Subdivision proves whole boxes, never treats a point sample as domain coverage.
An unfinished proof returns unknown and leaves the guaranteed schedule intact.
"""
import math
from geometry import hull, cross


def design(problem):
    if problem == 3:
        return [(0.,0.)]+[(1125*math.cos(k*math.pi/3),1125*math.sin(k*math.pi/3)) for k in range(6)]
    if problem != 4:
        raise ValueError("problem must be 3 or 4")
    inner=[(990*math.cos(k*math.pi/4),990*math.sin(k*math.pi/4)) for k in range(8)]
    outer=[(1836*math.cos(k*math.pi/8),1836*math.sin(k*math.pi/8)) for k in range(16)]
    return [(0.,0.)]+inner+[outer[(14+k)%16] for k in range(16)]


def mesh():
    points=design(4)
    a=points[1:9]
    b=[(1836*math.cos(k*math.pi/8),1836*math.sin(k*math.pi/8)) for k in range(16)]
    triangles=[]
    for i in range(8):
        x,y=a[i],a[(i+1)%8]
        e,m,f=b[2*i],b[(2*i+1)%16],b[(2*i+2)%16]
        triangles.extend([[(0.,0.),x,y],[x,e,m],[x,m,y],[y,m,f]])
    return triangles


def contains_strict(polygon,point):
    if len(polygon)<3:
        return False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        edge=(b[0]-a[0],b[1]-a[1])
        if cross(edge,(point[0]-a[0],point[1]-a[1]))<=1e-5*math.hypot(*edge):
            return False
    return True


def certify(points,problem,max_nodes=2048,max_depth=13,domain_radius=1800.):
    """Return proved/unknown, work count and a region still unresolved.

    For q4, common nearby vertices surround all four box corners; convexity
    then covers the entire box with every source orientation. Positive margins
    are conservative engineering tolerances, not interval-arithmetic claims.
    """
    points=list(dict.fromkeys(tuple(p) for p in points))
    stack=[(-domain_radius,-domain_radius,domain_radius,domain_radius,0)]
    count=0
    while stack and count<max_nodes:
        x0,y0,x1,y1,depth=stack.pop()
        count+=1
        dx=max(x0,0.,-x1);dy=max(y0,0.,-y1)
        if math.hypot(dx,dy)>domain_radius+1e-5:
            continue
        corners=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        nearby=[q for q in points if max(math.dist(q,v) for v in corners)<1000-1e-5]
        if problem==3 and nearby:
            continue
        if problem==4 and len(nearby)>=3:
            polygon=hull(nearby)
            if all(contains_strict(polygon,v) for v in corners):
                continue
        if depth>=max_depth:
            return dict(proved=False,nodes=count,unresolved_box=[x0,y0,x1,y1])
        mx,my=(x0+x1)/2,(y0+y1)/2
        stack.extend([(x0,y0,mx,my,depth+1),(mx,y0,x1,my,depth+1),
                      (x0,my,mx,y1,depth+1),(mx,my,x1,y1,depth+1)])
    return dict(proved=not stack,nodes=count,
                unresolved_box=list(stack[-1][:4]) if stack else None)
