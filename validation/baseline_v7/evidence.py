"""Conservative circular refinement and independent orientation constraints."""
import math
from geometry import hull
from posterior import clip


def disk_outer(polygon,center,radius,sides=32):
    for i in range(sides):
        t=2*math.pi*i/sides;nx,ny=math.cos(t),math.sin(t)
        polygon=clip(polygon,nx,ny,nx*center[0]+ny*center[1]+radius)
    if not polygon:
        raise ArithmeticError("Circular evidence is inconsistent")
    return polygon


def outside_disk_hull(polygon,center,radius=1000-1e-5):
    """Outer convex hull after removing an open disk.

    Extreme points are surviving polygon vertices or edge/circle intersections;
    an interior concave circular boundary cannot expose a new hull extremum.
    The shrunk exclusion radius leaves a margin around strict negative evidence.
    """
    points=[p for p in polygon if math.dist(p,center)>=radius]
    if len(polygon)==1:
        if not points:
            raise ArithmeticError("Negative distance contradicts source region")
        return points
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1]
        ux,uy=a[0]-center[0],a[1]-center[1]
        aa=dx*dx+dy*dy
        if aa<=1e-24:
            continue
        bb=2*(ux*dx+uy*dy);cc=ux*ux+uy*uy-radius*radius
        disc=bb*bb-4*aa*cc
        if disc<0:
            continue
        root=math.sqrt(disc)
        for t in ((-bb-root)/(2*aa),(-bb+root)/(2*aa)):
            if 0<=t<=1:
                points.append((a[0]+t*dx,a[1]+t*dy))
    if not points:
        raise ArithmeticError("Negative distance contradicts source region")
    return hull(points)


class DirectionEvidence:
    def __init__(self):
        self.arcs=[(0.,2*math.pi)]
        self.directional=False

    def negative(self,q,positives):
        self.directional=True
        for p in positives:
            x,y=p[0]-q[0],p[1]-q[1]
            if math.hypot(x,y)<1e-8:
                raise ArithmeticError("Same-point positive and in-range negative")
            center=math.atan2(y,x)
            allowed=[]
            # Relax strict dot>0 outward in angle. Never exclude a true direction.
            for k in range(-2,3):
                lo=center-math.pi/2-1e-10+k*2*math.pi
                hi=center+math.pi/2+1e-10+k*2*math.pi
                for a,b in self.arcs:
                    if max(a,lo)<=min(b,hi):
                        allowed.append((max(a,lo),min(b,hi)))
            self.arcs=allowed
            if not self.arcs:
                raise ArithmeticError("Directional evidence is inconsistent")

    def minimum_dot(self,point,polygon):
        values=[]
        for vertex in polygon:
            x,y=point[0]-vertex[0],point[1]-vertex[1]
            minimum=math.atan2(y,x)+math.pi
            for lo,hi in self.arcs:
                candidates=[lo,hi]
                for k in range(-2,3):
                    t=minimum+k*2*math.pi
                    if lo<=t<=hi:
                        candidates.append(t)
                values.extend(x*math.cos(t)+y*math.sin(t) for t in candidates)
        return min(values)
