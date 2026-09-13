from near_optimal import suanfa as v8
from near_optimal.jiaozhun import replay
from fractions import Fraction as F
import math
import copy
import itertools
from pathlib import Path
import sys
import unittest
from near_optimal import geometry as g
from near_optimal.jiaozhun import build_graph, solve, calibrate
from protocol import RejectedAction, UncertainAction
from strategy import search_points


def negative():
    return dict(measure_result="no_signal")


class GeometryTests(unittest.TestCase):
    def test_rational_distance_rounding(self):
        p, q = (g.point((0, 0)), g.point((1, 1)))
        self.assertEqual(g.floor_distance(p, q), F("1.414"))
        self.assertEqual(g.ceil_distance(p, q), F("1.415"))
        self.assertLessEqual(g.floor_distance(p, q) ** 2, 2)
        self.assertGreaterEqual(g.ceil_distance(p, q) ** 2, 2)

    def test_trigonometric_enclosures_and_wrap(self):
        for b in (0, 1.005, 44.9, 45, 90, 179.99, 270, 359.99, -721.005):
            cl, ch, sl, sh = g.trig(F(b))
            c, s = (math.cos(math.radians(b)), math.sin(math.radians(b)))
            self.assertLessEqual(float(cl) - 1e-15, c)
            self.assertGreaterEqual(float(ch) + 1e-15, c)
            self.assertLessEqual(float(sl) - 1e-15, s)
            self.assertGreaterEqual(float(sh) + 1e-15, s)
        self.assertEqual(g.trig(F("1.005")), g.trig(F("361.005")))

    def test_full_grid_covers_all_directions(self):
        for p in (3, 4):
            self.assertTrue(g.coverage_certificate(tuple(g.search_grid()), (), p)[0])
        self.assertEqual(len(g.search_grid()), 49)

    def test_seven_omni_stops_do_not_certify_directional_absence(self):
        points = tuple((g.point(q) for q in search_points(3)))
        self.assertTrue(g.coverage_certificate(points, (), 3)[0])
        self.assertFalse(g.coverage_certificate(points, (), 4)[0])
        self.assertTrue(all((q[0] < 1800 for q in points)))

    def test_budget_exhaustion_is_unknown(self):
        self.assertFalse(g.coverage_certificate(tuple(g.search_grid()), (), 4, 1)[0])

    def test_full_directional_lattice_has_exact_certificate(self):
        points = tuple((g.point(q) for q in search_points(4)))
        self.assertTrue(g.coverage_certificate(points, (), 4, 4096)[0])

    def test_current_directional_design_has_continuous_certificate(self):
        points = tuple(sorted(g.point(q) for q in v8.search_points(4)))
        self.assertEqual(len(points), 21)
        self.assertTrue(g.coverage_certificate(points, (), 4, 20000, 14)[0])

    def test_round_domain_retains_boundary_and_removes_square_corner(self):
        domain = g.source_domain()
        for angle in range(0, 360, 5):
            r = 1800 - 1e-9
            p = g.point((r * math.cos(math.radians(angle)), r * math.sin(math.radians(angle))))
            self.assertTrue(g.contains(domain, p))
        old = v8.xin_yuan((1000, 1000), 45, geometry_version=1)
        current = v8.xin_yuan((1000, 1000), 45, geometry_version=2)
        self.assertTrue(g.contains(old["polygon"], g.point((1700, 1700))))
        self.assertFalse(g.contains(current["polygon"], g.point((1700, 1700))))
        self.assertTrue(g.contains(current["polygon"], g.point((1200, 1200))))
        self.assertTrue(
            any(g.contains(cell, g.point((1200, 1200))) for cell in current["cells"].values())
        )

    def test_unknown_geometry_version_is_rejected(self):
        with self.assertRaises(ValueError):
            v8.xin_jilu(3, geometry_version=99)

    def test_second_positive_uses_posterior_lower_range(self):
        yuan = v8.xin_yuan((0, 0), 0)
        v8.gengxin_yuan(yuan, (500, 150), "direction", 340, problem=3)
        origin = yuan["anchor_point"]
        u, _ = g.direction(F(yuan["anchor_bearing"]))
        projected = [g.dot(g.sub(q, origin), u) for q in yuan["polygon"]]
        self.assertGreater(min(projected), F(yuan["anchor_radius"]) / 2)
        for q in v8.pair_points(yuan, (0, 0)):
            distance = g.dot(g.sub(q, origin), u)
            self.assertGreater(distance, min(projected))
            self.assertLess(distance, max(projected))

    def test_initial_cells_retain_edge_bearings_and_ranges(self):
        for angle, r, error in ((0, 1500, 1), (359.99, 1499.99, -1), (90, 5.001, 1), (45, 1000, -1)):
            p = (r * math.cos(math.radians(angle)), r * math.sin(math.radians(angle)))
            bearing = round((angle + error) % 360, 2) % 360
            yuan = v8.xin_yuan((0, 0), bearing)
            self.assertTrue(g.contains(yuan["polygon"], g.point(p)))
            self.assertTrue(any((g.contains(cell, g.point(p)) for cell in yuan["cells"].values())))
            self.assertLessEqual(len(yuan["cells"]), 183)
            for i, cell in yuan["cells"].items():
                self.assertTrue(g.disk_contains(cell, yuan["points"][i], F(20)))

    def test_direction_interval_uses_whole_interval(self):
        q = g.point((0, 0))
        poly = g.rectangle(-1800, -1800, 1800, 1800)
        outer = g.apply_bearing(poly, q, F(30), hi=F(40))
        for angle in (29.01, 30, 35, 40, 40.99):
            p = g.point((1000 * math.cos(math.radians(angle)), 1000 * math.sin(math.radians(angle))))
            self.assertTrue(g.contains(outer, p))

    def test_negative_pair_requires_previous_positive(self):
        yuan = v8.xin_yuan((0, 0), 0)
        a, b = v8.pair_points(yuan, (0, 0))
        with self.assertRaises(RuntimeError):
            v8.shuang_yinxing(yuan, yuan["origin"], a, b)
        v8.gengxin_yuan(yuan, a, "no_signal", problem=4)
        v8.gengxin_yuan(yuan, b, "no_signal", problem=4)
        self.assertTrue(v8.shuang_yinxing(yuan, yuan["origin"], a, b))
        self.assertTrue(g.contains(yuan["polygon"], g.point((100, 0))))
        self.assertFalse(g.contains(yuan["polygon"], g.point((1200, 0))))

    def test_a_single_directional_negative_does_not_delete_truth(self):
        yuan = v8.xin_yuan((0, 0), 0)
        v8.gengxin_yuan(yuan, (150, 0), "no_signal", problem=4)
        self.assertTrue(g.contains(yuan["polygon"], g.point((100, 0))))

    def test_optical_failure_discharges_its_cell(self):
        yuan = v8.xin_yuan((0, 0), 0)
        i = min(yuan["cells"])
        q = yuan["points"][i]
        v8.gengxin_yuan(yuan, q, "no_target_in_range")
        self.assertNotIn(i, yuan["cells"])
        self.assertTrue(g.contains(yuan["polygon"], g.point((1499, 0))))

    def test_near_is_continuously_clearable(self):
        yuan = v8.xin_yuan((100, 100))
        q = v8.continuous_clear(yuan, (90, 90))
        self.assertIsNotNone(q)
        self.assertTrue(g.disk_contains(yuan["polygon"], q, F("19.8")))


