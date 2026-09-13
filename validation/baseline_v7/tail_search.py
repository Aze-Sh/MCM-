"""Residual outer regions and quota-preserving continuous coverage rewrites."""
import math
from geometry import hull
from coverage import contains_strict, certify
from planning import open_route, route_length


def residual_regions(points, problem, max_nodes=512, max_depth=8, radius=1800.):
    """All unresolved boxes are retained, including the unprocessed stack.

    These boxes can contain already excluded space; neither their centres nor
    their area is evidence of a hidden source. Empty means a whole-domain proof.
    """
    stack=[(-radius,-radius,radius,radius,0)];regions=[];nodes=0
    while stack and nodes<max_nodes:
        x0,y0,x1,y1,depth=stack.pop();nodes+=1
        if math.hypot(max(x0,0.,-x1),max(y0,0.,-y1))>radius+1e-5:
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
            regions.append((x0,y0,x1,y1));continue
        mx,my=(x0+x1)/2,(y0+y1)/2
        stack.extend([(x0,y0,mx,my,depth+1),(mx,y0,x1,my,depth+1),
                      (x0,my,mx,y1,depth+1),(mx,my,x1,y1,depth+1)])
    regions.extend(tuple(box[:4]) for box in stack)
    return dict(boxes=regions,nodes=nodes,proved=not regions)


def revise_route(position, visited, remaining, problem, proof_limit=2):
    """Rank finitely many edits by travel; adopt only a full coverage proof.

    No extra scan is added. Search ordering still has its ordinary finite route
    heuristic; residual geometry proposes new vertices rather than claiming an
    area score proves discovery. An inconclusive proof leaves the plan intact.
    """
    route=open_route(position,remaining)
    residual=residual_regions(visited,problem)
    if not route:
        return route,dict(changed=False,residual=residual)
    boxes=residual["boxes"]
    candidates=[tuple(position)]
    if boxes:
        area=sum((b[2]-b[0])*(b[3]-b[1]) for b in boxes)
        candidates.append(tuple(sum((b[i]+b[i+2])/2*(b[2]-b[0])*(b[3]-b[1]) for b in boxes)/area for i in (0,1)))
        b=max(boxes,key=lambda b:(b[2]-b[0])*(b[3]-b[1]))
        candidates.append(((b[0]+b[2])/2,(b[1]+b[3])/2))
    radius=1820. if problem==3 else 1836.
    candidates=[tuple(x*min(1.,radius/max(radius,math.hypot(*p))) for x in p) for p in candidates]
    old_length=route_length(position,route);proposals=[]
    for old in route:
        without=[q for q in route if q!=old]
        proposals.append((route_length(position,without),without,old,None))
        for new in candidates:
            if new in route or any(math.dist(new,q)<1e-5 for q in visited):
                continue
            # Insertion position is itself optimized in this finite family.
            trial=min((without[:i]+[new]+without[i:] for i in range(len(without)+1)),
                      key=lambda r:route_length(position,r))
            proposals.append((route_length(position,trial),trial,old,new))
    checked=0
    for length,trial,old,new in sorted(proposals,key=lambda e:e[0]):
        if length>=old_length-1. or checked>=proof_limit:
            break
        checked+=1
        proof=certify(list(visited)+trial,problem,max_nodes=4096)
        if proof["proved"]:
            return trial,dict(changed=True,removed=old,inserted=new,
                planned_travel_reduction_m=old_length-length,proof=proof,
                proofs_attempted=checked,residual_nodes=residual["nodes"],
                unresolved_boxes=len(boxes))
    return route,dict(changed=False,proofs_attempted=checked,
                     residual_nodes=residual["nodes"],unresolved_boxes=len(boxes))
