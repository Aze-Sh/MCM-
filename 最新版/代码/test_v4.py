"""Necessary v4 checks: finite geometry and scripted responses, no arena."""
import math
import unittest
from unittest.mock import Mock, patch
from coverage import design, mesh, certify
from cooperative import CooperativeSolver
from evidence import outside_disk_hull, DirectionEvidence
from planning import open_route, route_length, attachment, optical_plan
from posterior import initial_region
from strategy import Anchor


class V4Checks(unittest.TestCase):
    def io_for(self,solver,kinds):
        sequence=iter(kinds)
        def call(path,point=None,channel=None):
            kind=next(sequence)
            cost=(5+int(channel!=solver.channel)) if path=="/measure" else (5 if kind=="success" else 3)
            result=dict(accepted=True,virtual_time_s=solver.virtual+math.dist(solver.position,point)/5+cost)
            result["measure_result" if path=="/measure" else "clear_result"]=kind
            return result
        return call

    def test_design_and_short_open_route(self):
        self.assertEqual((len(design(3)),len(design(4))),(7,25))
        self.assertGreater(1836*math.cos(math.pi/16),1800)
        for triangle in mesh():
            for a in triangle:
                for b in triangle:
                    self.assertLess(math.dist(a,b),1000)
            a,b,c=triangle
            self.assertGreater((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]),0)
        self.assertAlmostEqual(route_length((0,0),design(4)),17885.56730922849)
        order=open_route((0,0),design(4))
        self.assertEqual(set(order),set(design(4)))
        self.assertLessEqual(route_length((0,0),order),17885.568)
        self.assertEqual(attachment((0,0),[(1000,0),(2000,0)],(1900,10))[1],1)

    def test_continuous_boxes_proved_or_unknown(self):
        self.assertTrue(certify([(0,0)],3,domain_radius=100)["proved"])
        self.assertTrue(certify([(-300,-300),(300,-300),(0,400)],4,domain_radius=100)["proved"])
        self.assertFalse(certify([(300,0),(300,100),(300,-100)],4,max_depth=3,domain_radius=100)["proved"])

    def test_negative_radius_and_orientation(self):
        polygon=outside_disk_hull([(0,-.1),(2,-.1),(2,.1),(0,.1)],(0,0),1)
        self.assertGreater(min(p[0] for p in polygon),.99)
        self.assertIn((2,.1),polygon)
        evidence=DirectionEvidence()
        evidence.negative((1,0),[(0,0)])
        self.assertTrue(evidence.directional)
        self.assertGreater(evidence.minimum_dot((-10,0),[(0,0)]),-1e-6)
        self.assertLess(evidence.minimum_dot((10,0),[(0,0)]),-9)

    def test_optical_failure_then_certified_completion(self):
        io=Mock();s=CooperativeSolver(io,4);s.channel=7
        s.discover(2);s.anchors[2]=Anchor((0,0),0,70)
        s.regions[2]=[(5,-1.3),(70,-1.3),(70,1.3),(5,1.3)]
        plan=optical_plan(s.anchors[2],s.regions[2],s.position,4)
        self.assertEqual(len(plan["points"]),2)
        self.assertLess(plan["worst_time_s"],20)
        io.call.side_effect=self.io_for(s,["no_target_in_range","success"])
        s.approach(2)
        self.assertEqual(s.cleared,{2});self.assertEqual(s.failed_clears,1)
        self.assertEqual(s.channel,7);self.assertEqual(s.measures,0)

    def test_shared_bearing_tightens_without_resetting_rounds(self):
        io=Mock();s=CooperativeSolver(io,3)
        s.position=(750.,100.);s.discover(2)
        s.anchors[2]=Anchor((0,0),0,1500,2)
        s.regions[2]=initial_region(s.anchors[2],annular=True)
        s.positives[2]=[(0,0)]
        io.call.return_value=dict(accepted=True,virtual_time_s=6,measure_result="direction",svd_deg=270)
        s.shared_measurements(s.position)
        self.assertEqual(s.optional_counts[2],1)
        self.assertEqual(s.anchors[2].rounds,2)
        self.assertEqual(s.anchors[2].point,(0,0))
        self.assertLess(s.anchors[2].bound,800)

    def test_directional_fallback_then_optical_cover(self):
        io=Mock();s=CooperativeSolver(io,4);s.discover(2)
        s.anchors[2]=Anchor((0,0),0,1000)
        s.regions[2]=initial_region(s.anchors[2],annular=True)
        s.positives[2]=[(0,0)]
        io.call.side_effect=self.io_for(s,["no_signal"]*8+["no_target_in_range","success"])
        s.approach(2)
        self.assertEqual(s.negative_pairs[2],4)
        self.assertEqual(s.measures,8)
        self.assertEqual(s.cleared,{2})
        self.assertTrue(s.directions[2].directional)

    def test_joint_clear_preserves_two_channels_at_shared_position(self):
        io=Mock();s=CooperativeSolver(io,3)
        for c in (2,3):
            s.discover(c);s.anchors[c]=Anchor((0,0),0,30)
            s.regions[c]=[(10,-1),(12,-1),(12,1),(10,1)]
        io.call.side_effect=self.io_for(s,["success","success"])
        s.joint_clear([2,3],(100,0))
        self.assertEqual(s.cleared,{2,3})
        self.assertEqual(s.clear_attempts,2)
        self.assertEqual(s.channel,1)

    def test_scripted_complete_run_has_explicit_completion_basis(self):
        # Fixed protocol script only: ten initial near replies, then negatives.
        io=Mock();io.pending=None;s=CooperativeSolver(io,3)
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
        self.assertEqual(result["completion_basis"],"proved_coverage_schedule")
        self.assertEqual(len(result["absent_channels"]),10)


if __name__=="__main__":
    unittest.main()
