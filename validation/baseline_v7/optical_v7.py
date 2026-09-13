"""First-success branches condition on all earlier optical failures."""
from itertools import permutations
import math
from joint_belief import subtract_disk,minimum_distance,SAFE
from decision_v6 import optical_cover as geometric_cover,rf_lower_bound


def failure_residual(polygons,point,limit=384):
    out=[]
    for i,poly in enumerate(polygons):
        children=subtract_disk(poly,point,20.)
        if len(out)+len(children)+len(polygons)-i-1>limit:
            out.append(poly)  # Keep possible worlds if the representation fills.
        else:
            out.extend(children)
    return out


def conditional_chain(polygons,points,position,target=None):
    residual=list(polygons);chosen=[];elapsed=0.;worst=0.;branches=[]
    previous=position
    for point in points:
        if not residual:
            break
        if not any(minimum_distance(poly,point)<=20.+SAFE for poly in residual):
            continue  # Proven impossible success: omit this useless attempt.
        elapsed+=math.dist(previous,point)/5
        value=elapsed+3*len(chosen)+5+(math.dist(point,target)/5 if target else 0.)
        branches.append(dict(index=len(chosen)+1,upper_s=value,residual_components=len(residual)))
        worst=max(worst,value);chosen.append(point);previous=point
        residual=failure_residual(residual,point)
    return dict(points=chosen,worst_time_s=worst,first_success_branches=branches,
                omitted_attempts=len(points)-len(chosen))


def optical_cover(belief,anchor,position,target=None,max_attempts=3):
    plan=geometric_cover(belief,anchor,position,target,max_attempts)
    if plan is None:
        return None
    choices=[conditional_chain(belief.polygons(),list(seq),position,target) for seq in permutations(plan['points'])]
    best=min(choices,key=lambda p:p['worst_time_s'])
    if not best['points']:
        return None
    best['certificate']=plan['certificate']+'+conditioned_first_success'
    best['unconditioned_geometric_upper_s']=plan['worst_time_s']
    return best


def optical_decision(belief,anchor,position,target=None,switch_cost=0):
    geometric=geometric_cover(belief,anchor,position,target)
    if geometric is None:
        return None,dict(accepted=False,reason='no_three_disk_cover',optical_upper_s=None)
    lower=rf_lower_bound(belief,position,target,switch_cost)
    alone=lower if target is None else rf_lower_bound(belief,position,None,switch_cost)
    accepted=[];all_plans=[]
    for seq in permutations(geometric['points']):
        plan=conditional_chain(belief.polygons(),list(seq),position,target)
        standalone=conditional_chain(belief.polygons(),plan['points'],position)['worst_time_s']
        gap=min(lower['lower_s']-plan['worst_time_s'],alone['lower_s']-standalone)
        item=(plan,gap,standalone);all_plans.append(item)
        if plan['points'] and gap>1e-4:
            accepted.append(item)
    plan,gap,standalone=min(accepted or all_plans,key=lambda x:x[0]['worst_time_s'])
    plan['certificate']=geometric['certificate']+'+conditioned_first_success'
    ok=bool(accepted)
    return (plan if ok else None),dict(**lower,accepted=ok,optical_upper_s=plan['worst_time_s'],
        standalone_rf_lower_s=alone['lower_s'],standalone_optical_upper_s=standalone,
        dominance_gap_s=gap,omitted_attempts=plan['omitted_attempts'],
        reason='upper_below_rf_lower' if ok else 'bounds_overlap_keep_rf')
