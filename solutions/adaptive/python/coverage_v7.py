"""Fair deletion/replacement candidates; reserve proof work for later evidence."""
import math
from coverage import certify
from tail_search import residual_regions
from planning import open_route,route_length


def proof_allowance(visited,quota,spent):
    released=min(16,4*(1+4*visited//max(1,quota)))
    return max(0,min(2,released-spent))


def revise_route(position,visited,remaining,problem,proof_limit=2):
    route=open_route(position,remaining);old=route_length(position,route)
    if not route or proof_limit<=0:
        return route,dict(changed=False,proofs_attempted=0,reason='reserved_for_later')
    residual=residual_regions(visited,problem)
    boxes=residual['boxes'];extra=[]
    if boxes:
        b=max(boxes,key=lambda b:(b[2]-b[0])*(b[3]-b[1]))
        extra.append(((b[0]+b[2])/2,(b[1]+b[3])/2))
    deletions=[];replacements=[]
    radius=1820. if problem==3 else 1836.
    for q in route:
        without=[p for p in route if p!=q]
        deletions.append((route_length(position,without),without,q,None))
        for raw in [position,tuple((position[k]+q[k])/2 for k in (0,1))]+extra:
            new=tuple(x*min(1.,radius/max(radius,math.hypot(*raw))) for x in raw)
            if new in route or new in visited:
                continue
            trial=min((without[:i]+[new]+without[i:] for i in range(len(without)+1)),key=lambda r:route_length(position,r))
            replacements.append((route_length(position,trial),trial,q,new))
    # A guaranteed slot for each operation family prevents the cheapest failed
    # deletions from starving geometrically feasible relocations indefinitely.
    slots=[]
    for kind,family in (('replacement',replacements),('deletion',deletions)):
        useful=[p for p in family if p[0]<old-1.]
        if useful:
            slots.append((kind,min(useful,key=lambda p:p[0])))
    attempts=[]
    for kind,(length,trial,q,new) in slots[:proof_limit]:
        proof=certify(list(visited)+trial,problem,max_nodes=4096)
        attempts.append(dict(kind=kind,proved=proof['proved'],nodes=proof['nodes'],
                             unresolved_box=proof.get('unresolved_box'),removed=q,inserted=new))
        if proof['proved']:
            return trial,dict(changed=True,operation=kind,removed=q,inserted=new,
                              planned_travel_reduction_m=old-length,proof=proof,
                              proofs_attempted=len(attempts),attempts=attempts)
    return route,dict(changed=False,proofs_attempted=len(attempts),attempts=attempts,
                      unresolved_boxes=len(boxes),residual_nodes=residual['nodes'])
