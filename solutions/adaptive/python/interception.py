"""Actively choose a useful observation location with a whole-response bound."""
from dataclasses import replace
import math
from posterior import nearest_clear_point
from strategy import offset
from joint_belief import definitely_in_range, SAFE
from decision import output_intervals
from planning import fallback_bound


def reception_guaranteed(belief,point):
    return all(definitely_in_range(poly,point,belief.positives()) for poly in belief.polygons())


def observation_candidates(belief,anchor,position,target=None,domain_radius=1836.):
    poly=belief.hull();points=[tuple(position)]
    # Scale a general receive-disk intersection into the existing exact finite
    # disk-projection routine. This finds the closest guaranteed reception point.
    scale=19.8/999.9
    q=nearest_clear_point([(x*scale,y*scale) for x,y in poly],tuple(x*scale for x in position))
    if q is not None:
        points.append(tuple(x/scale for x in q))
    points.extend(offset(anchor,.5,side) for side in (-.15,.15))
    wide=[offset(anchor,.443,.405),offset(anchor,.443,-.405)]
    points.append(min(wide,key=lambda q:math.dist(position,q)+(math.dist(q,target) if target else 0)))
    accepted=[]
    for q in dict.fromkeys(points):
        if math.hypot(*q)>domain_radius or tuple(q) in [tuple(r['point']) for r in belief.records if r['kind']=='direction']:
            continue
        if reception_guaranteed(belief,q):
            accepted.append(q)
    return accepted


def observation_envelope(belief,anchor,point,problem,target=None,max_bins=24,measure_cost=6):
    if anchor.rounds!=0 or not reception_guaranteed(belief,point):
        return None
    def completion(posterior,kind,interval=None):
        if kind=='near':
            return 5+(math.dist(point,target)/5 if target else 0),5.
        temporary=anchor
        if kind=='direction':
            bound=min(1500.,max(5+SAFE,max(math.dist(point,v) for v in posterior.hull())+SAFE))
            temporary=replace(anchor,point=tuple(point),bound=bound,bearing=0.)
        # One executable continuation must satisfy BOTH budgets. Separately
        # minimizing target and standalone policies would not establish this.
        # Actual complete_reference only makes two-budget-safe substitutions.
        alone=fallback_bound(temporary,point,problem)-1
        value=fallback_bound(temporary,point,problem,target,posterior.hull())-1 if target is not None else alone
        return value,alone
    branches=[]
    for kind in ('near','no_signal'):
        if kind=='no_signal' and problem==3:
            continue
        posterior=belief.outcome(point,kind)
        if posterior is not None:
            value,alone=completion(posterior,kind)
            branches.append(dict(kind=kind,upper_s=value,standalone_s=alone))
    def normal(lo,hi):
        posterior=belief.outcome(point,'direction',(lo,hi))
        if posterior is None:
            return None
        value,alone=completion(posterior,'direction',(lo,hi))
        return dict(kind='direction',interval=(lo,hi),upper_s=value,standalone_s=alone)
    normals=[b for lo,hi in output_intervals(belief.hull(),point,max_bins=4) if (b:=normal(lo,hi)) is not None]
    leaves=len(normals);splits=0
    while normals and leaves<max_bins:
        largest=max(range(len(normals)),key=lambda i:max(normals[i]['upper_s'],normals[i]['standalone_s']))
        b=normals[largest];lo,hi=b['interval']
        if hi-lo<math.radians(.1):
            break
        other=max((max(v['upper_s'],v['standalone_s']) for v in branches),default=0.)
        if max(b['upper_s'],b['standalone_s'])<=other:
            break
        mid=(lo+hi)/2
        children=[child for a,z in ((lo,mid),(mid,hi)) if (child:=normal(a,z)) is not None]
        normals[largest:largest+1]=children;leaves+=1;splits+=1
    all_branches=branches+normals
    if not all_branches:
        raise ArithmeticError('No possible response at proposed observation')
    return dict(upper_s=measure_cost+max(b['upper_s'] for b in all_branches),
                standalone_s=measure_cost+max(b['standalone_s'] for b in all_branches),
                normal_bins=len(normals),interval_splits=splits,branches=all_branches,
                range_basis='minimum_radius_or_same_source_positive_distance')


def choose_interception(belief,anchor,position,problem,target,baseline_upper,baseline_standalone,
                        used=0,previous=(),channel_switch=1):
    if used>=2 or anchor.rounds!=0:
        return None,dict(reason='optional_budget_or_local_round',candidates=0)
    best=None;count=0
    for q in observation_candidates(belief,anchor,position,target,1820. if problem==3 else 1836.):
        if tuple(q) in previous:
            continue
        count+=1
        envelope=observation_envelope(belief,anchor,q,problem,target,measure_cost=5+channel_switch)
        if envelope is None:
            continue
        move=math.dist(position,q)/5
        upper=move+envelope['upper_s'];alone=move+envelope['standalone_s']
        if upper<baseline_upper-1. and alone<baseline_standalone-1.:
            if best is None or upper<best['upper_s']:
                best=dict(point=q,upper_s=upper,standalone_s=alone,
                          baseline_upper_s=baseline_upper,baseline_standalone_s=baseline_standalone,
                          normal_bins=envelope['normal_bins'],interval_splits=envelope['interval_splits'],
                          range_basis=envelope['range_basis'])
    return best,dict(reason='accepted' if best else 'no_certified_upper_improvement',candidates=count)
