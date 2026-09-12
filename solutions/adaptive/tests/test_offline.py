"""Small offline checks only: analytic fixtures and canned HTTP responses."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError
from geometry import solve_wedges
from protocol import HttpTransport, RejectedAction
from solver import Solver
from posterior import initial_region, constrain, tighten_anchor, nearest_clear_point, clear_choice
from strategy import (Anchor, paired_points, negative_pair_update, positive_update,
                      terminal_clear_point, search_points)
from strategy import annular_points,annular_update,annular_clear_disk,annular_clear_point,second_point_region
from posterior import omni_negative_cuts
from routing import improve_clear_route,two_leg


class OfflineChecks(unittest.TestCase):
    def test_annular_five_and_six_round_bounds(self):
        anchor=Anchor((0,0),0)
        for _ in range(5):
            self.assertIsNone(annular_clear_point(anchor,anchor.point))
            q=annular_points(anchor,anchor.point)[0]
            for r in (5,anchor.bound):
                for error in (-1.005,1.005):
                    t=math.radians(error)
                    x=(anchor.point[0]+r*math.cos(t),anchor.point[1]+r*math.sin(t))
                    self.assertLess(math.dist(q,x),.502*anchor.bound-2.4)
            anchor=annular_update(anchor,q,0)
        self.assertAlmostEqual(anchor.bound,43.1543916024096)
        self.assertIsNotNone(annular_clear_disk(anchor))
        mixed=Anchor((0,0),0)
        for _ in range(6):
            if annular_clear_disk(mixed) is not None:
                break
            mixed=annular_update(mixed)
        self.assertIsNotNone(annular_clear_disk(mixed))

    def test_second_region_strict_expansion(self):
        result=second_point_region((0,0),0,(500,840))
        self.assertTrue(result["query_in_region"])
        e=math.radians(1.005)
        self.assertGreater(math.dist((500,840),(1500*math.cos(e),-1500*math.sin(e))),1000)

    def test_omni_negative_halfplane(self):
        polygon=omni_negative_cuts([(-2,-2),(2,-2),(2,2),(-2,2)],(0,0),[(2,0)])
        self.assertLessEqual(max(v[0] for v in polygon),1.000001)
        self.assertEqual(min(v[0] for v in polygon),-2)

    def test_route_feasible_and_nonincreasing(self):
        p,t,start=(0,3),(3,0),(0,1)
        point,diag=improve_clear_route([(0,0)],1,start,p,t)
        self.assertLessEqual(math.hypot(*point),1+1e-10)
        self.assertLess(two_leg(point,p,t),two_leg(start,p,t)-.1)
        self.assertLessEqual(diag["iterations"],24)

    def test_fixed_double_negative_sequence_and_route_commitment(self):
        # Scripted responses only; no source/environment/simulator exists here.
        io=Mock()
        solver=Solver(io,4)
        solver.discover(2)
        solver.anchors[2]=Anchor((0,0),0,100)
        solver.regions[2]=initial_region(solver.anchors[2],annular=True)
        solver.remaining=[(100,0)]
        responses=iter(["no_signal"]*4+["success"])
        def reply(path,point,channel):
            kind=next(responses)
            cost=5+int(path=="/measure" and channel!=solver.channel)
            field="measure_result" if path=="/measure" else "clear_result"
            return dict(accepted=True,virtual_time_s=solver.virtual+math.dist(solver.position,point)/5+cost,
                        **{field:kind})
        io.call.side_effect=reply
        solver.approach(2)
        self.assertEqual(solver.negative_pairs[2],2)
        self.assertEqual(solver.measures,4)
        self.assertEqual(solver.cleared,{2})
        self.assertEqual(solver.channel,2)
        self.assertEqual(solver.next_search_committed,(100,0))

    def test_history_region_enables_early_clear(self):
        # Two prescribed bearing constraints, not a generated arena or rollout.
        first = Anchor((0,0),0)
        second = positive_update(first,(750,30),270)
        polygon = constrain(initial_region(first),second)
        tightened = tighten_anchor(second,polygon)
        self.assertLess(tightened.bound,second.bound)
        self.assertIsNone(terminal_clear_point(second,(750,30)))
        point,method = clear_choice(second,polygon,(750,30))
        self.assertEqual(method,"history_projection")
        self.assertIsNotNone(point)
        self.assertLessEqual(max(math.dist(point,v) for v in polygon),19.8)

    def test_clear_projection_two_active_circles(self):
        polygon = [(-10,0),(10,0)]
        radius = 19.8-1e-6
        point = nearest_clear_point(polygon,(0,50))
        self.assertAlmostEqual(point[0],0,places=9)
        self.assertAlmostEqual(point[1],math.sqrt(radius*radius-100),places=8)
        self.assertIsNone(nearest_clear_point([(-21,0),(21,0)],(0,50)))
        self.assertEqual(nearest_clear_point(polygon,(0,0)),(0,0))

    def test_clear_choice_retains_anchor_fallback(self):
        anchor = Anchor((0,0),0,bound=30)
        old = terminal_clear_point(anchor,(100,0))
        # Deliberately loose outer region: the independent anchor remains valid.
        point,method = clear_choice(anchor,[(-50,-50),(50,-50),(0,50)],(100,0))
        self.assertEqual((point,method),(old,"anchor_certificate"))

    def test_contraction_and_terminal_boundary(self):
        a = Anchor((0,0), 0)
        self.assertEqual(paired_points(a,(0,0)), ((750,30),(750,-30)))
        b = negative_pair_update(a)
        self.assertEqual((b.point,b.bearing), (a.point,a.bearing))
        self.assertEqual(b.bound,751.5)
        for _ in range(6):
            a = positive_update(a,paired_points(a,a.point)[0],0)
        q = terminal_clear_point(a,(0,0))
        self.assertIsNotNone(q)
        # Sector endpoints suffice for the extremal distance here.
        for delta in (-1.005,1.005):
            t = math.radians(delta)
            endpoint = (a.point[0]+a.bound*math.cos(t),a.point[1]+a.bound*math.sin(t))
            self.assertLessEqual(math.dist(q,endpoint),19.8)
        self.assertLessEqual(math.dist(q,a.point),19.8)
        self.assertEqual((len(search_points(3)),len(search_points(4))), (7,31))

    def test_wedge_unbounded_and_inconsistent(self):
        self.assertEqual(solve_wedges([dict(x=0,y=0,bearing_deg=0)])["state"],"UNBOUNDED")
        result = solve_wedges([dict(x=0,y=0,bearing_deg=0),dict(x=-1,y=0,bearing_deg=180)])
        self.assertEqual(result["state"],"EMPTY_OR_NUMERICALLY_UNRESOLVED")

    def test_triangle_diameter_circle(self):
        vertices = [(0,0),(1,0),(.5,math.sqrt(3)/2)]
        observations = []
        for i,p in enumerate(vertices):
            q = vertices[(i+1)%3]
            dx,dy = q[0]-p[0],q[1]-p[1]
            observations.append(dict(x=p[0]-100*dx,y=p[1]-100*dy,
                                     bearing_deg=math.degrees(math.atan2(dy,dx))+1))
        result = solve_wedges(observations,1)
        self.assertEqual(result["state"],"POLYGON")
        self.assertAlmostEqual(result["diameter"],1,places=8)
        self.assertFalse(result["diameter_circle_covers"])

    def test_clear_preserves_tuned_channel(self):
        io = Mock()
        io.call.return_value = dict(accepted=True,virtual_time_s=5,clear_result="success")
        solver = Solver(io,4)
        solver.channel = 2
        solver.action("/clear",(0,0),3)
        self.assertEqual(solver.channel,2)
        self.assertEqual(solver.switches,0)

    def test_rejection_preserves_state(self):
        io = Mock()
        io.call.side_effect = RejectedAction("accepted=false")
        solver = Solver(io,3)
        solver.virtual = 17
        with self.assertRaises(RejectedAction):
            solver.action("/measure",(100,0),2)
        self.assertEqual((solver.virtual,solver.position,solver.channel), (17,(0,0),1))

    def test_retry_identical_request_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            transport = HttpTransport("202612001024",Path(folder)/"actions.jsonl")
            response = Mock()
            response.status = 200
            response.read.return_value = json.dumps(dict(accepted=True,virtual_time_s=5,
                                                        measure_result="no_signal")).encode()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            transport.opener = Mock()
            transport.opener.open.side_effect = [URLError("fixed offline fixture"),response]
            try:
                with patch("protocol.time.sleep"):
                    transport.call("/measure",(0,0),1)
                requests = [c.args[0] for c in transport.opener.open.call_args_list]
                self.assertEqual(len(requests),2)
                self.assertEqual(requests[0].data,requests[1].data)
                self.assertEqual(requests[0].full_url,requests[1].full_url)
                self.assertIsNone(transport.pending)
            finally:
                transport.close()


if __name__ == "__main__":
    unittest.main()