class EvidenceTests(unittest.TestCase):
    def test_optional_omni_negative_is_useful_without_assuming_reception(self):
        class IO:
            pending = None

            def __init__(self):
                self.calls = []

            def call(self, path, q, c):
                self.calls.append((path, q, c))
                return dict(accepted=True, virtual_time_s=5.0, measure_result="no_signal")

            def record(self, event):
                pass

        io = IO()
        state = v8.xin_zhuangtai(io, 3)
        state["position"] = (750.0, 750.0)
        ledger = state["ledger"]
        v8.gengxin_jilu(ledger, "/measure", (0, 0), 1, dict(measure_result="direction", svd_deg=0))
        source = ledger["channels"][1]["source"]
        self.assertFalse(g.disk_contains(source["polygon"], g.point(state["position"]), F(999)))
        self.assertTrue(v8.shunlu_celiang(state))
        self.assertEqual(io.calls, [("/measure", (750.0, 750.0), 1)])
        self.assertEqual(state["travel"], 0)
        self.assertTrue(g.contains(source["polygon"], g.point((10, 0))))
        self.assertLess(max(float(q[0]) for q in source["polygon"]), 1000)
        self.assertEqual(ledger["channels"][1]["status"], "found")

    def test_shared_station_has_no_movement_and_keeps_directional_negative_feasible(self):
        class IO:
            pending = None

            def __init__(self):
                self.calls = []

            def call(self, path, q, c):
                self.calls.append((path, q, c))
                return dict(accepted=True, virtual_time_s=5.0, measure_result="no_signal")

            def record(self, event):
                pass

        io = IO()
        state = v8.xin_zhuangtai(io, 4)
        state["position"] = (750.0, 200.0)
        ledger = state["ledger"]
        v8.gengxin_jilu(ledger, "/measure", (0, 0), 1, dict(measure_result="direction", svd_deg=0))
        source = ledger["channels"][1]["source"]
        v8.xianding_fanwei(source, g.rectangle(700, -5, 800, 5))
        self.assertTrue(v8.shunlu_celiang(state))
        self.assertEqual(io.calls, [("/measure", (750.0, 200.0), 1)])
        self.assertEqual(state["travel"], 0.0)
        self.assertTrue(g.contains(source["polygon"], g.point((750, 0))))
        self.assertEqual(ledger["channels"][1]["status"], "found")
        self.assertTrue(v8.shunlu_celiang(state))
        self.assertEqual(len(io.calls), 1)

    def test_per_channel_histories_cannot_be_shared(self):
        jilu = v8.xin_jilu(3)
        for q in search_points(3):
            v8.gengxin_jilu(jilu, "/measure", q, 1, negative())
        self.assertEqual(jilu["channels"][1]["status"], "absent")
        self.assertEqual(jilu["channels"][2]["status"], "unknown")
        self.assertEqual(len(jilu["channels"][2]["pending"]), 49)

    def test_sixteen_discoveries_allow_count_stop_but_ten_do_not(self):
        for count in (10, 16):
            jilu = v8.xin_jilu(4)
            for c in range(1, count + 1):
                v8.gengxin_jilu(jilu, "/clear", (0, 0), c, dict(clear_result="success"))
            self.assertEqual(v8.quanbu_qingchu(jilu), count == 16)
            self.assertEqual(len(v8.pindao(jilu, ("unknown",))), 0 if count == 16 else 10)

    def test_unproductive_credits_never_reset(self):
        jilu = v8.xin_jilu(4, 2)
        for x in (1, 2):
            receipt = v8.gengxin_jilu(jilu, "/measure", (x, 1), 1, negative(), prove=False)
            self.assertLess(receipt["after"], receipt["before"])
        self.assertEqual(jilu["extra"], 0)
        q = g.search_grid()[0]
        v8.gengxin_jilu(jilu, "/measure", q, 1, negative(), prove=False)
        self.assertEqual(jilu["extra"], 0)

    def test_remaining_bound_includes_undiscovered_sources(self):
        jilu = v8.xin_jilu(4, 0)
        self.assertLess(v8.shengyu_shangjie(jilu, (0, 0)), 41640)
        self.assertGreater(v8.shengyu_shangjie(jilu, (0, 0)), 40000)

    def test_rejected_request_changes_neither_state_nor_evidence(self):

        class IO:
            pending = None

            def call(self, *args):
                return dict(accepted=False)

        zhuangtai = v8.xin_zhuangtai(IO(), 4)
        rank = v8.shengyu_renwu(zhuangtai["ledger"])
        with self.assertRaises(RejectedAction):
            v8.zhixing(zhuangtai, "/measure", (100, 200), 1)
        self.assertEqual(zhuangtai["position"], (0, 0))
        self.assertEqual(v8.shengyu_renwu(zhuangtai["ledger"]), rank)
        self.assertFalse(zhuangtai["ledger"]["receipts"])

    def test_unresolved_request_prevents_new_action(self):

        class IO:
            pending = {"request_id": "uncertain"}

            def call(self, *args):
                raise AssertionError("No call allowed")

        with self.assertRaises(UncertainAction):
            v8.zhixing(v8.xin_zhuangtai(IO(), 3), "/measure", (0, 0), 1)

    def test_bad_cost_cannot_produce_a_certificate(self):

        class IO:
            pending = None

            def call(self, *args):
                return dict(accepted=True, virtual_time_s=999, measure_result="near")

        zhuangtai = v8.xin_zhuangtai(IO(), 3)
        with self.assertRaises(RuntimeError):
            v8.zhixing(zhuangtai, "/measure", (10, 0), 1)
        self.assertEqual(zhuangtai["position"], (10, 0))
        self.assertFalse(v8.pindao(zhuangtai["ledger"], ("found", "cleared")))
        self.assertFalse(zhuangtai["certificate"])


