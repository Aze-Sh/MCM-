"""Finite outer unions of position polygons coupled to direction intervals.

All real observations are retained. A refinement that exceeds the cell budget
keeps its parent; it never discards a possible branch to meet a resource limit.
"""
from dataclasses import dataclass, replace
import math
from geometry import hull, cross
from posterior import clip

TAU=2*math.pi
EPS=math.radians(1.005)
SAFE=2e-5


def safe_disk_outer(polygon,q,radius):
    for i in range(32):
        t=i*TAU/32;nx,ny=math.cos(t),math.sin(t)
        polygon=clip(polygon,nx,ny,nx*q[0]+ny*q[1]+radius)
        if not polygon:
            break
    return polygon


def polygon_intersection(a,b):
    if len(b)<3:
        # Degenerate outer regions are rare; retaining a is conservative.
        return a
    for p,q in zip(b,b[1:]+b[:1]):
        dx,dy=q[0]-p[0],q[1]-p[1]
        length=math.hypot(dx,dy)
        if length>1e-12:
            a=clip(a,dy/length,-dx/length,(dy*p[0]-dx*p[1])/length)
    return a


def minimum_distance(polygon,point):
    if not polygon:
        return float("inf")
    # Clipping can leave almost identical consecutive vertices. A tiny edge
    # must not turn an interior point into a false "outside" classification.
    if len(polygon)>=3 and all(math.dist(a,b)<1e-10 or
        cross((b[0]-a[0],b[1]-a[1]),(point[0]-a[0],point[1]-a[1]))
        >=-1e-8*math.dist(a,b) for a,b in zip(polygon,polygon[1:]+polygon[:1])):
        return 0.
    best=min(math.dist(point,p) for p in polygon)
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
        if den>1e-24:
            t=max(0.,min(1.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/den))
            best=min(best,math.dist(point,(a[0]+t*dx,a[1]+t*dy)))
    return best


def subtract_disk(polygon,point,radius):
    """Outer union of P minus a disk, using an inscribed 32-gon.

    The removed polygon lies strictly inside the physical disk. Keeping its
    thin circular rim is conservative; unlike a convex hull, no entire hole
    is filled back in. Each returned piece is convex and ordered.
    """
    if not polygon:
        return []
    if max(math.dist(v,point) for v in polygon)<radius-SAFE:
        return []
    if minimum_distance(polygon,point)>=radius:
        return [polygon]
    bound=(radius-SAFE)*math.cos(math.pi/32)
    inside=polygon;pieces=[]
    for i in range(32):
        t=(2*i+1)*math.pi/32;nx,ny=math.cos(t),math.sin(t)
        b=nx*point[0]+ny*point[1]+bound
        outside=clip(inside,-nx,-ny,-b)
        if outside:
            pieces.append(outside)
        inside=clip(inside,nx,ny,b)
        if not inside:
            break
    return pieces


def bearing_clip(polygon,q,lo,hi):
    """A whole output-angle interval, expanded by the measurement error."""
    lo-=EPS;hi+=EPS
    if hi-lo>=math.pi:
        return polygon
    for nx,ny in ((math.sin(lo),-math.cos(lo)),(-math.sin(hi),math.cos(hi))):
        polygon=clip(polygon,nx,ny,nx*q[0]+ny*q[1])
    mid=(lo+hi)/2;nx,ny=-math.cos(mid),-math.sin(mid)
    return clip(polygon,nx,ny,nx*q[0]+ny*q[1]-5*math.cos((hi-lo)/2))


@dataclass
class Cell:
    polygon: list
    # None denotes an omnidirectional hypothesis, not an unknown direction.
    arc: tuple | None=None


def angle_plane(cell,q,visible):
    if cell.arc is None:
        return cell.polygon if visible else []
    lo,hi=cell.arc;mid=(lo+hi)/2
    nx,ny=math.cos(mid),math.sin(mid)
    # |n(theta)-n(mid)| <= 2 sin((hi-lo)/4), uniformly on this interval.
    radius=max(math.dist(q,v) for v in cell.polygon)
    margin=2*math.sin((hi-lo)/4)*radius+SAFE
    if visible:
        return clip(cell.polygon,nx,ny,nx*q[0]+ny*q[1]+margin)
    return clip(cell.polygon,-nx,-ny,-nx*q[0]-ny*q[1]+margin)


def definitely_in_range(polygon,q,positives):
    if max(math.dist(q,v) for v in polygon)<1000-SAFE:
        return True
    # R is also at least each previously observed positive distance.
    return any(min(math.dist(v,p)**2-math.dist(v,q)**2 for v in polygon)>SAFE
               for p in positives)


