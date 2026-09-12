"""Necessary fixed-evidence checks; no environment, network or simulator."""
from dataclasses import replace
import math
import unittest
from unittest.mock import Mock, patch
from strategy import Anchor
from posterior import initial_region
from adaptive import AdaptiveSolver
from joint_belief import JointBelief, Cell, minimum_distance, subtract_disk, EPS, TAU
from decision import optical_cover, optical_decision, measurement_envelope, output_intervals
from decision import terminal_upper
import run_robot  # Import only; its main guard must not connect.


def rectangle(x0,x1,y=.1):
    return [(x0,-y),(x1,-y),(x1,y),(x0,y)]


def contains(polys,p):
    return any(minimum_distance(poly,p)<1e-7 for poly in polys)


class V5Checks(unittest.TestCase):
    def state(self,problem=3,bound=70):
        io=Mock();s=AdaptiveSolver(io,problem);s.channel=7
        s.discover(2);s.anchors[2]=Anchor((0,0),0,bound)
        s.regions[2]=initial_region(s.anchors[2],annular=True)
        s.positives[2]=[(0,0)]
        s.raw_evidence[2]=[dict(kind="direction",point=(0,0),bearing=0)]
        return io,s

    def scripted(self,s,entries):
        seq=iter(entries)
        def call(path,point=None,channel=None):
            entry=next(seq);kind=entry[0] if isinstance(entry,tuple) else entry
            cost=5+int(channel!=s.channel) if path=="/measure" else (5 if kind=="success" else 3)
            result=dict(accepted=True,virtual_time_s=s.virtual+math.dist(s.position,point)/5+cost)
            result["measure_result" if path=="/measure" else "clear_result"]=kind
            if isinstance(entry,tuple):
                result["svd_deg"]=entry[1]
            return result
        return call

    def test_hole_retained_and_budget_never_discards_parent(self):
        pieces=subtract_disk(rectangle(-2,2),(0,0),1)
        self.assertFalse(contains(pieces,(0,0)))
        self.assertTrue(contains(pieces,(-1.5,0)));self.assertTrue(contains(pieces,(1.5,0)))
        b=JointBelief(rectangle(-30,30),3,max_cells=1)
        b.observe(dict(kind="clear_failure",point=(0,0)))
        self.assertEqual(len(b.cells),1);self.assertEqual(b.retained_parents,1)
        self.assertTrue(contains(b.polygons(),(0,0)))
        self.assertEqual(len(b.records),1)

    def test_joint_direction_cells_do_not_form_an_independent_product(self):
        poly=rectangle(100,900,1)
        b=JointBelief.from_cells([Cell(poly,(math.pi-.01,math.pi+.01)),
                                 Cell(poly,(4.62,4.68))],4)
        b.records=[dict(kind="direction",point=(0,0),bearing=0)]
        b.observe(dict(kind="no_signal",point=(500,100)))
        left=[c.polygon for c in b.cells if c.arc[0]<=math.pi<=c.arc[1]]
        self.assertTrue(left)
        self.assertLess(max(v[0] for p in left for v in p),520)
        self.assertTrue(contains(b.polygons(),(900,0)))
        self.assertIsNotNone(b.witness((900,0)))

    def test_new_positive_reprocesses_old_negative_radius_constraint(self):
        b=JointBelief(rectangle(1100,1400),3)
        b.observe(dict(kind="no_signal",point=(0,0)))
        b.observe(dict(kind="direction",point=(2600,0),bearing=180))
        self.assertGreater(min(v[0] for p in b.polygons() for v in p),1299.999)
        self.assertTrue(contains(b.polygons(),(1350,0)))

    def test_output_intervals_cover_extreme_allowed_bearings(self):
        a=Anchor((0,0),0)
        b=JointBelief(initial_region(a,annular=True),3,
                      [dict(kind="direction",point=(0,0),bearing=0)])
        q=(750,100);intervals=output_intervals(b.hull(),q)
        envelope=measurement_envelope(b,a,q,3)
        self.assertLessEqual(len(envelope["branches"]),14)
        for x in (20.,750.,1480.):
            for error in (-EPS*.999,0.,EPS*.999):
                bearing=math.atan2(-100,x-750)+error
                matches=[(lo,hi) for lo,hi in intervals if any(lo<=bearing+k*TAU<=hi for k in (-1,0,1))]
                self.assertTrue(matches)
                self.assertTrue(any(contains(b.outcome(q,"direction",iv).polygons(),(x,0)) for iv in matches))

    def test_optical_requires_lower_bound_dominance_not_just_an_upper(self):
        a=Anchor((0,0),0,70)
        b=JointBelief(rectangle(5.01,69.5,1),3,[dict(kind="direction",point=(0,0),bearing=0)])
        plan,d=optical_decision(b,a,(0,0))
        self.assertIsNotNone(plan);self.assertGreater(d["witness_count"],0)
        self.assertGreater(d["dominance_gap_s"],0)
        self.assertIsNone(b.witness((69.5,2)))  # Outside the real bearing band.
        self.assertIsNone(b.witness((4,0)))     # Contradicts a normal response.
        rejected,d=optical_decision(b,a,(35,0))
        self.assertIsNone(rejected);self.assertEqual(d["reason"],"bounds_overlap_keep_rf")

    def test_disconnected_components_use_two_disks_across_empty_gap(self):
        b=JointBelief.from_cells([Cell(rectangle(10,12,1)),Cell(rectangle(100,102,1))],3)
        b.records=[dict(kind="direction",point=(0,0),bearing=0)]
        plan=optical_cover(b,Anchor((0,0),0,110),(0,0))
        self.assertEqual(len(plan["points"]),2)
        self.assertLess(plan["worst_time_s"],26)
        self.assertEqual(plan["certificate"],"continuous_atom_cover")

    def test_shared_read_reanchors_before_round_one_and_commits(self):
        io,s=self.state(bound=1500);s.position=(750.,100.);s.remaining=[]
        s.reserved_source=2
        io.call.side_effect=self.scripted(s,[("direction",270)])
        s.shared_measurements(s.position)
        self.assertEqual(s.anchors[2].point,s.position)
        self.assertEqual(s.anchors[2].rounds,0)
        self.assertLess(s.anchors[2].bound,120)
        self.assertEqual(s.optional_counts[2],1);self.assertEqual(s.committed_source,2)
        s.anchors[2]=replace(s.anchors[2],rounds=1)
        self.assertIsNone(s._forecast(2,(750,200),None))

    def test_whole_outcome_information_changes_the_route_decision(self):
        io,s=self.state(bound=1500);q=(750.,100.)
        belief=s._belief(2);a=s.anchors[2]
        now=terminal_upper(belief,a,s.position,3,q)[0]-math.dist(s.position,q)/5
        later_without_read=terminal_upper(belief,a,q,3)[0]
        self.assertLess(now,later_without_read)  # Motion alone prefers handling now.
        candidates,ready=s.choose_candidates([q])
        self.assertEqual(candidates,[]);self.assertEqual(ready,[])
        self.assertEqual(s.reserved_source,2)   # Complete outcome bounds change it.

    def test_optical_failure_enters_posterior_and_preserves_rf_channel(self):
        io,s=self.state(bound=70)
        io.call.side_effect=self.scripted(s,["no_target_in_range","success"])
        s.approach(2)
        self.assertEqual(s.cleared,{2});self.assertEqual(s.failed_clears,1)
        self.assertEqual(s.channel,7);self.assertEqual(s.measures,0)
        self.assertEqual(s.raw_evidence[2][-1]["kind"],"clear_failure")
        self.assertEqual(s.optical_accepted,1)

    def test_radio_fallback_near_then_clear(self):
        io,s=self.state(bound=200)
        io.call.side_effect=self.scripted(s,["near","success"])
        s.approach(2)
        self.assertEqual(s.cleared,{2});self.assertEqual(s.measures,1)
        self.assertEqual(s.clear_attempts,1);self.assertEqual(s.optical_accepted,0)

    def test_directional_negative_then_near_keeps_the_paired_action_valid(self):
        # Fixed consistent responses: for the L=200 pair, x=(102.5,0) with a
        # downward visible half-plane permits negative above and near below.
        io,s=self.state(problem=4,bound=200)
        io.call.side_effect=self.scripted(s,["no_signal","near","success"])
        s.approach(2)
        self.assertEqual(s.cleared,{2});self.assertEqual(s.measures,2)
        self.assertEqual(s.clear_attempts,1)
        self.assertTrue(s.directions[2].directional)
        self.assertEqual([r["kind"] for r in s.raw_evidence[2]],["direction","no_signal","near"])

    def test_full_scripted_run_keeps_completion_and_action_accounting(self):
        io=Mock();io.pending=None;s=AdaptiveSolver(io,3)
        def call(path,point=None,channel=None):
            if path=="/enter":
                return dict(accepted=True,virtual_time_s=0,max_virtual_duration_s=360000,remaining_real_duration_s=1200)
            if path=="/exit":
                return dict(accepted=True,virtual_time_s=s.virtual,exit_reason="user_exit")
            cost=5+int(path=="/measure" and channel!=s.channel)
            result=dict(accepted=True,virtual_time_s=s.virtual+math.dist(s.position,point)/5+cost)
            if path=="/clear":
                result["clear_result"]="success"
            else:
                result["measure_result"]="near" if not s.visited and channel<=10 else "no_signal"
            return result
        io.call.side_effect=call
        with patch("cooperative.certify",return_value=dict(proved=False,nodes=0,unresolved_box=None)):
            result=s.run()
        self.assertEqual(result["cleared_count"],10)
        self.assertEqual(result["measure_count"],80)
        self.assertTrue(result["exit_confirmed"])
        self.assertEqual(result["strategy"],"joint-outcome-lookahead-v5")
        self.assertEqual(result["completion_basis"],"proved_coverage_schedule")


if __name__=="__main__":
    unittest.main()