class PlanningTests(unittest.TestCase):
    def test_directional_visibility_conditions_on_actual_negative_history(self):
        poly = g.rectangle(-1, -1, 1, 1)
        record = dict(
            source=dict(cells={0: poly}),
            records=[
                dict(path="/measure", point=(-100, 0), kind="direction"),
                dict(path="/measure", point=(100, 0), kind="no_signal"),
            ],
        )
        before = copy.deepcopy(record)
        model = v8.radio_model(record)
        self.assertAlmostEqual(v8.radio_probability(model, (-200, 0)), 1)
        self.assertAlmostEqual(v8.radio_probability(model, (0, 0)), 1)
        self.assertAlmostEqual(v8.radio_probability(model, (200, 0)), 0)
        self.assertAlmostEqual(v8.radio_probability(model, (-1600, 0)), 0)
        self.assertEqual(record, before)

    def test_optical_chain_covers_complete_region_not_only_sample_points(self):
        source = v8.xin_yuan((0, 0), 0)
        v8.xianding_fanwei(source, g.rectangle(500, -8, 600, 8))
        options = v8.optical_offers(source, (0, 0))
        self.assertTrue(options)
        for _, order, _, upper in options:
            self.assertLessEqual(len(order), 8)
            self.assertGreaterEqual(upper, v8.chain_bound(order, (0, 0)))
            for q in order:
                cell = source["polygon"]
                for other in order:
                    if q != other:
                        cell = g.clip(cell, g.sub(other, q), (g.dot(other, other) - g.dot(q, q)) / 2)
                self.assertTrue(not cell or g.disk_contains(cell, q, F("19.8")))

    def test_optical_chain_is_rejected_before_action_when_credit_is_insufficient(self):
        state = v8.xin_zhuangtai(None, 4, extra_actions=1)
        event = dict(kind="optical_chain", channel=1, points=(g.point((10, 0)), g.point((20, 0))))
        before = v8.shengyu_renwu(state["ledger"])
        self.assertFalse(v8.zhixing_yici(state, event))
        self.assertEqual(v8.shengyu_renwu(state["ledger"]), before)
        self.assertEqual(state["position"], (0, 0))

    def test_negative_pair_without_contraction_is_not_measured_again(self):
        state = v8.xin_zhuangtai(None, 4, planning_seconds=0)
        source = v8.xin_yuan((0, 0), 0)
        source["positives"].append(g.point((-50, 20)))
        v8.xianding_fanwei(source, g.rectangle(500, -8, 600, 8))
        pair = v8.pair_points(source, (0, 0))
        for q in pair:
            v8.gengxin_yuan(source, q, "no_signal", problem=4)
        self.assertFalse(v8.shuang_yinxing(source, source["anchor_point"], *pair))
        before = copy.deepcopy(source)
        event = v8.yuan_dongzuo(state["planner"], source, 1, g.floating(pair[-1]), 1, 640)
        self.assertIn(event["kind"], ("clear", "optical_chain"))
        self.assertEqual(source, before)
        self.assertEqual(state["planner"]["statistics"]["repeated_negative_pairs_skipped"], 1)

    def test_small_service_plan_matches_exhaustive_orders_and_modes(self):
        jobs = {}
        for channel, points in enumerate(
            (((9, 0), (0, 8)), ((20, 3), (2, 13)), ((-4, 18), (18, 17))), 1
        ):
            job = ("source", channel)
            jobs[job] = [
                dict(
                    job=job, entry=p, exit=(p[0] + 2 * channel, p[1] - channel), service=3 + channel + i
                )
                for i, p in enumerate(points)
            ]
        position = (1, -2)
        exact = math.inf
        for order in itertools.permutations(jobs):
            for modes in itertools.product(*(jobs[job] for job in order)):
                cost = math.dist(position, modes[0]["entry"]) / 5 + modes[0]["service"]
                cost += sum(
                    math.dist(a["exit"], b["entry"]) / 5 + b["service"] for a, b in zip(modes, modes[1:])
                )
                exact = min(exact, cost)
        plan = v8.anpai_renwu(jobs, position, (("source", 99), ("source", 2)))
        self.assertAlmostEqual(plan["estimate"], exact)
        self.assertCountEqual(plan["order"], jobs)
        self.assertEqual([mode["job"] for mode in plan["modes"]], plan["order"])


