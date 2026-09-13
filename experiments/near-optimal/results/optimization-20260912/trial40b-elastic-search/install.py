import math
import time


def install(v):
    from planning import open_route, route_length
    from probe_frontier import disk_intersection_projection
    from routing import improve_clear_route
    original=v.gengxin_luxian
    original_summary=v.huizong

    def arc(point):
        radius=math.hypot(*point)
        if not 802<radius<2798:return None
        cosine=(radius*radius+1800**2-998**2)/(2*radius*1800)
        if not -1<cosine<1:return None
        return math.acos(cosine)

    def boundary(angle):
        return 1800*math.cos(angle),1800*math.sin(angle)

    def update(layout,ledger,position):
        pending=layout['pending_stop']
        route=original(layout,ledger,position)
        unknown=v.pindao(ledger,('unknown',))
        if ledger['problem']!=3 or pending is None or not unknown:return route
        clear=tuple(pending);clear_arc=arc(clear)
        if clear_arc is None or clear in route:return route
        common=set.intersection(*(set(ledger['channels'][c]['radio']) for c in unknown))
        if v.g.point(clear) in common:return route
        remaining=set(map(tuple,route))
        sites=set(v.g.floating(q) for q in common)|remaining
        ring=sorted((q for q in sites if math.hypot(*q)>802),key=lambda q:math.atan2(q[1],q[0])%(2*math.pi))
        if len(ring)<5:return route
        angles=[math.atan2(q[1],q[0])%(2*math.pi) for q in ring]
        start=time.perf_counter();options=[];rejected=0
        old_cost=route_length(position,route)/5+6*len(unknown)*len(route)
        n=len(ring)
        def theta(index):return angles[index%n]+2*math.pi*(index//n)
        for i,removed in enumerate(ring):
            if removed not in remaining:continue
            angle=theta(i);a=math.atan2(clear[1],clear[0]);a=angle+math.atan2(math.sin(a-angle),math.cos(a-angle))
            trial=[clear if q==removed else q for q in route]
            changed=[];valid=True
            for side in (-1,1):
                index=i+side;neighbor=ring[index%n]
                if neighbor not in remaining:
                    width=arc(neighbor)
                    if width is None or (side==-1 and theta(index)+width<a-clear_arc) or (side==1 and theta(index)-width>a+clear_arc):valid=False
                    continue
                fixed_index=i+2*side;fixed=ring[fixed_index%n];fixed_arc=arc(fixed)
                if fixed_arc is None:valid=False;break
                if side==-1:lo,hi=theta(fixed_index)+fixed_arc-math.radians(.03),a-clear_arc+math.radians(.03)
                else:lo,hi=a+clear_arc-math.radians(.03),theta(fixed_index)-fixed_arc+math.radians(.03)
                if not 0<hi-lo<math.pi:valid=False;break
                ends=[boundary(lo),boundary(hi)]
                point=disk_intersection_projection(ends,neighbor,999.)
                if point is None:valid=False;break
                ordered=open_route(position,trial);j=ordered.index(neighbor)
                before=position if j==0 else ordered[j-1]
                after=ordered[j+1] if j+1<len(ordered) else before
                point,_=improve_clear_route(ends,999.,point,before,after,max_steps=24)
                trial=[point if q==neighbor else q for q in trial]
                changed.append(dict(old=neighbor,new=point,boundary_arc=[lo,hi]))
            if not valid or not changed:
                rejected+=1;continue
            trial=open_route(position,trial)
            cost=route_length(position,trial)/5+6*len(unknown)*len(trial)
            if cost<old_cost-1e-6:options.append((cost,removed,changed,trial))
        checks=[];accepted=None
        for cost,removed,changed,trial in sorted(options,key=lambda item:item[0]):
            if time.perf_counter()-start>.75:break
            points=tuple(sorted(common|{v.g.point(p) for p in trial}))
            t=time.perf_counter();proof=v.g.coverage_certificate(points,(),3,ledger['coverage_nodes'],ledger['coverage_depth']);wall=time.perf_counter()-t
            checks.append(dict(removed=removed,nodes=proof[1],proved=proof[0],unresolved=proof[2],wall_s=wall,predicted_saving_s=old_cost-cost))
            if proof[0]:
                accepted=dict(clear=clear,removed=removed,moved_neighbors=changed,future_points=trial,old_cost_s=old_cost,new_cost_s=cost,saving_s=old_cost-cost,coverage_nodes=proof[1],scope='prospective whole coverage only; no future negatives inserted')
                route=trial;layout['points']=trial;layout['route']=trial;layout['signature']=None
                break
        layout.setdefault('local_adjustment_audits',[]).append(dict(clear=clear,geometry_rejected=rejected,cost_candidates=len(options),checks=checks,accepted=accepted,wall_s=time.perf_counter()-start))
        return route

    def summary(state):
        result=original_summary(state)
        result['local_search_adjustment']=state['search_plan'].get('local_adjustment_audits',[])
        return result
    v.gengxin_luxian=update;v.huizong=summary
