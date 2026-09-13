import time
import unittest
from benchmark import offline_io


class OfflineTimeoutTests(unittest.TestCase):
    def test_expired_call_does_not_send(self):
        sent = []
        io = offline_io(lambda *args: sent.append(args))
        io["wall_deadline"] = time.monotonic() - 1
        with self.assertRaises(TimeoutError):
            io["call"]("/enter")
        self.assertEqual(sent, [])

    def test_expired_record_stops_planning(self):
        io = offline_io(None)
        io["wall_deadline"] = time.monotonic() - 1
        with self.assertRaises(TimeoutError):
            io["record"]({"event": "planning"})


if __name__ == "__main__":
    unittest.main()
