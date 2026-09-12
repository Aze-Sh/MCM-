import time
import unittest
from benchmark import OfflineIO


class OfflineTimeoutTests(unittest.TestCase):
    def test_expired_call_does_not_send(self):
        sent = []
        io = OfflineIO(lambda *args: sent.append(args))
        io.wall_deadline = time.monotonic() - 1
        with self.assertRaises(TimeoutError):
            io.call('/enter')
        self.assertEqual(sent, [])

    def test_expired_record_stops_planning(self):
        io = OfflineIO(None)
        io.wall_deadline = time.monotonic() - 1
        with self.assertRaises(TimeoutError):
            io.record({'event': 'planning'})


if __name__ == '__main__':
    unittest.main()
