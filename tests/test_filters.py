import unittest
from xevents import xEvents


class TestFilter(unittest.TestCase):
    def setUp(self):
        self.bus = xEvents()
        self.received = []

    def test_filter_skips_non_matching(self):
        self.bus.subscribe(
            "order",
            lambda d: self.received.append(d),
            filter_fn=lambda d: d.get("status") == "paid",
        )
        self.bus.post("order", {"status": "pending", "id": 1})
        self.bus.post("order", {"status": "paid", "id": 2})
        self.bus.post("order", {"status": "refunded", "id": 3})
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0]["id"], 2)


if __name__ == "__main__":
    unittest.main()
