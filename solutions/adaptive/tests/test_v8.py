"""Adversarial geometry, independent evidence and finite-policy calibration."""
from fractions import Fraction as F
import math
import copy
from pathlib import Path
import sys
import unittest

from near_optimal import geometry as g
from near_optimal.state import Ledger, Source, EvidenceError
from near_optimal.planner import pair_points, continuous_clear, radio_rollout
from near_optimal.solver import SolverV8
from near_optimal.finite_policy import build_graph, solve, calibrate
from near_optimal.replay import replay
from near_optimal.search_plan import SearchPlan
from protocol import RejectedAction, UncertainAction
from strategy import search_points


def negative():
    return dict(measure_result='no_signal')


class GeometryTests(unittest.TestCase):
    def test_rational_distance_rounding(self):
        p,q = g.point((0,0)),g.point((1,1))
        self.assertEqual(g.floor_distance(p,q),F('1.414'))
        self.assertEqual(g.ceil_distance(p,q),F('1.415'))
        self.assertLessEqual(g.floor_distance(p,q)**2,2)
        self.assertGreaterEqual(g.ceil_distance(p,q)**2,2)

    def test_trigonometric_enclosures_and_wrap(self):
        for b in (0,1.005,44.9,45,90,179.99,270,359.99,-721.005):
            cl,ch,sl,sh = g.trig(F(b))
            c,s = math.cos(math.radians(b)),math.sin(math.radians(b))
            self.assertLessEqual(float(cl)-1e-15,c)
            self.assertGreaterEqual(float(ch)+1e-15,c)
            self.assertLessEqual(float(sl)-1e-15,s)
            self.assertGreaterEqual(float(sh)+1e-15,s)
        self.assertEqual(g.trig(F('1.005')),g.trig(F('361.005')))

    def test_full_grid_covers_all_directions(self):
        for p in (3,4):
            self.assertTrue(g.coverage_certificate(tuple(g.search_grid()),(),p)[0])
        self.assertEqual(len(g.search_grid()),49)

    def test_seven_omni_stops_do_not_certify_directional_absence(self):
        points = tuple(g.point(q) for q in search_points(3))
        self.assertTrue(g.coverage_certificate(points,(),3)[0])
        self.assertFalse(g.coverage_certificate(points,(),4)[0])
        # Boundary source (1800,0), outward orientation: all stops behind it.
        self.assertTrue(all(q[0]<1800 for q in points))

    def test_budget_exhaustion_is_unknown(self):
        self.assertFalse(g.coverage_certificate(tuple(g.search_grid()),(),4,1)[0])

    def test_full_directional_lattice_has_exact_certificate(self):
        points = tuple(g.point(q) for q in search_points(4))
        self.assertTrue(g.coverage_certificate(points,(),4,4096)[0])

    def test_initial_cells_retain_edge_bearings_and_ranges(self):
        for angle,r,error in ((0,1500,1),(359.99,1499.99,-1),(90,5.001,1),(45,1000,-1)):
            p = (r*math.cos(math.radians(angle)),r*math.sin(math.radians(angle)))
            bearing = round((angle+error)%360,2)%360
            source = Source.found((0,0),bearing)
            self.assertTrue(g.contains(source.polygon,g.point(p)))
            self.assertTrue(any(g.contains(cell,g.point(p)) for cell in source.cells.values()))
            self.assertLessEqual(len(source.cells),183)
            for i,cell in source.cells.items():
                self.assertTrue(g.disk_contains(cell,source.points[i],F(20)))

    def test_direction_interval_uses_whole_interval(self):
        q = g.point((0,0));poly = g.rectangle(-1800,-1800,1800,1800)
        outer = g.apply_bearing(poly,q,F(30),hi=F(40))
        for angle in (29.01,30,35,40,40.99):
            p = g.point((1000*math.cos(math.radians(angle)),1000*math.sin(math.radians(angle))))
            self.assertTrue(g.contains(outer,p))

    def test_negative_pair_requires_previous_positive(self):
        source = Source.found((0,0),0)
        a,b = pair_points(source,(0,0))
        with self.assertRaises(EvidenceError):
            source.negative_pair(source.origin,a,b)
        source.negative(a,4);source.negative(b,4)
        self.assertTrue(source.negative_pair(source.origin,a,b))
        self.assertTrue(g.contains(source.polygon,g.point((100,0))))
        self.assertFalse(g.contains(source.polygon,g.point((1200,0))))

    def test_a_single_directional_negative_does_not_delete_truth(self):
        source = Source.found((0,0),0)
        source.negative((150,0),4)
        self.assertTrue(g.contains(source.polygon,g.point((100,0))))

    def test_optical_failure_discharges_its_cell(self):
        source = Source.found((0,0),0)
        i = min(source.cells);q = source.points[i]
        source.optical_failure(q)
        self.assertNotIn(i,source.cells)
        self.assertTrue(g.contains(source.polygon,g.point((1499,0))))

    def test_near_is_continuously_clearable(self):
        source = Source.found((100,100))
        q = continuous_clear(source,(90,90))
        self.assertIsNotNone(q)
        self.assertTrue(g.disk_contains(source.polygon,q,F('19.8')))


