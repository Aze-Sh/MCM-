import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError
from jammer_solver.questions import jhqy
from jammer_solver.protocol import xjjk
from jammer_solver.questions import ecdqy
from jammer_solver.solver import zjqcd
from jammer_solver.solver import qclxyh


class HelperTests(unittest.TestCase):
    def test_second_region_strict_expansion(self):
        result = ecdqy((0, 0), 0, (500, 840))
        self.assertTrue(result["query_in_region"])
        e = math.radians(1.005)
        self.assertGreater(
            math.dist((500, 840), (1500 * math.cos(e), -1500 * math.sin(e))), 1000
        )

    def test_route_feasible_and_nonincreasing(self):
        p, t, start = (0, 3), (3, 0), (0, 1)
        point, diag = qclxyh([(0, 0)], 1, start, p, t)
        self.assertLessEqual(math.hypot(*point), 1 + 1e-10)
        self.assertLess(
            (
                math.hypot(p[0] - point[0], p[1] - point[1])
                + math.hypot(point[0] - t[0], point[1] - t[1])
            ),
            (
                math.hypot(p[0] - start[0], p[1] - start[1])
                + math.hypot(start[0] - t[0], start[1] - t[1])
            )
            - 0.1,
        )
        self.assertLessEqual(diag["iterations"], 24)

    def test_clear_projection_two_active_circles(self):
        polygon = [(-10, 0), (10, 0)]
        radius = 19.8 - 1e-6
        point = zjqcd(polygon, (0, 50))
        self.assertAlmostEqual(point[0], 0, places=9)
        self.assertAlmostEqual(point[1], math.sqrt(radius * radius - 100), places=8)
        self.assertIsNone(zjqcd([(-21, 0), (21, 0)], (0, 50)))
        self.assertEqual(zjqcd(polygon, (0, 0)), (0, 0))

    def test_wedge_unbounded_and_inconsistent(self):
        self.assertEqual(jhqy([dict(x=0, y=0, bearing_deg=0)])["state"], "UNBOUNDED")
        result = jhqy([dict(x=0, y=0, bearing_deg=0), dict(x=-1, y=0, bearing_deg=180)])
        self.assertEqual(result["state"], "EMPTY_OR_NUMERICALLY_UNRESOLVED")

    def test_triangle_diameter_circle(self):
        vertices = [(0, 0), (1, 0), (0.5, math.sqrt(3) / 2)]
        observations = []
        for i, p in enumerate(vertices):
            q = vertices[(i + 1) % 3]
            dx, dy = q[0] - p[0], q[1] - p[1]
            observations.append(
                dict(
                    x=p[0] - 100 * dx,
                    y=p[1] - 100 * dy,
                    bearing_deg=math.degrees(math.atan2(dy, dx)) + 1,
                )
            )
        result = jhqy(observations, 1)
        self.assertEqual(result["state"], "POLYGON")
        self.assertAlmostEqual(result["diameter"], 1, places=8)
        self.assertFalse(result["diameter_circle_covers"])

    def test_http_requests_and_evidence_log_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "actions.jsonl"
            response = Mock()
            response.status = 200
            response.read.return_value = json.dumps(
                dict(accepted=True, virtual_time_s=5, measure_result="no_signal")
            ).encode()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            opener = Mock()
            opener.open.return_value = response
            with path.open("x", encoding="utf-8") as log:
                with patch("jammer_solver.protocol.ljq", return_value=opener):
                    transport = xjjk("test-robot", log)
                reply = transport["call"]("/measure", (12.5, -4), 7)
                self.assertEqual(reply["measure_result"], "no_signal")
                self.assertIsNone(transport["pending"])
            request = opener.open.call_args.args[0]
            self.assertEqual(request.full_url, "http://127.0.0.1:2026/measure")
            payload = json.loads(request.data)
            self.assertEqual(payload["position"], {"x": 12.5, "y": -4})
            self.assertEqual(payload["channel"], 7)
            events = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([e["event"] for e in events], ["intent", "response"])
            self.assertEqual(events[0]["payload"], payload)
            self.assertEqual(events[1]["request_id"], payload["request_id"])

    def test_network_failure_propagates_and_leaves_request_unconfirmed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "actions.jsonl"
            opener = Mock()
            opener.open.side_effect = URLError("fixed offline fixture")
            with path.open("x", encoding="utf-8") as log:
                with patch("jammer_solver.protocol.ljq", return_value=opener):
                    transport = xjjk("test-robot", log)
                with self.assertRaises(URLError):
                    transport["call"]("/measure", (0, 0), 1)
                self.assertIsNotNone(transport["pending"])
                with self.assertRaises(RuntimeError):
                    transport["call"]("/exit")
            opener.open.assert_called_once()
            self.assertEqual(len(path.read_text().splitlines()), 1)