def range_branch(polygon,q,positives):
    for p in positives:
        d=math.dist(p,q)
        if d<1e-10:
            return []
        nx,ny=(q[0]-p[0])/d,(q[1]-p[1])/d
        mid=((p[0]+q[0])/2,(p[1]+q[1])/2)
        polygon=clip(polygon,nx,ny,nx*mid[0]+ny*mid[1])
        if not polygon:
            return []
    return subtract_disk(polygon,q,1000)


class JointBelief:
    def __init__(self,polygon,problem,records=(),max_cells=48):
        self.problem=problem;self.max_cells=max_cells
        self.cells=[Cell(polygon)]
        if problem==4:
            self.cells += [Cell(polygon,(i*TAU/8,(i+1)*TAU/8)) for i in range(8)]
        self.records=[];self.retained_parents=0
        for record in records:
            self.observe(record,refine=False)
        self.refine_angles()

    @classmethod
    def from_cells(cls,cells,problem,max_cells=48):
        obj=cls.__new__(cls);obj.problem=problem;obj.max_cells=max_cells
        obj.cells=cells;obj.records=[];obj.retained_parents=0
        return obj

    def positives(self):
        return [r["point"] for r in self.records if r["kind"] in ("direction","near")]

    def _replace_cells(self,operation):
        old=self.cells;out=[]
        for i,cell in enumerate(old):
            children=operation(cell)
            if len(out)+len(children)+len(old)-i-1>self.max_cells:
                out.append(cell);self.retained_parents+=1
            else:
                out.extend(children)
        self.cells=out
        if not out:
            raise ArithmeticError("Joint position-direction evidence is inconsistent")

    def observe(self,record,refine=True):
        self.records.append(record)
        q=record["point"];kind=record["kind"];positives=self.positives()
        def update(cell):
            poly=cell.polygon
            if kind=="direction":
                theta=math.radians(record["bearing"])
                poly=bearing_clip(poly,q,theta,theta)
                if not poly:
                    return []
                poly=safe_disk_outer(poly,q,1500)
                if not poly:
                    return []
                poly=angle_plane(replace(cell,polygon=poly),q,True)
                return [replace(cell,polygon=poly)] if poly else []
            if kind=="clear_failure":
                return [replace(cell,polygon=p) for p in subtract_disk(poly,q,20)]
            if kind=="no_signal":
                if definitely_in_range(poly,q,positives):
                    hidden=angle_plane(cell,q,False)
                    return [replace(cell,polygon=hidden)] if hidden else []
                pieces=range_branch(poly,q,positives)
                if cell.arc is not None:
                    hidden=angle_plane(cell,q,False)
                    if hidden:
                        pieces.append(hidden)
                return [replace(cell,polygon=p) for p in pieces]
            return [cell]
        self._replace_cells(update)
        if kind=="direction":
            # New positives raise the same source's unknown but fixed radius
            # lower bound. Revisit OLD negatives with all positive distances.
            for previous in self.records[:-1]:
                if previous["kind"]!="no_signal":
                    continue
                negative=previous["point"]
                def revisit(cell):
                    if definitely_in_range(cell.polygon,negative,positives):
                        p=angle_plane(cell,negative,False)
                        return [replace(cell,polygon=p)] if p else []
                    pieces=range_branch(cell.polygon,negative,positives)
                    if cell.arc is not None:
                        p=angle_plane(cell,negative,False)
                        if p:
                            pieces.append(p)
                    return [replace(cell,polygon=p) for p in pieces]
                self._replace_cells(revisit)
        if refine:
            self.refine_angles()

    def _contract_angles(self,cell):
        for r in self.records:
            if not cell.polygon:
                return None
            if r["kind"]=="direction":
                cell=replace(cell,polygon=angle_plane(cell,r["point"],True))
            elif r["kind"]=="no_signal" and definitely_in_range(cell.polygon,r["point"],self.positives()):
                cell=replace(cell,polygon=angle_plane(cell,r["point"],False))
        return cell if cell.polygon else None

    def refine_angles(self,max_splits=8):
        contracted=[self._contract_angles(c) for c in self.cells]
        self.cells=[c for c in contracted if c is not None]
        if not self.cells:
            raise ArithmeticError("No joint hypothesis remains")
        if not any(r["kind"]=="no_signal" for r in self.records):
            return
        for _ in range(max_splits):
            choices=[(c.arc[1]-c.arc[0],i) for i,c in enumerate(self.cells)
                     if c.arc is not None and c.arc[1]-c.arc[0]>math.pi/512]
            if not choices or len(self.cells)>=self.max_cells:
                break
            _,i=max(choices);c=self.cells[i];lo,hi=c.arc;mid=(lo+hi)/2
            children=[self._contract_angles(replace(c,arc=a)) for a in ((lo,mid),(mid,hi))]
            self.cells[i:i+1]=[c for c in children if c is not None]
            if not self.cells:
                raise ArithmeticError("Angular refinement removed every hypothesis")

    def intersect(self,polygon):
        self._replace_cells(lambda c:[replace(c,polygon=p)] if (p:=polygon_intersection(c.polygon,polygon)) else [])
        self.refine_angles()

    def polygons(self):
        unique={}
        for c in self.cells:
            unique.setdefault(tuple(c.polygon),c.polygon)
        return list(unique.values())

    def hull(self):
        return hull([v for c in self.cells for v in c.polygon])

    def outcome(self,q,kind,interval=None):
        """Outer posterior for every response in a whole interval, not a sample."""
        cells=[]
        for c in self.cells:
            poly=c.polygon
            if kind=="direction":
                poly=bearing_clip(poly,q,*interval)
                if poly:
                    poly=angle_plane(replace(c,polygon=poly),q,True)
            elif kind=="near":
                if minimum_distance(poly,q)>5+SAFE:
                    continue
                # Exact near semantics allow immediate clear; no polygon needed.
            else:
                poly=angle_plane(c,q,False)
            if poly:
                cells.append(replace(c,polygon=poly))
        return JointBelief.from_cells(cells,self.problem,self.max_cells) if cells else None

    def witness(self,x):
        """Validate one complete physical world before using it in a LOWER bound."""
        if math.hypot(*x)>1800:
            return None
        positives=[];negatives=[];seen={}
        for r in self.records:
            q=r["point"];d=math.dist(x,q)
            if r["kind"]=="direction":
                if not 5<d<=1500:
                    return None
                bearing=math.radians(r["bearing"])
                error=(math.atan2(x[1]-q[1],x[0]-q[0])-bearing+math.pi)%TAU-math.pi
                if abs(error)>EPS-1e-10:
                    return None
                if tuple(q) in seen and seen[tuple(q)]!=r["bearing"]:
                    return None
                seen[tuple(q)]=r["bearing"];positives.append(q)
            elif r["kind"]=="no_signal":
                negatives.append(q)
            elif r["kind"]=="clear_failure" and d<=20:
                return None
        if not positives:
            return None
        radius=max([1000.]+[math.dist(x,q) for q in positives])
        in_range=[q for q in negatives if math.dist(x,q)<=radius]
        if not in_range:
            return dict(point=x,radius=radius,type="omni")
        if self.problem==3:
            return None
        constraints=[(q,True) for q in positives]+[(q,False) for q in in_range]
        endpoints=[0.,TAU]
        for q,_ in constraints:
            t=math.atan2(q[1]-x[1],q[0]-x[0])
            endpoints.extend(((t-math.pi/2)%TAU,(t+math.pi/2)%TAU))
        endpoints=sorted(set(endpoints))
        angles=endpoints+[(a+b)/2 for a,b in zip(endpoints,endpoints[1:])]
        for t in angles:
            nx,ny=math.cos(t),math.sin(t)
            if all(((q[0]-x[0])*nx+(q[1]-x[1])*ny>=SAFE if visible else
                    (q[0]-x[0])*nx+(q[1]-x[1])*ny<-SAFE)
                   for q,visible in constraints):
                return dict(point=x,radius=radius,type="directional",angle=t)
        return None

    def witnesses(self,limit=12):
        points=[]
        # Inner convex combinations are candidates only. witness() checks all
        # circular, angular and fixed-radius constraints before accepting them.
        for poly in self.polygons():
            center=tuple(sum(v[i] for v in poly)/len(poly) for i in (0,1))
            points.append(center)
            for v in poly:
                points.extend((v,tuple(.999*v[i]+.001*center[i] for i in (0,1))))
        found={}
        for p in points[:800]:
            w=self.witness(p)
            if w is not None:
                found.setdefault(tuple(p),w)
        values=list(found.values())
        if len(values)<=limit:
            return values
        # Keep spatial extremes, not just the first small component.
        selected=[]
        for i in range(limit):
            t=i*TAU/limit;u=(math.cos(t),math.sin(t))
            selected.append(max(values,key=lambda w:sum(w["point"][j]*u[j] for j in (0,1))))
        return list({tuple(w["point"]):w for w in selected}.values())