class EvidenceTests(unittest.TestCase):
    def test_per_channel_histories_cannot_be_shared(self):
        ledger = Ledger(3)
        for q in search_points(3):
            ledger.observe('/measure',q,1,negative())
        self.assertEqual(ledger.channels[1].status,'absent')
        self.assertEqual(ledger.channels[2].status,'unknown')
        self.assertEqual(len(ledger.channels[2].pending),49)

    def test_sixteen_discoveries_allow_count_stop_but_ten_do_not(self):
        for count in (10,16):
            ledger = Ledger(4)
            for c in range(1,count+1):
                ledger.observe('/clear',(0,0),c,dict(clear_result='success'))
            self.assertEqual(ledger.complete(),count==16)
            self.assertEqual(len(ledger.unknown),0 if count==16 else 10)

    def test_unproductive_credits_never_reset(self):
        ledger = Ledger(4,2)
        for x in (1,2):
            receipt = ledger.observe('/measure',(x,1),1,negative(),prove=False)
            self.assertLess(receipt['after'],receipt['before'])
        self.assertEqual(ledger.extra,0)
        q = g.search_grid()[0]
        ledger.observe('/measure',q,1,negative(),prove=False)
        self.assertEqual(ledger.extra,0)

    def test_remaining_bound_includes_undiscovered_sources(self):
        ledger = Ledger(4,0)
        self.assertLess(ledger.remaining_upper((0,0)),41640)
        self.assertGreater(ledger.remaining_upper((0,0)),40000)

    def test_rejected_request_changes_neither_state_nor_evidence(self):
        class IO:
            pending = None
            def call(self,*args): return dict(accepted=False)
        solver = SolverV8(IO(),4)
        rank = solver.ledger.potential()
        with self.assertRaises(RejectedAction):
            solver.action('/measure',(100,200),1)
        self.assertEqual(solver.position,(0,0))
        self.assertEqual(solver.ledger.potential(),rank)
        self.assertFalse(solver.ledger.receipts)

    def test_unresolved_request_prevents_new_action(self):
        class IO:
            pending = {'request_id':'uncertain'}
            def call(self,*args): raise AssertionError('No call allowed')
        with self.assertRaises(UncertainAction):
            SolverV8(IO(),3).action('/measure',(0,0),1)

    def test_bad_cost_cannot_produce_a_certificate(self):
        class IO:
            pending = None
            def call(self,*args):
                return dict(accepted=True,virtual_time_s=999,measure_result='near')
        solver = SolverV8(IO(),3)
        with self.assertRaises(EvidenceError):
            solver.action('/measure',(10,0),1)
        self.assertEqual(solver.position,(10,0))  # Accepted physical movement.
        self.assertFalse(solver.ledger.discovered)
        self.assertFalse(solver.certificate)


