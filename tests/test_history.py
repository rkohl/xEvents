import unittest
from xevents import xEvents, EventRecord


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.bus = xEvents(history_limit=50)

    def test_history_records(self):
        self.bus.post("a", {"v": 1})
        self.bus.post("b", {"v": 2})
        h = self.bus.history()
        self.assertEqual(len(h), 2)
        self.assertIsInstance(h[0], EventRecord)

    def test_history_filter_by_event(self):
        self.bus.post("a", {"v": 1})
        self.bus.post("b", {"v": 2})
        self.bus.post("a", {"v": 3})
        h = self.bus.history(event="a")
        self.assertEqual(len(h), 2)

    def test_history_filter_by_channel(self):
        self.bus.post("orders:created", {"id": 1})
        self.bus.post("users:created", {"id": 2})
        h = self.bus.history(channel="orders")
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0].data["id"], 1)

    def test_history_limit(self):
        self.bus.post("a", {"v": 1})
        self.bus.post("a", {"v": 2})
        self.bus.post("a", {"v": 3})
        h = self.bus.history(event="a", limit=2)
        self.assertEqual(len(h), 2)
        self.assertEqual(h[0].data["v"], 2)

    def test_history_cap(self):
        bus = xEvents(history_limit=5)
        for i in range(10):
            bus.post("x", {"i": i})
        h = bus.history()
        self.assertEqual(len(h), 5)
        self.assertEqual(h[0].data["i"], 5)

    def test_clear_history(self):
        self.bus.post("a", {})
        self.bus.clear_history()
        self.assertEqual(len(self.bus.history()), 0)


if __name__ == "__main__":
    unittest.main()
