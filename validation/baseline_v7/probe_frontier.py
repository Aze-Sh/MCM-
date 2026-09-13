"""Nearest probes that certify contraction of the WHOLE compatible region."""
from dataclasses import replace
import math
from posterior import nearest_clear_point
from joint_belief import angle_plane,SAFE
from planning import fallback_bound


def disk_intersection_projection(polygon,position,radius):
    if radius<=0:return None
    scale=19.8/radius
    point=nearest_clear_point([(v[0]*scale,v[1]*scale) for v in polygon],tuple(x*scale for x in position))
    return None if point is None else tuple(x/scale for x in point)


def visibility_guaranteed(belief,point):
    return belief.problem==3 or all(not angle_plane(cell,point,False) for cell in belief.cells)


def guaranteed_probes(belief,anchor,position):
    if anchor.bound<=44.5:return []
    limit=.502*anchor.bound-2.4
    radii=sorted(set(r for r in (44.5,89.9,179.9,limit) if 5<r<=limit))
    poly=belief.hull();probes=[]
    for radius in radii:
        point=disk_intersection_projection(poly,position,radius-1e-3)
        if point is None or not visibility_guaranteed(belief,point):continue
        bound=max(5+SAFE,max(math.dist(point,v) for v in poly)+SAFE)
        if bound>limit or bound>=1000-SAFE:continue
        temporary=replace(anchor,point=point,bearing=0.,bound=bound,rounds=anchor.rounds+1)
        service=6+max(5.,fallback_bound(temporary,point,belief.problem)-1.)
        probes.append(dict(point=point,bound=bound,service_s=service,limit=limit,
                           proof='whole_region_receive_radius_and_visible_halfplane'))
    return probes


def regional_upper(belief,anchor,position,target=None):
    """One certified regional measurement followed by the original fallback."""
    choices=[];poly=belief.hull()
    outgoing=(max(math.dist(v,target) for v in poly)+20)/5 if target is not None else 0.
    for probe in guaranteed_probes(belief,anchor,position):
        alone=math.dist(position,probe['point'])/5+probe['service_s']
        choices.append((alone+outgoing,alone,probe))
    return min(choices,key=lambda c:c[0]) if choices else None
