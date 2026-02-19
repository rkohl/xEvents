import unittest
from xevents import xEvents


class TestWildcard(unittest.TestCase):
    def setUp(self):
        self.bus = xEvents()
        self.received = []

    def test_wildcard_star(self):
        self.bus.on_any("orders:*", lambda ev, d: self.received.append((ev, d)))
        self.bus.post("orders:created", {"id": 1})
        self.bus.post("orders:deleted", {"id": 2})
        self.bus.post("users:created", {"id": 3})
        self.assertEqual(len(self.received), 2)
        self.assertEqual(self.received[0][0], "orders:created")
        self.assertEqual(self.received[1][0], "orders:deleted")

    def test_wildcard_all(self):
        self.bus.on_any("*", lambda ev, d: self.received.append(ev))
        self.bus.post("a", {})
        self.bus.post("b", {})
        self.assertEqual(len(self.received), 2)

    def test_off_any(self):
        listener = lambda ev, d: self.received.append(ev)
        self.bus.on_any("*", listener)
        self.bus.post("a", {})
        self.bus.off_any("*", listener)
        self.bus.post("b", {})
        self.assertEqual(len(self.received), 1)


if __name__ == "__main__":
    unittest.main()