class CalibrationTests(unittest.TestCase):
    def test_exact_value_and_rollout_gap(self):
        result = calibrate([(0,), (60,), (120,)], (0, 60, 120))
        self.assertEqual(result["exact_fraction"], "34")
        self.assertEqual(result["rollout"][0]["upper_s"], 35)
        self.assertEqual(result["rollout"][2]["gap_s"], 0)

    def test_bellman_solution_and_nonanticipative_actions(self):
        root, graph, terminal = build_graph([(0, 120), (120, 0)], (0, 60, 120))
        values, policy, _ = solve(graph, terminal)
        for s, actions in graph.items():
            if s in terminal:
                self.assertEqual(values[s], 0)
                continue
            expected = min(
                (max((cost + values[t] for _, cost, t in edges)) for edges in actions.values())
            )
            self.assertEqual(values[s], expected)
            for _, cost, t in actions[policy[s]]:
                self.assertGreater(cost, 0)
                self.assertLess(values[t], values[s])
        self.assertTrue(math.isfinite(values[root]))

    def test_variable_count_is_rejected(self):
        with self.assertRaises(ValueError):
            build_graph([(0,), (0, 60)], (0, 60))

    def test_information_lower_bound(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "experiments/optimality-bounds"))
        from information import per_channel, absence_lower

        self.assertEqual((per_channel(3), per_channel(4)), (30, 35))
        self.assertEqual(absence_lower(4, 10), 350)
        self.assertEqual(absence_lower(4, 16), 0)


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(root / "experiments/near-optimal"))
        from benchmark import run_case
        from b_simulation import Source as TruthSource

        cls.results = []
        for problem, n, fallback in ((3, 10, False), (4, 16, True)):
            case = dict(
                name="unit-completion",
                problem=problem,
                seed=17,
                extreme=True,
                sources=[
                    TruthSource(c, (0.0, 0.0), 1000.0, 0.0 if problem == 4 else None)
                    for c in range(1, n + 1)
                ],
            )
            result, events = run_case(
                case, planning_seconds=0, extra_actions=0 if fallback else 640, fallback_only=fallback
            )
            cls.results.append((result, events))

    def test_actual_completion_and_truth_free_replay(self):
        for result, events in self.results:
            self.assertIsNone(result["error"], result.get("traceback"))
            self.assertEqual(result["source_count"], result["cleared_count"])
            self.assertTrue(replay(events)["verified"])

    def test_zero_credit_fallback_with_failed_optical_attempts(self):
        result, events = self.results[1]
        self.assertTrue(result["summary"]["fallback_used"])
        self.assertEqual(result["summary"]["extra_actions_remaining"], 0)
        self.assertGreater(result["counts"]["clear"], result["source_count"])
        self.assertLess(result["virtual_time_s"], result["summary"]["initial_fallback_upper_s"])
        self.assertLessEqual(result["counts"]["measure"] + result["counts"]["clear"], 3908)

    def test_tampered_response_is_rejected_by_replay(self):
        events = copy.deepcopy(self.results[0][1])
        item = next((e for e in events if e.get("event") == "evidence_observation"))
        item["reply"]["virtual_time_s"] += 1
        with self.assertRaises(RuntimeError):
            replay(events)

    def test_missing_receipt_is_rejected_by_replay(self):
        events = list(self.results[0][1])
        i = next((i for i, e in enumerate(events) if e.get("event") == "rank_receipt"))
        del events[i]
        with self.assertRaises(RuntimeError):
            replay(events)

    def test_prospective_search_proofs_do_not_erase_unknowns(self):
        jilu = v8.xin_jilu(3)
        plan = v8.xin_luxian(search_points(3), seconds=1)
        v8.gengxin_luxian(plan, jilu, (0, 0))
        self.assertEqual(v8.pindao(jilu, ("unknown",)), set(range(1, 21)))
        self.assertEqual(v8.shengyu_renwu(jilu), 980 + 16 * 183 + 640)
        self.assertFalse(jilu["certificates"])


if __name__ == "__main__":
    unittest.main()