class CalibrationTests(unittest.TestCase):
    def test_exact_value_and_rollout_gap(self):
        result = calibrate([(0,),(60,),(120,)],(0,60,120))
        # Measure at 60: move12+measure5; adverse endpoint move12+clear5.
        self.assertEqual(result['exact_fraction'],'34')
        self.assertEqual(result['rollout'][0]['upper_s'],35)
        self.assertEqual(result['rollout'][2]['gap_s'],0)

    def test_bellman_solution_and_nonanticipative_actions(self):
        root,graph,terminal = build_graph([(0,120),(120,0)],(0,60,120))
        values,policy,_ = solve(graph,terminal)
        for s,actions in graph.items():
            if s in terminal:
                self.assertEqual(values[s],0);continue
            expected = min(max(cost+values[t] for _,cost,t in edges) for edges in actions.values())
            self.assertEqual(values[s],expected)
            for _,cost,t in actions[policy[s]]:
                self.assertGreater(cost,0)
                self.assertLess(values[t],values[s])
        self.assertTrue(math.isfinite(values[root]))

    def test_variable_count_is_rejected(self):
        with self.assertRaises(ValueError):
            build_graph([(0,),(0,60)],(0,60))

    def test_information_lower_bound(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'experiments/optimality-bounds'))
        from information import per_channel,absence_lower
        self.assertEqual((per_channel(3),per_channel(4)),(30,35))
        self.assertEqual(absence_lower(4,10),350)
        self.assertEqual(absence_lower(4,16),0)


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[3]
        sys.path.insert(0,str(root/'experiments/near-optimal'))
        from benchmark import run_case
        from b_simulation import Source as TruthSource
        cls.results = []
        for problem,n,fallback in ((3,10,False),(4,16,True)):
            case = dict(name='unit-completion',problem=problem,seed=17,extreme=True,
                        sources=[TruthSource(c,(0.,0.),1000.,0. if problem==4 else None) for c in range(1,n+1)])
            result,events = run_case(case,planning_seconds=0,extra_actions=0 if fallback else 640,
                                    fallback_only=fallback)
            cls.results.append((result,events))

    def test_actual_completion_and_truth_free_replay(self):
        for result,events in self.results:
            self.assertIsNone(result['error'],result.get('traceback'))
            self.assertEqual(result['source_count'],result['cleared_count'])
            self.assertTrue(replay(events)['verified'])

    def test_zero_credit_fallback_with_failed_optical_attempts(self):
        result,events = self.results[1]
        self.assertTrue(result['summary']['fallback_used'])
        self.assertEqual(result['summary']['extra_actions_remaining'],0)
        self.assertGreater(result['counts']['clear'],result['source_count'])
        self.assertLess(result['virtual_time_s'],result['summary']['initial_fallback_upper_s'])
        self.assertLessEqual(result['counts']['measure']+result['counts']['clear'],3908)

    def test_tampered_response_is_rejected_by_replay(self):
        events = copy.deepcopy(self.results[0][1])
        item = next(e for e in events if e.get('event')=='evidence_observation')
        item['reply']['virtual_time_s'] += 1
        with self.assertRaises(EvidenceError): replay(events)

    def test_missing_receipt_is_rejected_by_replay(self):
        events = list(self.results[0][1])
        i = next(i for i,e in enumerate(events) if e.get('event')=='rank_receipt')
        del events[i]
        with self.assertRaises(EvidenceError): replay(events)

    def test_prospective_search_proofs_do_not_erase_unknowns(self):
        ledger = Ledger(3)
        plan = SearchPlan(search_points(3),seconds=1)
        plan.update(ledger,(0,0))
        self.assertEqual(ledger.unknown,set(range(1,21)))
        self.assertEqual(ledger.potential(),980+16*183+640)
        self.assertFalse(ledger.certificates)


if __name__=='__main__':
    unittest.main()
