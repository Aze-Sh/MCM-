"""Allocate angular resolution to current actions and their cost bottlenecks."""
from dataclasses import replace
import math
from joint_belief import JointBelief, angle_plane, definitely_in_range, SAFE


class DecisionBelief(JointBelief):
    def refine_angles(self,max_splits=8):
        # Automatic updates contract evidence only. Splitting waits until the
        # controller supplies real candidate actions rather than generic angles.
        self.cells=[c for old in self.cells if (c:=self._contract_angles(old)) is not None]
        if not self.cells:
            raise ArithmeticError("No joint hypothesis remains")
        self.action_splits=getattr(self,"action_splits",0)
        self.split_revision=getattr(self,"split_revision",(-1,0))

    def refine_for_actions(self,points,position,target=None,max_splits=8):
        points=list(dict.fromkeys(tuple(p) for p in points if p is not None))[:4]
        revision=len(self.records)
        old_revision,used=self.split_revision
        if old_revision!=revision:
            used=0
        remaining=min(max_splits,8-used)
        splits=0;reduction=0.
        if not points or remaining<=0:
            return dict(splits=0,reason="no_new_action_budget")
        def support(c):
            return max(math.dist(position,v)+(math.dist(v,target) if target is not None else 0)
                       for v in c.polygon)
        def ambiguity(c):
            if c.arc is None:
                return 0.
            uncertainty=2*math.sin((c.arc[1]-c.arc[0])/4)
            score=0.
            for q in points:
                if definitely_in_range(c.polygon,q,self.positives()) and angle_plane(c,q,True) and angle_plane(c,q,False):
                    score=max(score,uncertainty*max(math.dist(q,v) for v in c.polygon))
            return score
        for _ in range(remaining):
            if len(self.cells)>=self.max_cells:
                break
            global_support=max(support(c) for c in self.cells)
            choices=[]
            for i,c in enumerate(self.cells):
                if c.arc is None or c.arc[1]-c.arc[0]<=math.pi/512:
                    continue
                # A cell is relevant when it can change signal/no-signal at a
                # real candidate action, or attain the worst travel support.
                a=ambiguity(c);s=support(c)
                if a<=SAFE and s<global_support-1e-4:
                    continue
                choices.append((a+max(0.,s-global_support+1.),i))
            trials=[]
            for _,i in sorted(choices,reverse=True)[:4]:
                c=self.cells[i];lo,hi=c.arc;mid=(lo+hi)/2
                children=[child for arc in ((lo,mid),(mid,hi))
                          if (child:=self._contract_angles(replace(c,arc=arc))) is not None]
                old_score=support(c)+ambiguity(c)
                new_score=max((support(k)+ambiguity(k) for k in children),default=0.)
                if old_score-new_score>1e-7:
                    trials.append((old_score-new_score,i,children))
            if not trials:
                break
            gain,i,children=max(trials,key=lambda t:t[0])
            self.cells[i:i+1]=children;splits+=1;reduction+=gain
            if not self.cells:
                raise ArithmeticError("Action refinement removed every hypothesis")
        self.action_splits+=splits;self.split_revision=(revision,used+splits)
        return dict(splits=splits,action_support_reduction_m=reduction,
                    candidate_points=points,reason="action_ambiguity_and_worst_travel_support")
