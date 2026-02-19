import unittest
from xevents import xEvents


class TestSubscribeAndPost(unittest.TestCase):
    def setUp(self):
        self.bus = xEvents()
        self.received = []

    def test_subscribe_and_post(self):
        self.bus.subscribe("test", lambda d: self.received.append(d))
        self.bus.post("test", {"msg": "hello"})
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0]["msg"], "hello")

    def test_on_alias(self):
        self.bus.on("test", lambda d: self.received.append(d))
        self.bus.post("test", {"val": 1})
        self.assertEqual(len(self.received), 1)

    def test_unsubscribe(self):
        listener = lambda d: self.received.append(d)
        self.bus.subscribe("test", listener)
        self.bus.post("test", {"a": 1})
        self.bus.unsubscribe("test", listener)
        self.bus.post("test", {"a": 2})
        self.assertEqual(len(self.received), 1)

    def test_multiple_listeners(self):
        results_a = []
        results_b = []
        self.bus.subscribe("test", lambda d: results_a.append(d))
        self.bus.subscribe("test", lambda d: results_b.append(d))
        self.bus.post("test", {"x": 1})
        self.assertEqual(len(results_a), 1)
        self.assertEqual(len(results_b), 1)

    def test_disabled_events(self):
        self.bus.subscribe("test", lambda d: self.received.append(d))
        self.bus.enabled = False
        self.bus.post("test", {"a": 1})
        self.assertEqual(len(self.received), 0)

    def test_no_duplicate_subscribe(self):
        listener = lambda d: self.received.append(d)
        self.bus.subscribe("test", listener)
        self.bus.subscribe("test", listener)
        self.bus.post("test", {"a": 1})
        self.assertEqual(len(self.received), 1)

    def test_pre_registered_events(self):
        bus = xEvents(events=["start", "stop"])
        evts = bus.events()
        self.assertIn("start", evts)
        self.assertIn("stop", evts)


class TestOnceListener(unittest.TestCase):
    def setUp(self):
        self.bus = xEvents()
        self.received = []

    def test_once_fires_once(self):
        self.bus.once("test", lambda d: self.received.append(d))
        self.bus.post("test", {"a": 1})
        self.bus.post("test", {"a": 2})
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0]["a"], 1)

    def test_once_alias(self):
        self.bus.once("test", lambda d: self.received.append(d))
        self.bus.post("test", {"v": 10})
        self.bus.post("test", {"v": 20})
        self.assertEqual(len(self.received), 1)


if __name__ == "__main__":
    unittest.main()
