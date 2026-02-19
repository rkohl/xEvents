import unittest
from xevents import xEvents


class TestReplay(unittest.TestCase):
    def setUp(self):
        self.bus = xEvents()
        self.received = []

    def test_replay_delivers_past_events(self):
        self.bus.post("update", {"v": 1})
        self.bus.post("update", {"v": 2})
        self.bus.post("other", {"v": 3})
        count = self.bus.replay("update", lambda d: self.received.append(d))
        self.assertEqual(count, 2)
        self.assertEqual(len(self.received), 2)

    def test_replay_with_limit(self):
        for i in range(5):
            self.bus.post("x", {"i": i})
        count = self.bus.replay("x", lambda d: self.received.append(d), limit=2)
        self.assertEqual(count, 2)
        self.assertEqual(self.received[0]["i"], 3)

    def test_replay_channel(self):
        self.bus.post("orders:created", {"id": 1})
        self.bus.post("orders:updated", {"id": 2})
        self.bus.post("users:created", {"id": 3})
        count = self.bus.replay_channel("orders", lambda d: self.received.append(d))
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
